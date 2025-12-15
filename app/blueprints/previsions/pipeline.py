# Minimal ML pipeline skeleton
import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'models_ml', 'model_final.joblib')

def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None

def predict(model, X):
    # X expected as a pandas DataFrame or 2D array
    return model.predict(X)
