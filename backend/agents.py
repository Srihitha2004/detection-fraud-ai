import os
import csv
import math
import joblib
import logging
from database import db

logger = logging.getLogger(__name__)

class MLPredictionAgent:
    """
    Agent 1: ML Prediction Agent
    Loads the trained model (Logistic Regression or SVM) and performs prediction.
    """
    def __init__(self):
        self.model_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "models", "best_model.pkl"
        )
        self.model_data = None
        self._load_model()
        
    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model_data = joblib.load(self.model_path)
                logger.info(f"ML Agent loaded best model: {self.model_data['model_name']}")
            except Exception as e:
                logger.error(f"Failed to load ML model: {e}")
        else:
            logger.warning("Serialized model file missing. ML Agent will use fallback heuristics.")

    def predict(self, text):
        if not self.model_data:
            # Fallback heuristics
            lower_text = text.lower()
            spam_indicators = ["otp", "verify", "suspended", "reward", "prize", "winner", "routing", "kyc"]
            hits = sum(1 for ind in spam_indicators if ind in lower_text)
            prob = min(0.05 + hits * 0.20, 0.99)
            pred_label = "spam" if prob > 0.45 else "ham"
            return pred_label, prob

        try:
            model = self.model_data["model"]
            vectorizer = self.model_data["vectorizer"]
            
            vec_text = vectorizer.transform([text])
            pred_val = int(model.predict(vec_text)[0])
            pred_label = "spam" if pred_val == 1 else "ham"
            
            # Extract probability or confidence value
            if hasattr(model, "predict_proba"):
                prob = float(model.predict_proba(vec_text)[0][1])
            elif hasattr(model, "decision_function"):
                dec_val = float(model.decision_function(vec_text)[0])
                # Convert decision value to probability using Sigmoid
                prob = 1.0 / (1.0 + math.exp(-dec_val))
            else:
                prob = 0.90 if pred_label == "spam" else 0.10
                
            return pred_label, prob
        except Exception as e:
            logger.error(f"Error during ML prediction: {e}")
            return "ham", 0.10


class FraudIntelligenceAgent:
    """
    Agent 2: Fraud Intelligence Agent
    Scans the text using keyword CSV files to detect fraud phrases.
    """
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.keywords = {}
        self.load_keywords()
        
    def load_keywords(self):
        files = ["fraud_keywords.csv", "phishing_keywords.csv", "logistics_keywords.csv"]
        count = 0
        for filename in files:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            kw = row["keyword"].lower().strip()
                            self.keywords[kw] = {
                                "category": row["category"].strip(),
                                "risk_score": float(row["risk_score"])
                            }
                            count += 1
                except Exception as e:
                    logger.error(f"Failed to load keyword file {filepath}: {e}")
        logger.info(f"Fraud Intelligence Agent loaded {count} keywords.")

    def scan_text(self, text):
        lower_text = text.lower()
        matched_keywords = []
        detected_categories = set()
        
        # Sort keywords by length descending to match longest phrases first
        sorted_kws = sorted(self.keywords.keys(), key=len, reverse=True)
        matched_spans = []
        
        for kw in sorted_kws:
            if kw in lower_text:
                start_idx = lower_text.find(kw)
                end_idx = start_idx + len(kw)
                
                # Check overlap
                overlap = False
                for s, e in matched_spans:
                    if not (end_idx <= s or start_idx >= e):
                        overlap = True
                        break
                        
                if not overlap:
                    matched_spans.append((start_idx, end_idx))
                    meta = self.keywords[kw]
                    matched_keywords.append({
                        "keyword": kw,
                        "category": meta["category"],
                        "risk_score": meta["risk_score"]
                    })
                    detected_categories.add(meta["category"])
                    
        return matched_keywords, list(detected_categories)


