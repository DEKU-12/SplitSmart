import pandas as pd
from sklearn.preprocessing import StandardScaler

class FeatureEngineer:
    def __init__(self):
        self.scaler = StandardScaler()
    
    def prepare_for_ml(self, df):
        feature_cols = ['calories', 'protein', 'fat', 'carbs']
        X = df[feature_cols].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        return X_scaled, feature_cols
