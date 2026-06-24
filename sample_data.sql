-- Sample Data for Cargo Theft Fraud Detection Platform
-- Compatible with MySQL and SQLite

-- Seed Vendors
INSERT INTO vendors (vendor_id, name, trust_score, incidents_count, sla_compliance_rate, status) VALUES 
('VND-001', 'Apex Logistics Corp', 98.5, 0, 99.2, 'Active'),
('VND-002', 'Global Cargo Logistics', 94.0, 1, 95.8, 'Active'),
('VND-003', 'Summit Freight Services', 82.3, 3, 88.5, 'Active'),
('VND-004', 'NextDay Delivery Inc', 45.0, 8, 71.2, 'Suspended'),
('VND-005', 'Sentinel Transport Solutions', 99.1, 0, 99.8, 'Active'),
('VND-006', 'TransNational Carrier Group', 58.4, 6, 76.5, 'Under_Review'),
('VND-007', 'Titan Heavy Hauling', 91.2, 2, 93.0, 'Active');

-- Seed Users
-- The bcrypt password hash for 'admin123' is '$2b$12$K88f72.K.x7gC4D76V.VfO5.j/86J4VkW3w6Uf4bU7J7eZ9eE7wKq'
INSERT INTO users (username, password_hash, role) VALUES 
('admin', '$2b$12$K88f72.K.x7gC4D76V.VfO5.j/86J4VkW3w6Uf4bU7J7eZ9eE7wKq', 'Admin'),
('dispatcher', '$2b$12$K88f72.K.x7gC4D76V.VfO5.j/86J4VkW3w6Uf4bU7J7eZ9eE7wKq', 'Dispatcher'),
('investigator', '$2b$12$K88f72.K.x7gC4D76V.VfO5.j/86J4VkW3w6Uf4bU7J7eZ9eE7wKq', 'Investigator');

-- Seed Shipments
INSERT INTO shipments (shipment_id, vendor_id, carrier_id, origin, destination, route_details, weight_kg, cost_usd, scheduled_departure, scheduled_arrival, status) VALUES 
('SHP-1001', 'VND-001', 'CAR-982', 'Los Angeles, CA', 'Chicago, IL', 'I-80 E', 15200.0, 45000.00, '2026-06-22 08:00:00', '2026-06-25 18:00:00', 'Pending'),
('SHP-1002', 'VND-002', 'CAR-114', 'Miami, FL', 'New York, NY', 'I-95 N', 18450.0, 62000.00, '2026-06-22 09:30:00', '2026-06-24 14:00:00', 'Pending'),
('SHP-1003', 'VND-004', 'CAR-504', 'Houston, TX', 'Phoenix, AZ', 'I-10 W', 8500.0, 95000.00, '2026-06-23 06:00:00', '2026-06-25 12:00:00', 'Pending'),
('SHP-1004', 'VND-003', 'CAR-098', 'Seattle, WA', 'Denver, CO', 'I-84 E to I-80 E', 12000.0, 31000.00, '2026-06-21 11:00:00', '2026-06-23 17:00:00', 'In_Transit'),
('SHP-1005', 'VND-006', 'CAR-371', 'Atlanta, GA', 'Detroit, MI', 'I-75 N', 1400.0, 115000.00, '2026-06-22 14:00:00', '2026-06-23 20:00:00', 'Pending');

-- Seed Communications
INSERT INTO communications (shipment_id, sender, receiver, message_type, message_content, is_fraudulent, fraud_probability) VALUES 
('SHP-1001', 'apex-dispatchers@apexcorp.com', 'logistics-ops@controlcenter.com', 'Email', 'Hello, this is the dispatch team confirming that driver John Smith (ID CAR-982) has successfully completed the gate check-in at Los Angeles Terminal. Estimated departure remains on schedule.', 0, 0.02),
('SHP-1003', 'urgent-cargo-support@gmail-logistics.com', 'dispatch-desk@controlcenter.com', 'Email', 'URGENT UPDATE: Shipment SHP-1003 has been rerouted due to sudden mechanical issues. Please dispatch to the alternative warehouse at 1224 Industrial Dr, Tolleson, AZ immediately instead of the primary terminal. Confirm receipt ASAP.', 1, 0.94),
('SHP-1003', 'carrier-desk@apexcorp.com', 'broker-ops@controlcenter.com', 'Email', 'Hi, please find attached the updated Bill of Lading (BOL) for shipment SHP-1003. We are running slightly behind due to minor highway construction but everything is secure.', 0, 0.05),
('SHP-1005', '+15550198273', '+15550123984', 'SMS', 'Driver alert. Reroute SHP-1005 now. Delivery at destination Detroit locked out. Go to 844 Outer Dr, Detroit instead. Drop cargo off at loading dock B. Do not contact dispatcher via phone, system is undergoing maintenance.', 1, 0.88),
('SHP-1002', 'global-fleet@globalcargo.com', 'logistics-ops@controlcenter.com', 'Email', 'Good morning, driver credentials and truck inspection logs have been uploaded to the portal for carrier check-in tomorrow. Thank you.', 0, 0.01);