class TrustedDomainAgent:
    """
    Agent 3: Trusted Domain Agent
    Checks email domain against whitelisted trusted domains in the database.
    """
    def __init__(self):
        pass

    def analyze_domain(self, email):
        if not email or "@" not in email:
            return False, "No"
            
        domain = email.split("@")[-1].lower().strip()
        try:
            # Query MySQL/SQLite trusted_domains table
            res = db.fetch_all("SELECT domain FROM trusted_domains WHERE domain = %s", (domain,))
            if res:
                return True, "Verified FedEx Domain" if "fedex" in domain else f"Verified {domain.split('.')[0].upper()} Domain"
        except Exception as e:
            logger.error(f"Failed to query trusted_domains: {e}")
            # Fallback whitelist
            fallback = ["fedex.com", "fedexexpress.com", "fedexlogistics.com", "dhl.com", "dhl.co.in", "ups.com", "bluedart.com", "delhivery.com", "ecomexpress.in"]
            if domain in fallback:
                return True, "Verified FedEx Domain" if "fedex" in domain else f"Verified {domain.split('.')[0].upper()} Domain"
                
        return False, "No"


class TrustedSenderAgent:
    """
    Agent 4: Trusted Sender Agent
    Checks sender number/email against whitelisted trusted senders in the database.
    """
    def __init__(self):
        pass

    def analyze_sender(self, number, email):
        is_trusted = False
        company = None
        
        # Check by email
        if email and email.strip():
            try:
                res = db.fetch_all("SELECT company_name FROM trusted_senders WHERE sender_email = %s AND status = 'active'", (email.strip(),))
                if res:
                    is_trusted = True
                    company = res[0]["company_name"]
            except Exception as e:
                logger.error(f"Failed to check trusted sender email: {e}")
                
        # Check by number
        if not is_trusted and number and number.strip():
            try:
                res = db.fetch_all("SELECT company_name FROM trusted_senders WHERE sender_number = %s AND status = 'active'", (number.strip(),))
                if res:
                    is_trusted = True
                    company = res[0]["company_name"]
            except Exception as e:
                logger.error(f"Failed to check trusted sender number: {e}")
                
        if is_trusted:
            return True, f"Verified Sender ({company})"
        return False, "No"


class DomainSpoofingAgent:
    """
    Agent 5: Domain Spoofing Agent
    Detects brand lookalike email domains.
    """
    def __init__(self):
        self.brands = ["fedex", "dhl", "ups", "bluedart", "delhivery", "ecomexpress"]

    def analyze_spoofing(self, email, is_trusted_domain):
        if not email or "@" not in email:
            return False, "No"
            
        domain = email.split("@")[-1].lower().strip()
        
        # If it is already verified as trusted domain, it's not spoofed
        if is_trusted_domain:
            return False, "No"
            
        # Check if the domain contains any of our brand keywords but is not whitelisted
        for brand in self.brands:
            if brand in domain:
                return True, "Potential Domain Spoofing Detected"
                
        return False, "No"


class DatabaseLearningAgent:
    """
    Agent 6: Database Learning Agent
    Stores auditing entries and detects repeated message runs.
    """
    def __init__(self):
        pass

    def check_repeated(self, message):
        try:
            # Query message_history for identical message text
            res = db.fetch_all(
                "SELECT risk_score, classification, analysis_date FROM message_history WHERE message = %s ORDER BY analysis_date DESC LIMIT 1",
                (message,)
            )
            if res:
                row = res[0]
                date_str = str(row["analysis_date"]).split(".")[0]
                return True, {
                    "risk_score": int(row["risk_score"]),
                    "classification": row["classification"],
                    "analysis_date": date_str
                }
        except Exception as e:
            logger.error(f"Failed to query duplicate messages: {e}")
            
        return False, None


