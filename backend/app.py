import os
import re
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from database import db
from agents import (
    MLPredictionAgent, 
    FraudIntelligenceAgent, 
    TrustedDomainAgent, 
    TrustedSenderAgent, 
    DomainSpoofingAgent, 
    DatabaseLearningAgent, 
    DecisionAgent
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Flask app to serve the frontend folder directly
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend"))
app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
CORS(app)

# Instantiate Agents
ml_agent = MLPredictionAgent()
fraud_agent = FraudIntelligenceAgent()
trusted_domain_agent = TrustedDomainAgent()
trusted_sender_agent = TrustedSenderAgent()
spoofing_agent = DomainSpoofingAgent()
learning_agent = DatabaseLearningAgent()

decision_agent = DecisionAgent(
    ml_agent, 
    fraud_agent, 
    trusted_domain_agent, 
    trusted_sender_agent, 
    spoofing_agent, 
    learning_agent
)

# Basic email validation regex pattern
EMAIL_REGEX = re.compile(r'^[^@]+@[^@]+\.[^@]+$')

@app.route("/")
def serve_index():
    """Serves index.html from the frontend folder."""
    return send_from_directory(frontend_dir, "index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    """
    POST /analyze
    Inputs: { sender_number, sender_email, message }
    Outputs: { classification, confidence, risk_score, trusted_domain, trusted_sender, domain_spoofing, repeated_message, detected_keywords, reasons, recommendation }
    """
    data = request.get_json() or {}
    sender_number = data.get("sender_number", "").strip()
    sender_email = data.get("sender_email", "").strip()
    message = data.get("message", "").strip()
    
    # 1. Validation: Message is required
    if not message:
        return jsonify({"error": "Message content is required!"}), 400
        
    # 2. Validation: At least one contact detail must be provided
    if not sender_number and not sender_email:
        return jsonify({"error": "Please enter Sender Number or Sender Email."}), 400
        
    # 3. Validation: Sender Number (optional but must be valid if provided)
    if sender_number:
        # Numbers only, length 10 to 15 digits
        if not sender_number.isdigit() or len(sender_number) < 10 or len(sender_number) > 15:
            return jsonify({"error": "Invalid Sender Number. Must be numbers only and between 10 and 15 digits."}), 400
            
    # 4. Validation: Sender Email (optional but must be valid if provided)
    if sender_email:
        if not EMAIL_REGEX.match(sender_email):
            return jsonify({"error": "Invalid Sender Email. Must follow standard email format (e.g. name@domain.com)."}), 400
            
    try:
        # Run agentic analysis
        res = decision_agent.analyze(sender_number, sender_email, message)
        
        # Save analysis log into the database
        try:
            db.execute(
                """
                INSERT INTO message_history (
                    sender_number, sender_email, message, risk_score, 
                    classification, confidence
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    sender_number or None,
                    sender_email or None,
                    message,
                    res["risk_score"],
                    res["classification"],
                    res["confidence"]
                )
            )
        except Exception as db_err:
            logger.error(f"Database logging to message_history failed: {db_err}")
            
        return jsonify(res), 200
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({"error": f"Internal system analysis failed: {str(e)}"}), 500

if __name__ == "__main__":
    # Ensure database tables are initialized
    db.init_db()
    
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
