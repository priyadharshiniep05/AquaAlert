import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import pickle
import os

class FloodPredictor:
    def __init__(self):
        self.model = None
        self.model_path = 'data/flood_model.pkl'
        self._train_or_load()

    def _generate_training_data(self):
        """Generate realistic mock training data"""
        np.random.seed(42)
        n = 2000
        rainfall = np.random.exponential(20, n)
        humidity = np.random.uniform(40, 100, n)
        soil_sat = np.random.uniform(0, 1, n)
        river_level = np.random.uniform(0, 10, n)
        temp = np.random.uniform(15, 40, n)
        
        # Risk logic: realistic thresholds
        risk = []
        for i in range(n):
            score = (
                (rainfall[i] / 150) * 40 +
                (soil_sat[i]) * 25 +
                (river_level[i] / 10) * 25 +
                (humidity[i] / 100) * 10
            )
            if score > 55:
                risk.append('HIGH')
            elif score > 30:
                risk.append('MEDIUM')
            else:
                risk.append('LOW')
        
        return pd.DataFrame({
            'rainfall_mm': rainfall,
            'humidity': humidity,
            'soil_saturation': soil_sat,
            'river_level': river_level,
            'temperature': temp,
            'risk': risk
        })

    def _train_or_load(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
        else:
            df = self._generate_training_data()
            X = df[['rainfall_mm', 'humidity', 'soil_saturation', 'river_level', 'temperature']]
            y = df['risk']
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X, y)
            os.makedirs('data', exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)

    def predict(self, rainfall_mm, humidity, soil_saturation, river_level, temperature):
        X = np.array([[rainfall_mm, humidity, soil_saturation, river_level, temperature]])
        risk_level = self.model.predict(X)[0]
        proba = self.model.predict_proba(X)[0]
        classes = self.model.classes_
        risk_score = float(proba[list(classes).index(risk_level)]) * 100
        return {
            'risk_level': risk_level,
            'risk_score': round(risk_score, 1),
            'probabilities': {c: round(float(p)*100, 1) for c, p in zip(classes, proba)}
        }