class DecisionAgent:
    """
    Agent 7: Decision Agent (Orchestrator)
    Integrates ML predictions, whitelists, keyword exclusions, lookalikes, and duplicate audits.
    """
    def __init__(self, ml_agent, fraud_agent, trusted_domain_agent, trusted_sender_agent, spoofing_agent, learning_agent):
        self.ml_agent = ml_agent
        self.fraud_agent = fraud_agent
        self.trusted_domain_agent = trusted_domain_agent
        self.trusted_sender_agent = trusted_sender_agent
        self.spoofing_agent = spoofing_agent
        self.learning_agent = learning_agent

    def analyze(self, sender_number, sender_email, message):
        reasons = []
        recommendations = []
        
        # 1. Run whitelist domain & sender agents
        is_trusted_domain, trusted_domain_status = self.trusted_domain_agent.analyze_domain(sender_email)
        is_trusted_sender, trusted_sender_status = self.trusted_sender_agent.analyze_sender(sender_number, sender_email)
        is_trusted = is_trusted_domain or is_trusted_sender
        
        # 2. Run domain spoofing check
        is_spoofed, spoofing_status = self.spoofing_agent.analyze_spoofing(sender_email, is_trusted_domain)
        
        # 3. Run database learning checks (repeated messages)
        is_repeated, prev_info = self.learning_agent.check_repeated(message)
        
        # 4. Run ML prediction
        ml_label, ml_prob = self.ml_agent.predict(message)
        ml_points = ml_prob * 50.0
        
        # 5. Run keyword scanning
        matched_kws, categories = self.fraud_agent.scan_text(message)
        
        # Exclude common logistics words if trusted (Logistics Rule)
        logistics_stopwords = ["shipment", "package", "parcel", "delivery", "tracking", "courier", "dispatch", "logistics", "hub", "warehouse"]
        
        if is_trusted:
            # Filters out matched keywords that are in logistics_stopwords list
            filtered_kws = [k for k in matched_kws if k["keyword"].lower() not in logistics_stopwords]
        else:
            filtered_kws = matched_kws
            
        kw_count = len(filtered_kws)
        if kw_count == 0:
            kw_points = 0.0
        elif kw_count == 1:
            kw_points = 25.0
        elif kw_count == 2:
            kw_points = 40.0
        else:
            kw_points = 50.0
            
        # 6. Score formulation
        risk_score = ml_points + kw_points
        
        # Add spoofing penalty
        if is_spoofed:
            risk_score += 20.0
            reasons.append("Potential Domain Spoofing Detected")
            recommendations.append("Warning: Domain resembles trusted brand but is unverified. Avoid clicking links.")
            
        # Add repeated message penalty
        if is_repeated and prev_info:
            risk_score += 10.0
            reasons.append("Repeated Message Detected")
            
        # Apply trust waivers (domain or sender)
        if is_trusted:
            if is_trusted_domain:
                risk_score -= 20.0
                reasons.append(f"Trusted Domain: {trusted_domain_status}")
            if is_trusted_sender:
                risk_score -= 25.0
                reasons.append(f"Trusted Sender: {trusted_sender_status}")
                
        # Capping score
        risk_score = min(max(risk_score, 0.0), 100.0)
        risk_score_int = int(round(risk_score))
        
        # Verdict calculation
        if risk_score_int < 35:
            classification = "SAFE"
        elif risk_score_int < 75:
            classification = "SUSPICIOUS"
        else:
            classification = "FRAUD"
            
        # Build explanation logs
        if ml_label == "spam":
            reasons.append("ML Model Classified as Fraud")
            
        # Append matched fraud phrase indicators
        phrases_matched = [k["keyword"] for k in filtered_kws if k["risk_score"] > 0.40]
        if phrases_matched:
            reasons.append(f"Detected suspicious phrases: {', '.join(phrases_matched[:3])}")
            
        if not reasons:
            reasons.append("No active phishing or spam markers detected")
            
        # Recommendations
        if classification == "SAFE":
            recommendations.append("Safe to proceed")
        elif classification == "SUSPICIOUS":
            recommendations.append("Verify the message directly via official corporate directory channels.")
            recommendations.append("Do not click links or download any unverified attachments.")
        else:
            recommendations.append("Do not share OTP or sensitive credentials.")
            recommendations.append("Block sender details immediately.")
            recommendations.append("Report spoofing attempt to security gate operations.")

        # Formatting duplicate display
        if is_repeated and prev_info:
            repeated_status_display = f"Repeated Message Detected (Previous classification: {prev_info['classification']} | Previous Risk Score: {prev_info['risk_score']} | Checked On: {prev_info['analysis_date']})"
        else:
            repeated_status_display = "New"

        return {
            "classification": classification,
            "confidence": round(ml_prob * 100.0, 1),
            "risk_score": risk_score_int,
            "trusted_domain": trusted_domain_status,
            "trusted_sender": trusted_sender_status,
            "domain_spoofing": spoofing_status,
            "repeated_message": repeated_status_display,
            "detected_keywords": [kw["keyword"] for kw in filtered_kws],
            "reasons": reasons,
            "recommendation": recommendations
        }
