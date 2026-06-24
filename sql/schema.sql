-- SQL schema for Hackathon AI Fraud Detection Portal
-- Compatible with MySQL and SQLite

CREATE TABLE IF NOT EXISTS message_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_number VARCHAR(100),
    sender_email VARCHAR(255),
    message TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    classification VARCHAR(50) NOT NULL, -- SAFE, SUSPICIOUS, FRAUD
    confidence FLOAT NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trusted_domains (
    domain VARCHAR(255) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS trusted_senders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_number VARCHAR(100),
    sender_email VARCHAR(255),
    company_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS keywords (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword VARCHAR(150) UNIQUE NOT NULL,
    category VARCHAR(100) NOT NULL,
    risk_score FLOAT NOT NULL
);
