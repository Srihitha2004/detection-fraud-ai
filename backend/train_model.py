import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Ensure models directory exists
models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(models_dir, exist_ok=True)

class ModelTrainer:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.models_dir = models_dir
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words='english')

    def load_data(self):
        """Loads fraud_messages.csv which contains spam/fraud and ham/safe texts."""
        messages_path = os.path.join(self.data_dir, "fraud_messages.csv")
        
        if not os.path.exists(messages_path):
            raise FileNotFoundError(f"Fraud messages dataset not found at {messages_path}. Run generate_datasets.py first.")
            
        print("Loading fraud messages dataset...")
        df = pd.read_csv(messages_path)
        
        df_clean = pd.DataFrame({
            "message": df["text"].astype(str),
            "label": df["label"].apply(lambda x: 1 if x == "spam" else 0)
        })
        
        # Drop duplicates or empty entries
        df_clean = df_clean.dropna().drop_duplicates()
        
        print(f"Total unique training samples: {len(df_clean)}")
        print(f"Fraud samples: {df_clean['label'].sum()} ({df_clean['label'].mean()*100:.1f}%)")
        
        return df_clean

    def train(self):
        df = self.load_data()
        
        X = df["message"]
        y = df["label"]
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # TF-IDF fit transform
        print("Fitting TF-IDF Vectorizer...")
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # Define classifiers (Logistic Regression and Linear SVM)
        models = {
            "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
            "Linear SVM": LinearSVC(random_state=42, dual=False)
        }
        
        results = {}
        trained_models = {}
        
        print("\n" + "="*70)
        print(f"{'Classifier Model':<25} | {'Accuracy':<8} | {'Precision':<9} | {'Recall':<6} | {'F1 Score':<8}")
        print("="*70)
        
        for name, clf in models.items():
            # Train
            clf.fit(X_train_vec, y_train)
            
            # Predict
            y_pred = clf.predict(X_test_vec)
            
            # Metrics
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, zero_division=0)
            rec = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            results[name] = f1
            trained_models[name] = {
                "model": clf,
                "metrics": {
                    "accuracy": acc,
                    "precision": prec,
                    "recall": rec,
                    "f1": f1
                }
            }
            
            print(f"{name:<25} | {acc:.4f}   | {prec:.4f}    | {rec:.4f} | {f1:.4f}")
            
        print("="*70)
        
        # Select best model based on F1 Score
        best_model_name = max(results, key=results.get)
        best_data = trained_models[best_model_name]
        print(f"\nAutomatically selected Best Model: {best_model_name} (F1 Score: {results[best_model_name]:.4f})")
        
        # Save pipeline artifacts
        save_path = os.path.join(self.models_dir, "best_model.pkl")
        joblib.dump({
            "model": best_data["model"],
            "model_name": best_model_name,
            "vectorizer": self.vectorizer,
            "metrics": best_data["metrics"]
        }, save_path)
        print(f"Saved best model artifacts to {save_path}")

if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train()
