import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
import warnings

warnings.filterwarnings('ignore')

# Ensure models directory exists
models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(models_dir, exist_ok=True)

class LogisticsFraudMLPipeline:
    """
    ML training and evaluation pipeline.
    Loads synthetic datasets, engineers features, trains 5 models,
    evaluates them, selects the best model, and saves it.
    """
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.models_dir = models_dir
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_cols = []
        
    def load_data(self):
        """Loads shipments, vendors, and communications CSVs."""
        shipments_path = os.path.join(self.data_dir, "synthetic_shipments.csv")
        vendors_path = os.path.join(self.data_dir, "synthetic_vendors.csv")
        comms_path = os.path.join(self.data_dir, "synthetic_communications.csv")
        
        if not (os.path.exists(shipments_path) and os.path.exists(vendors_path) and os.path.exists(comms_path)):
            raise FileNotFoundError("Synthetic datasets not found. Run mock_data_generator first.")
            
        shipments = pd.read_csv(shipments_path)
        vendors = pd.read_csv(vendors_path)
        comms = pd.read_csv(comms_path)
        
        return shipments, vendors, comms

    def engineer_features(self, shipments, vendors, comms):
        """Merges datasets and engineers predictive features for model training."""
        # 1. Merge shipments with vendor scores
        df = pd.merge(shipments, vendors, on="vendor_id", how="left")
        
        # Fill missing vendor scores with defaults
        df["trust_score"] = df["trust_score"].fillna(100.0)
        df["incidents_count"] = df["incidents_count"].fillna(0)
        df["sla_compliance_rate"] = df["sla_compliance_rate"].fillna(100.0)
        
        # 2. Aggregate communication metrics per shipment
        # Count fraudulent messages and find maximum fraud probability
        comm_features = comms.groupby("shipment_id").agg(
            comm_fraud_flags=("is_fraudulent", "sum"),
            comm_max_prob=("fraud_probability", "max"),
            comm_count=("message_type", "count")
        ).reset_index()
        
        # Merge with main dataframe
        df = pd.merge(df, comm_features, on="shipment_id", how="left")
        
        # Fill missing comm metrics (for shipments with no communication logs)
        df["comm_fraud_flags"] = df["comm_fraud_flags"].fillna(0)
        df["comm_max_prob"] = df["comm_max_prob"].fillna(0.0)
        df["comm_count"] = df["comm_count"].fillna(0)
        
        # 3. Create domain-specific cargo features
        # Ratio of Cost to Weight (High ratio = high value density, attractive for cargo theft)
        df["cost_weight_ratio"] = df["cost_usd"] / (df["weight_kg"] + 1e-5)
        
        # High Risk Route Flag (Hotspots like LA, Miami, Houston, Atlanta, Newark etc.)
        high_risk_cities = ["Los Angeles, CA", "Miami, FL", "Houston, TX", "Atlanta, GA", "New York, NY"]
        df["is_high_risk_origin"] = df["origin"].apply(lambda x: 1 if x in high_risk_cities else 0)
        df["is_high_risk_dest"] = df["destination"].apply(lambda x: 1 if x in high_risk_cities else 0)
        
        # Date & time features
        df["scheduled_departure"] = pd.to_datetime(df["scheduled_departure"])
        df["departure_hour"] = df["scheduled_departure"].dt.hour
        # Late-night pick up flag (10 PM to 4 AM is high risk for cargo theft)
        df["is_night_departure"] = df["departure_hour"].apply(lambda x: 1 if x >= 22 or x <= 4 else 0)
        
        # 4. Handle Categorical Encoding
        categorical_cols = ["origin", "destination", "route_details"]
        for col in categorical_cols:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            self.label_encoders[col] = le
            
        # 5. Define Feature Set
        self.feature_cols = [
            "weight_kg", "cost_usd", "trust_score", "incidents_count", 
            "sla_compliance_rate", "comm_fraud_flags", "comm_max_prob", 
            "comm_count", "cost_weight_ratio", "is_high_risk_origin", 
            "is_high_risk_dest", "departure_hour", "is_night_departure",
            "origin", "destination", "route_details"
        ]
        
        X = df[self.feature_cols]
        y = df["is_fraud"]
        
        return X, y

    def train_and_evaluate(self, X_train, X_test, y_train, y_test):
        """Trains and compares 5 ML classifiers, returning performance results."""
        # Scale numeric features
        cols_to_scale = ["weight_kg", "cost_usd", "trust_score", "incidents_count", 
                         "sla_compliance_rate", "comm_max_prob", "cost_weight_ratio"]
        
        X_train_scaled = X_train.copy()
        X_test_scaled = X_test.copy()
        
        X_train_scaled[cols_to_scale] = self.scaler.fit_transform(X_train[cols_to_scale])
        X_test_scaled[cols_to_scale] = self.scaler.transform(X_test[cols_to_scale])
        
        models = {
            "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
            "XGBoost": XGBClassifier(n_estimators=100, learning_rate=0.05, random_state=42, eval_metric='logloss'),
            "LightGBM": LGBMClassifier(n_estimators=100, learning_rate=0.05, random_state=42, verbose=-1),
            "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
            "SVM": SVC(probability=True, random_state=42)
        }
        
        results = {}
        trained_models = {}
        
        print("\n" + "="*70)
        print(f"{'Algorithm':<25} | {'Accuracy':<8} | {'Precision':<9} | {'Recall':<6} | {'F1 Score':<8} | {'ROC-AUC':<7}")
        print("="*70)
        
        for name, clf in models.items():
            # Train model
            clf.fit(X_train_scaled, y_train)
            
            # Predict
            y_pred = clf.predict(X_test_scaled)
            y_prob = clf.predict_proba(X_test_scaled)[:, 1]
            
            # Metrics
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, zero_division=0)
            rec = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            auc = roc_auc_score(y_test, y_prob)
            
            results[name] = {
                "Accuracy": acc,
                "Precision": prec,
                "Recall": rec,
                "F1 Score": f1,
                "ROC-AUC": auc
            }
            trained_models[name] = clf
            
            print(f"{name:<25} | {acc:.4f}   | {prec:.4f}    | {rec:.4f} | {f1:.4f}   | {auc:.4f}")
            
        print("="*70)
        
        # Pick best model based on F1 Score (standard for fraud detection due to imbalance)
        best_model_name = max(results, key=lambda k: results[k]["F1 Score"])
        print(f"\nBest Model Selected: {best_model_name} (F1 Score: {results[best_model_name]['F1 Score']:.4f})")
        
        return trained_models[best_model_name], best_model_name, results

    def run_pipeline(self):
        """Runs the entire training, evaluation, and saving pipeline."""
        shipments, vendors, comms = self.load_data()
        X, y = self.engineer_features(shipments, vendors, comms)
        
        # Train-Test Split (80% / 20%)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        best_model, best_name, metrics = self.train_and_evaluate(X_train, X_test, y_train, y_test)
        
        # Save Artifacts
        pipeline_artifacts = {
            "model": best_model,
            "model_name": best_name,
            "scaler": self.scaler,
            "label_encoders": self.label_encoders,
            "feature_cols": self.feature_cols,
            "metrics": metrics[best_name]
        }
        
        save_path = os.path.join(self.models_dir, "best_model.pkl")
        joblib.dump(pipeline_artifacts, save_path)
        print(f"Serialized best model pipeline components to {save_path}")
        
        return metrics

if __name__ == "__main__":
    pipeline = LogisticsFraudMLPipeline()
    pipeline.run_pipeline()
