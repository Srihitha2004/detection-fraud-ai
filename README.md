# Cargo Theft & Communications Fraud Detection System

A lightweight, agent-driven cyber-enabled cargo theft and logistics fraud detection system designed for a Hackathon. The platform analyzes SMS and email communications to flag spoofed identities, courier scams, phishing attacks, and cargo diversion schemes.

---

## 🚀 Key Features

1. **Simple Responsive Dashboard**: Single page application (SPA) styled using Bootstrap 5. Exposes fields for Sender Number, Sender Email, and Message Text. Supports Laptop, Tablet, Desktop, and Mobile.
2. **Hybrid Verification**: Integrates TF-IDF Natural Language Processing (ML) with a comprehensive database-backed keyword intelligence scanner ($792$ terms across 8 fraud categories).
3. **Agentic Decision Engine**: Uses $5$ dedicated lightweight agents:
   * **ML Prediction Agent**: Predicts safe vs spam using a Random Forest model.
   * **Fraud Intelligence Agent**: Matches explicit phishing, logistics, and courier keywords.
   * **Duplicate Detection Agent**: Searches the database for previously analyzed messages, numbers, or emails.
   * **Trusted Domain Agent**: White-lists domains (e.g. `fedex.com`) and manages risk score waivers while permitting overrides for high-risk text (e.g., password requests).
   * **Decision Agent**: Orchestrates and produces final classifications (`SAFE`, `SUSPICIOUS`, `FRAUD`), confidence scores, and recommendations.
4. **Database Tracking**: Stores audit logs in MySQL `message_history` with an automatic SQLite fallback.

---

## 📁 Project Structure

```text
frontend/
 ├── index.html       # Single-page UI
 ├── style.css        # Custom styles for badges, inputs, and alerts
 └── app.js           # AJAX fetch controller with validations

backend/
 ├── app.py           # Flask server serving frontend static assets and prediction routes
 ├── database.py      # Database connector (MySQL + SQLite fallback)
 ├── agents.py        # Coded logic for the 5 agents
 └── train_model.py   # ML pipeline script

data/
 ├── spam_dataset.csv             # Combined spam and phishing text dataset
 ├── fraud_keywords.csv           # OTP and general fraud keywords
 ├── phishing_keywords.csv        # Phishing and identity theft terms
 └── logistics_keywords.csv       # Courier tax and cargo diversion terms

models/
 └── best_model.pkl               # Serialized best trained ML model (Random Forest)

sql/
 └── schema.sql                   # Database setup for message_history and keywords table

requirements.txt                  # Required Python packages
README.md                         # Project documentation
```

---

## 🛠️ Setup and Run Instructions

### 1. Install Dependencies
Run the command below in the terminal to install required Python libraries:
```bash
pip install -r requirements.txt
```

### 2. Generate Datasets and Seed Keywords
Generate datasets and compile the keyword database by executing these commands:
```bash
# Generate CSV datasets
python backend/generate_datasets.py

# Generate keyword lists and seed database
python backend/generate_keywords.py
```

### 3. Train the Classifier
Run the model training pipeline to select the best model (comparing Random Forest, XGBoost, and Logistic Regression):
```bash
python backend/train_model.py
```

### 4. Launch the Web Application
Start the Flask backend server:
```bash
python backend/app.py
```
Open **`http://127.0.0.1:5000/`** in your web browser.
