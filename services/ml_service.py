# services/ml_service.py

import pandas as pd
import joblib

class MLService:
    """
    Service responsible for making predictions using a pre-trained ML model.
    This is the production version.
    """
    def __init__(self, model_path: str):
        try:
            self.model = joblib.load(model_path)
            if hasattr(self.model, 'feature_names_in_'):
                self.feature_names = self.model.feature_names_in_
                self.feature_names = self.model.get_booster().feature_names
            print(f"MLService: Model loaded successfully from {model_path}.")
        except FileNotFoundError:
            print(f"MLService: FATAL ERROR - Model file not found at {model_path}.")
            self.model = None
        except Exception as e:
            print(f"MLService: An error occurred while loading the model: {e}")
            self.model = None


    def get_prediction(self, df: pd.DataFrame) -> int:
        if self.model is None or df is None or df.empty:
            print("MLService: Model not loaded or DataFrame is empty. Returning HOLD.")
            return 0

        CONFIDENCE_THRESHOLD = 0.40  

        latest_data = df.iloc[-1:]
        features_for_model = latest_data[self.feature_names]
        
        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(features_for_model)[0]
        else:
            probabilities = self.model.predict(features_for_model)[0]
        max_probability = probabilities.max()
        predicted_class_mapped = probabilities.argmax()

        if max_probability < CONFIDENCE_THRESHOLD:
            print(f"MLService: Model prediction ({max_probability:.2f}) is below confidence threshold. Forcing HOLD.")
            return 0
        else:
            if predicted_class_mapped == 1:
                prediction = 1 # BUY
            elif predicted_class_mapped == 2:
                prediction = -1 # SELL
            else:
                prediction = 0 # HOLD
            
            print(f"MLService: Real prediction generated: {prediction} with confidence {max_probability:.2f}")
            return prediction