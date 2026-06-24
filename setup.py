import os
import sys
import logging

# Ensure the root of the project is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.database import db
from backend.mock_data_generator import generate_synthetic_data
from backend.ml_pipeline import LogisticsFraudMLPipeline

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("setup_bootstrap")

def bootstrap():
    logger.info("="*60)
    logger.info("BOOTSTRAPPING SENTINEL CARGO THEFT FRAUD PLATFORM")
    logger.info("="*60)
    
    # 1. Initialize Database
    logger.info("[Step 1] Initializing Database Schema...")
    db_success = db.init_database()
    if not db_success:
        logger.error("Failed to initialize database. Aborting bootstrap.")
        sys.exit(1)
    logger.info("Database initialized successfully.")
    
    # 2. Generate Synthetic Datasets
    logger.info("[Step 2] Synthesizing Logistics & Communication Datasets...")
    try:
        generate_synthetic_data(num_records=1000)
    except Exception as e:
        logger.error(f"Failed to generate mock data: {e}")
        sys.exit(1)
    logger.info("Dataset synthesis complete.")
    
    # 3. Train Machine Learning Models
    logger.info("[Step 3] Running ML Pipeline: Training & Comparison...")
    try:
        pipeline = LogisticsFraudMLPipeline()
        metrics = pipeline.run_pipeline()
        logger.info("ML pipeline run complete. Best classifier successfully serialized to models/best_model.pkl.")
    except Exception as e:
        logger.error(f"ML Pipeline execution failed: {e}")
        sys.exit(1)
        
    logger.info("="*60)
    logger.info("BOOTSTRAP PROCESS COMPLETED SUCCESSFULLY")
    logger.info("="*60)

if __name__ == "__main__":
    bootstrap()
    
    # 4. Start Flask App Server
    logger.info("Starting Flask application server...")
    from backend.app import app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
