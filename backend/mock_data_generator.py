import os
import random
import csv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Ensure folder exists
data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(data_dir, exist_ok=True)

# Seed for reproducibility
random.seed(42)
np.random.seed(42)

def generate_synthetic_data(num_records=1000):
    print(f"Generating {num_records} synthetic logistics records...")
    
    # 1. Generate Vendors
    vendors = []
    vendor_ids = [f"VND-{100 + i}" for i in range(25)]
    vendor_names = [
        "Atlas Cargo Services", "BlueSky Transport", "Cascade Logistics", "Delta Freight Systems",
        "Apex Carrier Group", "Frontier Hauling", "GoldStar Logistics", "Horizon Freight",
        "Interstate Carriers", "Jupiter Shipping", "Krypton Logistics", "Liberty Cargo",
        "Metro Logistics", "Northern Transport", "Oceanic Shipping", "Pinnacle Freight",
        "Quantum Logistics", "RedLine Transport", "Summit Logistics", "Titan Haulers",
        "United Cargo", "Vanguard Logistics", "WestCoast Freight", "Xpress Logistics",
        "Zephyr Shipping"
    ]
    
    for i, vid in enumerate(vendor_ids):
        # Create normal and high-risk vendors
        is_shady = (i % 5 == 0)  # 20% are suspicious vendors
        if is_shady:
            trust_score = round(random.uniform(40.0, 75.0), 1)
            incidents = random.randint(3, 9)
            sla_compliance = round(random.uniform(65.0, 85.0), 1)
            status = "Under_Review" if random.choice([True, False]) else "Active"
        else:
            trust_score = round(random.uniform(85.0, 100.0), 1)
            incidents = random.randint(0, 2)
            sla_compliance = round(random.uniform(90.0, 100.0), 1)
            status = "Active"
            
        vendors.append({
            "vendor_id": vid,
            "name": vendor_names[i],
            "trust_score": trust_score,
            "incidents_count": incidents,
            "sla_compliance_rate": sla_compliance,
            "status": status
        })
        
    vendors_df = pd.DataFrame(vendors)
    vendors_df.to_csv(os.path.join(data_dir, "synthetic_vendors.csv"), index=False)
    print("Saved synthetic_vendors.csv")

    # 2. Generate Shipments and Communication Logs
    shipments = []
    communications = []
    
    origins = ["Los Angeles, CA", "Miami, FL", "Houston, TX", "Seattle, WA", "New York, NY", "Chicago, IL", "Atlanta, GA", "Dallas, TX", "San Francisco, CA"]
    destinations = ["Chicago, IL", "New York, NY", "Phoenix, AZ", "Denver, CO", "Detroit, MI", "Boston, MA", "Las Vegas, NV", "Miami, FL", "Houston, TX"]
    routes = ["I-80 E", "I-95 N", "I-10 W", "I-90 E", "I-75 N", "I-40 W", "I-70 E", "I-35 N", "I-5 S"]
    
    phishing_domains = ["@gmail-cargo.com", "@apexcorp-logistics.net", "@verizon-dispatcher.org", "@outlook-logistics.com", "@fedex-billing-system.com"]
    safe_domains = {
        "VND-100": "atlascargo.com", "VND-101": "blueskytransport.com", "VND-102": "cascadelogistics.com",
        "VND-103": "deltafreight.com", "VND-104": "apexcarrier.com", "VND-105": "frontierhauling.com",
        "VND-106": "goldstarlogistics.com", "VND-107": "horizonfreight.com", "VND-108": "interstatecarriers.com",
        "VND-109": "jupitershipping.com", "VND-110": "kryptonlogistics.com", "VND-111": "libertycargo.com",
        "VND-112": "metrologistics.com", "VND-113": "northerntransport.com", "VND-114": "oceanicshipping.com",
        "VND-115": "pinnaclefreight.com", "VND-116": "quantumlogistics.com", "VND-117": "redlinetransport.com",
        "VND-118": "summitlogistics.com", "VND-119": "titanhaulers.com", "VND-120": "unitedcargo.com",
        "VND-121": "vanguardlogistics.com", "VND-122": "westcoastfreight.com", "VND-123": "xpresslogistics.com",
        "VND-124": "zephyrshipping.com"
    }

    suspicious_keywords = [
        "URGENT rerouting", "Immediate payment update", "Change banking details", 
        "bypass dispatcher", "DO NOT CALL", "route modified due to mechanical issues", 
        "deliver to secondary dock", "turn off GPS tracking", "update credit terms",
        "wire transfer required", "unauthorized delivery terminal"
    ]
    
    normal_email_templates = [
        "Hi Team, please find attached the BOL for shipment {shp_id}. Let us know if you need anything else.",
        "Good morning, here is the tracking status report for cargo. The driver is currently in transit and ETA is looking good.",
        "Hello, gate check-in has been completed for shipment {shp_id} in {origin}. Estimated arrival in {dest} remains unchanged.",
        "Confirming receipt of the shipment request. We will assign a driver soon. Best regards.",
        "Attached are the truck inspection logs and driver credentials for carrier verification."
    ]

    normal_sms_templates = [
        "DriverJohn here. SHP {shp_id} load completed. Departing origin now.",
        "Arrived at receiver. Waiting for dock assignment. Everything secure.",
        "Highway construction near check point. Delay of 30 mins, but route remains secure.",
        "Refueling. Trailer locks checked and secure."
    ]

    suspicious_email_templates = [
        "URGENT UPDATE: Shipment {shp_id} has been rerouted due to warehouse maintenance. Deliver to alternative dock: 404 Industrial Way, {dest} immediately.",
        "Important billing update for {shp_id}. Due to audit, we changed bank details. Wire payment to routing 021000021, account 992837262. Confirm transaction asap.",
        "Notice of Carrier Change: Driver John is unavailable. Carrier has been switched to Priority Logistics. Please release the load to truck ID {carrier_id}.",
        "Dear customer, system outage has affected our primary logistics email. Do not reply to standard office number. Confirm container drop details via this email."
    ]

    suspicious_sms_templates = [
        "Driver: Reroute load {shp_id} now. Destination changed. Go to loading dock 4 behind retail complex.",
        "Ops alert: GPS system updating. Turn off transponder for 2 hours to avoid sync error. Maintain driving speed.",
        "Security notice: Logistics portal compromised. Contact broker ONLY at +1 (555) 019-3829. Do not use main desk line.",
        "Rerouting SHP {shp_id}. Deliver load to {dest} West Compound instead of Main Terminal."
    ]

    # Date generator
    start_date = datetime.now() - timedelta(days=90)
    
    for i in range(num_records):
        shp_id = f"SHP-{1000 + i}"
        vendor_id = random.choice(vendor_ids)
        vendor_info = next(v for v in vendors if v["vendor_id"] == vendor_id)
        
        # Decide if this shipment is part of a fraud attempt (approx 15% fraud rate)
        # Higher risk if vendor trust score is lower
        fraud_risk = 0.05 + (100.0 - vendor_info["trust_score"]) / 150.0
        is_fraud = random.random() < fraud_risk
        
        origin = random.choice(origins)
        # Avoid destination matching origin
        dest = random.choice([d for d in destinations if d != origin])
        route = random.choice(routes)
        carrier_id = f"CAR-{random.randint(100, 999)}"
        
        # Weight in kg (normal freight cargo ranges 2000-22000 kg)
        # Cost in USD (normal cargo ranges $2000 - $80000)
        # Fraud: High value cargo at suspiciously low weights (cargo theft of electronics, pharma)
        if is_fraud and random.choice([True, False]):
            # Anomaly: Low weight, extremely high value
            weight_kg = round(random.uniform(100.0, 1500.0), 1)
            cost_usd = round(random.uniform(90000.0, 250000.0), 2)
        else:
            weight_kg = round(random.uniform(3000.0, 22000.0), 1)
            cost_usd = round(weight_kg * random.uniform(1.5, 4.0), 2)
            
        dep_date = start_date + timedelta(days=random.randint(1, 85), hours=random.randint(0, 23))
        # Add transit time
        arr_date = dep_date + timedelta(days=random.randint(1, 4), hours=random.randint(4, 12))
        
        status = "Delivered" if arr_date < datetime.now() else "Pending"
        if is_fraud and status == "Pending":
            status = "Under_Investigation"
            
        shipments.append({
            "shipment_id": shp_id,
            "vendor_id": vendor_id,
            "carrier_id": carrier_id,
            "origin": origin,
            "destination": dest,
            "route_details": route,
            "weight_kg": weight_kg,
            "cost_usd": cost_usd,
            "scheduled_departure": dep_date.strftime("%Y-%m-%d %H:%M:%S"),
            "scheduled_arrival": arr_date.strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
            "is_fraud": 1 if is_fraud else 0
        })
        
        # Generate communication logs for this shipment
        num_comms = random.randint(1, 3)
        for c in range(num_comms):
            comm_type = random.choice(["Email", "SMS"])
            is_comm_fraud = 0
            
            # If the shipment is fraud, communications can be fraudulent
            if is_fraud and random.random() < 0.7:
                is_comm_fraud = 1
                sender_domain = random.choice(phishing_domains)
                sender = f"dispatch{sender_domain}" if comm_type == "Email" else f"+1555{random.randint(1000000, 9999999)}"
                receiver = f"ops@controlcenter.com" if comm_type == "Email" else f"+1555{random.randint(1000000, 9999999)}"
                
                if comm_type == "Email":
                    text = random.choice(suspicious_email_templates).format(shp_id=shp_id, dest=dest, carrier_id=carrier_id)
                else:
                    text = random.choice(suspicious_sms_templates).format(shp_id=shp_id, dest=dest)
            else:
                domain = safe_domains[vendor_id]
                sender = f"info@{domain}" if comm_type == "Email" else f"+1555{random.randint(1000000, 9999999)}"
                receiver = f"ops@controlcenter.com" if comm_type == "Email" else f"+1555{random.randint(1000000, 9999999)}"
                
                if comm_type == "Email":
                    text = random.choice(normal_email_templates).format(shp_id=shp_id, origin=origin, dest=dest)
                else:
                    text = random.choice(normal_sms_templates).format(shp_id=shp_id)
                    
            communications.append({
                "shipment_id": shp_id,
                "sender": sender,
                "receiver": receiver,
                "message_type": comm_type,
                "message_content": text,
                "is_fraudulent": is_comm_fraud,
                "fraud_probability": round(random.uniform(0.7, 0.99), 2) if is_comm_fraud else round(random.uniform(0.0, 0.25), 2),
                "created_at": dep_date.strftime("%Y-%m-%d %H:%M:%S")
            })

    shipments_df = pd.DataFrame(shipments)
    shipments_df.to_csv(os.path.join(data_dir, "synthetic_shipments.csv"), index=False)
    print("Saved synthetic_shipments.csv")
    
    comms_df = pd.DataFrame(communications)
    comms_df.to_csv(os.path.join(data_dir, "synthetic_communications.csv"), index=False)
    print("Saved synthetic_communications.csv")
    print("Data generation complete!")

if __name__ == "__main__":
    generate_synthetic_data()
