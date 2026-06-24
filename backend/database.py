import os
import csv
import sqlite3
import logging

logger = logging.getLogger(__name__)

class Database:
    """
    Manages MySQL database connection with SQLite fallback.
    Automatically seeds tables from local CSV files in data/ if empty.
    """
    def __init__(self):
        self.db_type = os.environ.get("DB_TYPE", "sqlite")
        self.sqlite_path = os.environ.get("SQLITE_DB_PATH", os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "hackathon.db"
        ))
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
        
        self.mysql_config = {
            "host": os.environ.get("MYSQL_HOST", "localhost"),
            "user": os.environ.get("MYSQL_USER", "root"),
            "password": os.environ.get("MYSQL_PASSWORD", ""),
            "database": os.environ.get("MYSQL_DATABASE", "cargo_fraud_db"),
            "port": int(os.environ.get("MYSQL_PORT", 3306))
        }

    def get_connection(self):
        if self.db_type == "mysql":
            try:
                import pymysql
                conn = pymysql.connect(
                    host=self.mysql_config["host"],
                    user=self.mysql_config["user"],
                    password=self.mysql_config["password"],
                    database=self.mysql_config["database"],
                    port=self.mysql_config["port"],
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True
                )
                return conn
            except Exception as e:
                logger.warning(f"MySQL connection failed: {e}. Falling back to SQLite...")
                self.db_type = "sqlite"

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def execute(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if self.db_type == "sqlite":
                query = query.replace("%s", "?")
            else:
                query = query.replace("?", "%s")
                
            cursor.execute(query, params or ())
            
            if self.db_type == "sqlite":
                conn.commit()
                last_id = cursor.lastrowid
            else:
                last_id = cursor.lastrowid
                
            return last_id
        except Exception as e:
            logger.error(f"DB Execute Error: {e} | Query: {query}")
            if self.db_type == "sqlite":
                conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def fetch_all(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if self.db_type == "sqlite":
                query = query.replace("%s", "?")
            else:
                query = query.replace("?", "%s")
                
            cursor.execute(query, params or ())
            rows = cursor.fetchall()
            if self.db_type == "sqlite":
                return [dict(row) for row in rows]
            return rows
        except Exception as e:
            logger.error(f"DB Fetch All Error: {e} | Query: {query}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def init_db(self):
        """Initializes tables using schema.sql and seeds tables if empty."""
        schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql", "schema.sql")
        if not os.path.exists(schema_path):
            logger.error(f"Schema file not found at {schema_path}")
            return
            
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        conn = self.get_connection()
        if self.db_type == "sqlite":
            try:
                conn.executescript(sql_script)
                conn.commit()
            except Exception as e:
                logger.error(f"SQLite init failed: {e}")
        else:
            try:
                cursor = conn.cursor()
                mysql_script = sql_script.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "INT PRIMARY KEY AUTO_INCREMENT")
                for stmt in mysql_script.split(";"):
                    s = stmt.strip()
                    if s:
                        cursor.execute(s)
                conn.commit()
            except Exception as e:
                logger.error(f"MySQL init failed: {e}")
        conn.close()

        # Seed data tables if they are empty
        self._seed_tables()

    def _seed_tables(self):
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        
        # 1. Seed trusted_domains
        try:
            rows = self.fetch_all("SELECT COUNT(*) as cnt FROM trusted_domains")
            if rows[0]["cnt"] == 0:
                csv_path = os.path.join(data_dir, "trusted_domains.csv")
                if os.path.exists(csv_path):
                    print("Seeding trusted_domains from CSV...")
                    with open(csv_path, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            self.execute("INSERT OR IGNORE INTO trusted_domains (domain) VALUES (%s)", (row["domain"],))
        except Exception as e:
            # Fallback to MySQL INSERT syntax if INSERT OR IGNORE fails
            try:
                with open(os.path.join(data_dir, "trusted_domains.csv"), "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.execute("INSERT IGNORE INTO trusted_domains (domain) VALUES (%s)", (row["domain"],))
            except Exception as e2:
                logger.error(f"Failed to seed trusted_domains: {e2}")

        # 2. Seed trusted_senders
        try:
            rows = self.fetch_all("SELECT COUNT(*) as cnt FROM trusted_senders")
            if rows[0]["cnt"] == 0:
                csv_path = os.path.join(data_dir, "trusted_senders.csv")
                if os.path.exists(csv_path):
                    print("Seeding trusted_senders from CSV...")
                    with open(csv_path, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            sender_num = row["sender_number"].strip() or None
                            sender_email = row["sender_email"].strip() or None
                            self.execute(
                                "INSERT INTO trusted_senders (sender_number, sender_email, company_name, status) VALUES (%s, %s, %s, %s)",
                                (sender_num, sender_email, row["company_name"], row["status"])
                            )
        except Exception as e:
            logger.error(f"Failed to seed trusted_senders: {e}")

        # 3. Seed keywords
        try:
            rows = self.fetch_all("SELECT COUNT(*) as cnt FROM keywords")
            if rows[0]["cnt"] == 0:
                print("Seeding keywords from CSV files...")
                k_files = ["fraud_keywords.csv", "phishing_keywords.csv", "logistics_keywords.csv"]
                for k_file in k_files:
                    csv_path = os.path.join(data_dir, k_file)
                    if os.path.exists(csv_path):
                        with open(csv_path, "r", encoding="utf-8") as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                try:
                                    self.execute(
                                        "INSERT OR IGNORE INTO keywords (keyword, category, risk_score) VALUES (%s, %s, %s)",
                                        (row["keyword"], row["category"], float(row["risk_score"]))
                                    )
                                except Exception:
                                    self.execute(
                                        "INSERT IGNORE INTO keywords (keyword, category, risk_score) VALUES (%s, %s, %s)",
                                        (row["keyword"], row["category"], float(row["risk_score"]))
                                    )
        except Exception as e:
            logger.error(f"Failed to seed keywords: {e}")

db = Database()
