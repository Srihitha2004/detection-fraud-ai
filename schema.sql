-- SQL Database Schema for Cyber Cargo Theft Fraud Detection Platform
-- Compatible with both MySQL and SQLite

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Dispatcher',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vendors (
    vendor_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    trust_score FLOAT NOT NULL DEFAULT 100.0,
    incidents_count INTEGER NOT NULL DEFAULT 0,
    sla_compliance_rate FLOAT NOT NULL DEFAULT 100.0,
    status VARCHAR(50) NOT NULL DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id VARCHAR(50) PRIMARY KEY,
    vendor_id VARCHAR(50),
    carrier_id VARCHAR(50) NOT NULL,
    origin VARCHAR(150) NOT NULL,
    destination VARCHAR(150) NOT NULL,
    route_details VARCHAR(255) NOT NULL,
    weight_kg FLOAT NOT NULL,
    cost_usd FLOAT NOT NULL,
    scheduled_departure TIMESTAMP,
    scheduled_arrival TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    FOREIGN KEY(vendor_id) REFERENCES vendors(vendor_id)
);

CREATE TABLE IF NOT EXISTS communications (
    comm_id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id VARCHAR(50),
    sender VARCHAR(150) NOT NULL,
    receiver VARCHAR(150) NOT NULL,
    message_type VARCHAR(10) NOT NULL, -- 'Email' or 'SMS'
    message_content TEXT NOT NULL,
    is_fraudulent BOOLEAN DEFAULT 0,
    fraud_probability FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(shipment_id) REFERENCES shipments(shipment_id)
);

CREATE TABLE IF NOT EXISTS fraud_predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id VARCHAR(50),
    model_name VARCHAR(100) NOT NULL,
    fraud_probability FLOAT NOT NULL,
    predicted_label INTEGER NOT NULL, -- 0 for Safe, 1 for Fraud
    prediction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(shipment_id) REFERENCES shipments(shipment_id)
);

CREATE TABLE IF NOT EXISTS fraud_alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id VARCHAR(50),
    risk_level VARCHAR(50) NOT NULL, -- 'SAFE', 'LOW RISK', 'MEDIUM RISK', 'HIGH RISK', 'CRITICAL FRAUD'
    risk_score FLOAT NOT NULL,
    reasoning TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Open', -- 'Open', 'Investigating', 'Resolved', 'Dismissed'
    assigned_to VARCHAR(100) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(shipment_id) REFERENCES shipments(shipment_id)
);

CREATE TABLE IF NOT EXISTS risk_scores (
    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id VARCHAR(50) UNIQUE,
    aggregate_score FLOAT NOT NULL,
    risk_level VARCHAR(50) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(shipment_id) REFERENCES shipments(shipment_id)
);

CREATE TABLE IF NOT EXISTS agent_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id VARCHAR(50),
    agent_name VARCHAR(100) NOT NULL,
    thoughts TEXT NOT NULL,
    score_contribution FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(shipment_id) REFERENCES shipments(shipment_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) NOT NULL,
    action TEXT NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
