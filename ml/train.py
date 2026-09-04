import os
import sys
import pickle
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# Ensure root path is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import DatabaseManager
from ml.preprocess import build_training_data, get_feature_names

def train_models(db=None, save_path=None):
    print("Loading data from DB...")
    if db is None:
        db_file = 'admission_predictor.db'
        if not os.path.exists(db_file) and os.path.exists('../admission_predictor.db'):
            db_file = '../admission_predictor.db'
        db = DatabaseManager(db_file)
        db.initialize()
    
    X, y = build_training_data(db)
    print(f"Built training dataset with {len(X)} samples.")
    if len(X) == 0:
        print("No training samples found in database.")
        return None
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    
    models = {
        'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
        'GradientBoosting': GradientBoostingClassifier(random_state=42),
        'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42)
    }
    
    best_model = None
    best_auc = 0
    best_name = ""
    
    print("\nTraining and evaluating models:")
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1]
        
        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, zero_division=0)
        rec = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        auc = roc_auc_score(y_test, probs)
        
        print(f"\n{name}:")
        print(f"Accuracy: {acc:.4f} | Precision: {prec:.4f} | Recall: {rec:.4f} | F1: {f1:.4f} | AUC: {auc:.4f}")
        
        if auc > best_auc or best_model is None:
            best_auc = auc
            best_model = model
            best_name = name
            
    print(f"\nBest Model: {best_name} (AUC: {best_auc:.4f})")
    
    # Calibrate best model
    print("Calibrating best model...")
    calibrated = CalibratedClassifierCV(best_model, cv='prefit')
    calibrated.fit(X_test, y_test)
    
    metadata = {
        'model_name': best_name,
        'features': get_feature_names(),
        'thresholds': {'safe': 75, 'moderate': 40, 'dream': 15},
        'training_date': datetime.now().isoformat(),
        'metrics': {
            'auc': best_auc
        }
    }
    
    if save_path is None:
        save_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
        
    os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
    with open(save_path, 'wb') as f:
        pickle.dump({'model': calibrated, 'metadata': metadata}, f)
        
    print(f"Model and metadata saved to {save_path}")
    return {'model': calibrated, 'metadata': metadata}

if __name__ == '__main__':
    train_models()

