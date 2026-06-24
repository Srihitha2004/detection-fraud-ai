import os
import re
import json
import joblib
import logging
import requests
import numpy as np
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class AgenticFraudEngine:
    """
    Agentic AI engine containing 7 specialized agents.
    Tries to connect to Ollama (Llama 3/Mistral/Phi-3) for agent reasoning.
    If Ollama is not running, falls back to a highly sophisticated, rule-based NLP system.
    """

    def __init__(self, ollama_url="http://localhost:11434/api/generate", model_name="llama3"):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.ml_model_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "models", "best_model.pkl"
        )
        self.ml_pipeline = None
        self._load_ml_model()

    def _load_ml_model(self):
        """Attempts to load the serialized ML best model pipeline."""
        if os.path.exists(self.ml_model_path):
            try:
                self.ml_pipeline = joblib.load(self.ml_model_path)
                logger.info("Successfully loaded ML model for Agentic Engine.")
            except Exception as e:
                logger.error(f"Error loading ML model: {e}")
        else:
            logger.warning("ML model file not found. ML Prediction Agent will use heuristic fallback.")

    def _call_ollama(self, prompt, system_prompt=""):
        """Calls local Ollama API. Returns response string if successful, else None."""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2
                }
            }
            response = requests.post(self.ollama_url, json=payload, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
        except Exception as e:
            # Silence connection errors to allow smooth fallback
            pass
        return None

    # --- AGENT 1: Communication Analysis Agent ---
    def communication_agent(self, sender, receiver, message_content, message_type):
        """Analyzes text messages/emails for phishing, urgent tones, spoofing, etc."""
        system_prompt = (
            "You are a Communication Analysis Agent specialized in detecting cargo theft fraud. "
            "Examine the message for spoofed domains, phishing attempts, urgent tones, bank changes, "
            "and suspicious instructions. Respond in JSON format with: 'is_fraud' (boolean), "
            "'confidence' (0.0 to 1.0), and 'thoughts' (string detailing your analysis)."
        )
        
        prompt = (
            f"Sender: {sender}\nReceiver: {receiver}\nType: {message_type}\n"
            f"Content: {message_content}\n\nAnalyze this message and return the JSON structure."
        )
        
        # Try LLM
        llm_response = self._call_ollama(prompt, system_prompt)
        if llm_response:
            try:
                # Attempt to extract JSON from markdown wrappers
                match = re.search(r"\{.*\}", llm_response, re.DOTALL)
                if match:
                    res = json.loads(match.group(0))
                    return res["is_fraud"], res["confidence"], res["thoughts"]
            except Exception:
                pass
                
        # Heuristic NLP Fallback (Highly sophisticated checks)
        thoughts = []
        confidence = 0.0
        is_fraud = False
        
        # 1. Domain Check (for Emails)
        if message_type.lower() == "email":
            # Extract domain
            domain_match = re.search(r"@([\w.-]+)", sender.lower())
            if domain_match:
                domain = domain_match.group(1)
                # Known logistics spoof pattern check
                spoof_patterns = ["gmail-cargo", "logistics-net", "dispatcher-org", "outlook-logistics", "freights-ltd"]
                if any(pat in domain for pat in spoof_patterns):
                    is_fraud = True
                    confidence += 0.45
                    thoughts.append(f"Spoofed sender domain detected: '@{domain}' matches known cargo-phishing profiles.")
                elif domain in ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]:
                    is_fraud = True
                    confidence += 0.25
                    thoughts.append("Official logistics message sent from a free personal email address (freemail).")
                    
        # 2. Urgent / Coercive Language
        urgency_words = ["urgent", "immediately", "asap", "quick", "critical", "attention required", "action required"]
        if any(word in message_content.lower() for word in urgency_words):
            confidence += 0.15
            thoughts.append("Urgent time-sensitive tone detected, typical of social engineering pressure tactics.")

        # 3. Fraud-Specific Context (Rerouting, banking updates)
        if "reroute" in message_content.lower() or "alternative warehouse" in message_content.lower() or "deliver to" in message_content.lower():
            is_fraud = True
            confidence += 0.35
            thoughts.append("Instruction to reroute shipment or deliver to secondary location detected.")
            
        if "bank" in message_content.lower() or "routing" in message_content.lower() or "wire" in message_content.lower() or "payment detail" in message_content.lower():
            is_fraud = True
            confidence += 0.30
            thoughts.append("Request to modify banking details or request wire transfer detected.")
            
        if "gps" in message_content.lower() or "transponder" in message_content.lower() or "turn off" in message_content.lower() or "tracker" in message_content.lower():
            is_fraud = True
            confidence += 0.40
            thoughts.append("Suspicious command telling driver to disable GPS tracking transponder.")

        confidence = min(confidence, 0.99)
        if confidence > 0.45:
            is_fraud = True
            
        if not thoughts:
            thoughts.append("No obvious phishing, spoofing, or fraudulent keywords identified in message text.")
            confidence = 0.05
            
        return is_fraud, confidence, " | ".join(thoughts)

    # --- AGENT 2: Vendor Intelligence Agent ---
    def vendor_agent(self, trust_score, incidents_count, sla_compliance_rate, status):
        """Analyzes vendor history and calculates a risk multiplier based on historical incidents and SLAs."""
        score_contribution = 0.0
        thoughts = []
        
        # High incidents
        if incidents_count > 5:
            score_contribution += 30.0
            thoughts.append(f"High risk: Vendor has {incidents_count} prior security/delivery incidents.")
        elif incidents_count > 2:
            score_contribution += 15.0
            thoughts.append(f"Elevated risk: Vendor has {incidents_count} historical incidents.")
            
        # Poor SLA Compliance
        if sla_compliance_rate < 75.0:
            score_contribution += 25.0
            thoughts.append(f"Critical SLA breach: compliance is extremely low ({sla_compliance_rate}%).")
        elif sla_compliance_rate < 90.0:
            score_contribution += 10.0
            thoughts.append(f"Suboptimal SLA: compliance rate at {sla_compliance_rate}%.")
            
        # Status check
        if status.lower() == "suspended":
            score_contribution += 40.0
            thoughts.append("CRITICAL: Vendor status is set to 'Suspended'. All assignments should be halted.")
        elif status.lower() == "under_review":
            score_contribution += 20.0
            thoughts.append("Vendor is currently 'Under Review' due to previous compliance failure.")
            
        # Trust score
        if trust_score < 60.0:
            score_contribution += 25.0
            thoughts.append(f"Low trust rating: score is {trust_score}/100.")
        elif trust_score < 85.0:
            score_contribution += 10.0
            
        if not thoughts:
            thoughts.append("Vendor profile is clean. High trust rating and solid SLA compliance.")
            
        score_contribution = min(score_contribution, 100.0)
        return score_contribution, " | ".join(thoughts)

    # --- AGENT 3: Shipment Intelligence Agent ---
    def shipment_agent(self, weight_kg, cost_usd):
        """Detects anomalies in shipment metadata (high cost density, weight/cost mismatches)."""
        score_contribution = 0.0
        thoughts = []
        
        cost_weight_ratio = cost_usd / (weight_kg + 1e-5)
        
        # Anomaly: Low weight, very high cost (e.g. cargo theft of microchips, drugs, luxury goods)
        if weight_kg < 1500.0 and cost_usd > 80000.0:
            score_contribution += 35.0
            thoughts.append(f"High Value Density Anomaly: Weight ({weight_kg}kg) is extremely light relative to value (${cost_usd:,.2f}). High-risk target.")
        elif weight_kg < 5000.0 and cost_usd > 120000.0:
            score_contribution += 20.0
            thoughts.append(f"Elevated cost density: Weight is {weight_kg}kg, cost is ${cost_usd:,.2f}.")
            
        if cost_usd > 180000.0:
            score_contribution += 15.0
            thoughts.append("Ultra high-value load. Exceeds standard cargo insurance thresholds.")
            
        if weight_kg <= 0.0:
            score_contribution += 30.0
            thoughts.append("Zero or negative weight reported. Invalid manifest entry.")
            
        if not thoughts:
            thoughts.append("Shipment parameters (weight and valuation) match expected normal cargo profiles.")
            
        score_contribution = min(score_contribution, 100.0)
        return score_contribution, " | ".join(thoughts)

    # --- AGENT 4: Route Intelligence Agent ---
    def route_agent(self, origin, destination, route_details, scheduled_departure):
        """Evaluates geographical risks and routing departures."""
        score_contribution = 0.0
        thoughts = []
        
        high_risk_hubs = ["Los Angeles, CA", "Miami, FL", "Houston, TX", "Atlanta, GA", "New York, NY"]
        
        if origin in high_risk_hubs:
            score_contribution += 10.0
            thoughts.append(f"Origin '{origin}' is a designated cargo theft hotspot.")
            
        if destination in high_risk_hubs:
            score_contribution += 10.0
            thoughts.append(f"Destination '{destination}' is in a high-theft logistical corridor.")
            
        # Night departure check (between 10 PM and 4 AM)
        try:
            dep_dt = datetime.strptime(scheduled_departure, "%Y-%m-%d %H:%M:%S")
            hour = dep_dt.hour
            if hour >= 22 or hour <= 4:
                score_contribution += 15.0
                thoughts.append(f"Late-night dispatch scheduled ({hour:02d}:00). Statistically higher cargo theft vulnerability.")
        except Exception:
            pass
            
        if not thoughts:
            thoughts.append("Route details indicate low-threat corridors and scheduled daytime travel.")
            
        score_contribution = min(score_contribution, 100.0)
        return score_contribution, " | ".join(thoughts)

    # --- AGENT 5: ML Prediction Agent ---
    def ml_agent(self, shipment_data):
        """Runs the trained ML pipeline to predict statistical probability."""
        if not self.ml_pipeline:
            # Handcoded fallback formula to approximate model
            prob = 0.05
            if shipment_data.get("comm_fraud_flags", 0) > 0:
                prob += 0.40
            if shipment_data.get("trust_score", 100) < 70:
                prob += 0.20
            if shipment_data.get("cost_usd", 0) / (shipment_data.get("weight_kg", 1) + 1e-5) > 100:
                prob += 0.20
            prob = min(prob, 0.99)
            return prob, f"Heuristic prediction: Probability estimated at {prob:.2f} due to baseline rule evaluation."
            
        try:
            # Build DataFrame row
            row_dict = {}
            for col in self.ml_pipeline["feature_cols"]:
                # Lookup in shipment_data
                val = shipment_data.get(col, 0)
                # Map categorical columns with encoders if needed
                if col in self.ml_pipeline["label_encoders"]:
                    le = self.ml_pipeline["label_encoders"][col]
                    try:
                        # Check if the class is seen
                        if str(val) in le.classes_:
                            val = le.transform([str(val)])[0]
                        else:
                            val = le.transform([le.classes_[0]])[0] # Fallback to first class
                    except Exception:
                        val = 0
                row_dict[col] = [val]
                
            df_row = pd.DataFrame(row_dict)
            
            # Scale numeric features
            cols_to_scale = ["weight_kg", "cost_usd", "trust_score", "incidents_count", 
                             "sla_compliance_rate", "comm_max_prob", "cost_weight_ratio"]
            scaler = self.ml_pipeline["scaler"]
            df_row[cols_to_scale] = scaler.transform(df_row[cols_to_scale])
            
            # Predict
            clf = self.ml_pipeline["model"]
            prob = float(clf.predict_proba(df_row)[0][1])
            model_name = self.ml_pipeline["model_name"]
            
            return prob, f"Trained model '{model_name}' evaluated. Statistical fraud probability is {prob:.4f}."
        except Exception as e:
            logger.error(f"Error in ML Agent execution: {e}")
            return 0.1, f"ML Agent error: {e}. Default baseline probability applied."

    # --- AGENT 6: Fraud Investigation Agent (Explainability Agent) ---
    def investigation_agent(self, shipment_id, agent_outputs, final_score, risk_level):
        """Generates detailed explanation and recommendations for investigations."""
        system_prompt = (
            "You are a senior Fraud Investigation Copilot. "
            "Combine the findings of the Communication Agent, Vendor Agent, Route Agent, "
            "Shipment Agent, and ML Agent. Explain the alert level and compile 4 clear, "
            "actionable security protocols to mitigate risks. Respond in standard Markdown format."
        )
        
        prompt = (
            f"Shipment: {shipment_id}\n"
            f"Risk Level: {risk_level} (Score: {final_score}/100)\n\n"
            f"Agent Findings:\n"
            f"- Communication Agent: {agent_outputs['comm_thoughts']}\n"
            f"- Vendor Agent: {agent_outputs['vendor_thoughts']}\n"
            f"- Shipment Agent: {agent_outputs['shipment_thoughts']}\n"
            f"- Route Agent: {agent_outputs['route_thoughts']}\n"
            f"- ML Prediction Agent: {agent_outputs['ml_thoughts']}\n"
        )
        
        # Try LLM
        llm_response = self._call_ollama(prompt, system_prompt)
        if llm_response:
            return llm_response
            
        # Heuristic Generator (Markdown Format)
        recs = []
        if risk_level == "SAFE":
            recs = [
                "Proceed with standard logistics check-in.",
                "Verify driver identity at gate using ID card and standard manifest.",
                "Ensure cargo locks are checked prior to departure."
            ]
        elif risk_level in ["LOW RISK", "MEDIUM RISK"]:
            recs = [
                "Perform standard dispatch check. Confirm cargo paperwork (BOL) matches driver records.",
                "Contact the carrier dispatcher via the official office line to confirm driver identity.",
                "Instruct driver to keep tracking transponder active at all times during transit.",
                "Monitor transit check-ins. Require driver updates every 4 hours."
            ]
        else: # HIGH RISK or CRITICAL FRAUD
            recs = [
                "**HOLD CARGO**: Instruct gate security to prevent cargo from leaving secure custody immediately.",
                "**VERIFY IDENTITIES**: Call the vendor on a pre-established, verified hotline. Do not use the phone numbers or email addresses provided in the recent emails/SMS.",
                "**DISPATCH SECURITY**: Issue secondary gate check for driver credentials, tractor ID, and trailer locks. Cross-check DMV license plates.",
                "**INVESTIGATE MESSAGES**: Audit company logistics servers for signs of employee account compromise or spoofed carrier email headers."
            ]
            
        md = f"### Investigation Dossier for Shipment **{shipment_id}**\n\n"
        md += f"#### Executive Summary\n"
        md += f"The platform has classified this shipment as **{risk_level}** with an aggregated threat score of **{final_score:.1f}/100**.\n\n"
        
        md += "#### Key Fraud Indicators Detected:\n"
        indicators = []
        if "phishing" in agent_outputs["comm_thoughts"].lower() or "spoof" in agent_outputs["comm_thoughts"].lower() or "gmail" in agent_outputs["comm_thoughts"].lower():
            indicators.append("🚨 **Spoofed Communications**: Phishing attempts or non-official email domains detected in logs.")
        if "reroute" in agent_outputs["comm_thoughts"].lower():
            indicators.append("🚨 **Rerouting Attempt**: Suspicious text-based request to change cargo delivery location.")
        if "trust" in agent_outputs["vendor_thoughts"].lower() or "incident" in agent_outputs["vendor_thoughts"].lower() or "suspended" in agent_outputs["vendor_thoughts"].lower():
            indicators.append("🚨 **Vendor Risk**: Historical SLA violations, high carrier incident rates, or suspended vendor status.")
        if "density" in agent_outputs["shipment_thoughts"].lower() or "weight" in agent_outputs["shipment_thoughts"].lower():
            indicators.append("🚨 **Cargo Anomaly**: High cost density or physical manifest details mismatch standard loads.")
        if "night" in agent_outputs["route_thoughts"].lower() or "hotspot" in agent_outputs["route_thoughts"].lower():
            indicators.append("🚨 **Route/Scheduling Risk**: Late-night departures or origin hubs in cargo-theft hotspots.")
            
        if not indicators:
            if final_score > 40:
                indicators.append("⚠️ **Statistical ML Flag**: High probability score generated by predictive model matching historical fraud vectors.")
            else:
                indicators.append("✅ **No Significant Risk**: Baseline parameters are within normal tolerances.")
                
        for ind in indicators:
            md += f"- {ind}\n"
            
        md += "\n#### Recommended Action Plan:\n"
        for i, rec in enumerate(recs, 1):
            md += f"{i}. {rec}\n"
            
        md += "\n*Report generated automatically by the explainability agent.*"
        return md

    # --- AGENT 7: Decision Agent (Aggregator) ---
    def orchestrate_analysis(self, shipment_id, origin, destination, route_details, weight_kg, cost_usd, scheduled_departure, vendor_info, message_logs):
        """Orchestrates all agents to produce a final aggregated risk score and decision."""
        # 1. Comms Analysis
        comm_fraud_flags = 0
        comm_max_prob = 0.0
        comm_thoughts_list = []
        
        for msg in message_logs:
            is_f, conf, thoughts = self.communication_agent(
                msg.get("sender", ""), msg.get("receiver", ""), msg.get("message_content", ""), msg.get("message_type", "Email")
            )
            if is_f:
                comm_fraud_flags += 1
            comm_max_prob = max(comm_max_prob, conf)
            comm_thoughts_list.append(f"[{msg.get('message_type')} from {msg.get('sender')}]: {thoughts}")
            
        comm_thoughts = " | ".join(comm_thoughts_list) if comm_thoughts_list else "No communication logs available."
        
        # 2. Vendor Analysis
        vendor_contribution, vendor_thoughts = self.vendor_agent(
            vendor_info.get("trust_score", 100.0),
            vendor_info.get("incidents_count", 0),
            vendor_info.get("sla_compliance_rate", 100.0),
            vendor_info.get("status", "Active")
        )
        
        # 3. Shipment Analysis
        shipment_contribution, shipment_thoughts = self.shipment_agent(weight_kg, cost_usd)
        
        # 4. Route Analysis
        route_contribution, route_thoughts = self.route_agent(origin, destination, route_details, scheduled_departure)
        
        # 5. ML Prediction
        shipment_data = {
            "weight_kg": weight_kg,
            "cost_usd": cost_usd,
            "trust_score": vendor_info.get("trust_score", 100.0),
            "incidents_count": vendor_info.get("incidents_count", 0),
            "sla_compliance_rate": vendor_info.get("sla_compliance_rate", 100.0),
            "comm_fraud_flags": comm_fraud_flags,
            "comm_max_prob": comm_max_prob,
            "comm_count": len(message_logs),
            "cost_weight_ratio": cost_usd / (weight_kg + 1e-5),
            "origin": origin,
            "destination": destination,
            "route_details": route_details,
            "scheduled_departure": scheduled_departure
        }
        ml_prob, ml_thoughts = self.ml_agent(shipment_data)
        
        # 6. Risk Scoring Formula
        # Combine metrics: ML probability weights 45%, Comms max fraud weights 25%, Vendor history weights 15%, Shipment details weights 10%, Route details weights 5%
        ml_contrib = ml_prob * 100.0
        comms_contrib = comm_max_prob * 100.0
        
        final_score = (
            (ml_contrib * 0.40) +
            (comms_contrib * 0.30) +
            (vendor_contribution * 0.15) +
            (shipment_contribution * 0.10) +
            (route_contribution * 0.05)
        )
        
        # Classify Fraud Levels
        if final_score <= 20.0:
            risk_level = "SAFE"
        elif final_score <= 40.0:
            risk_level = "LOW RISK"
        elif final_score <= 60.0:
            risk_level = "MEDIUM RISK"
        elif final_score <= 80.0:
            risk_level = "HIGH RISK"
        else:
            risk_level = "CRITICAL FRAUD"
            
        agent_outputs = {
            "comm_thoughts": comm_thoughts,
            "comm_score": comms_contrib,
            "vendor_thoughts": vendor_thoughts,
            "vendor_score": vendor_contribution,
            "shipment_thoughts": shipment_thoughts,
            "shipment_score": shipment_contribution,
            "route_thoughts": route_thoughts,
            "route_score": route_contribution,
            "ml_thoughts": ml_thoughts,
            "ml_score": ml_contrib
        }
        
        # 7. Explainability
        explanation = self.investigation_agent(shipment_id, agent_outputs, final_score, risk_level)
        
        return {
            "shipment_id": shipment_id,
            "final_score": round(final_score, 2),
            "risk_level": risk_level,
            "agent_outputs": agent_outputs,
            "explanation": explanation
        }

# Singleton instance
agent_engine = AgenticFraudEngine()
