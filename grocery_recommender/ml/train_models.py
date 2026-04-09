import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

class ModelTrainer:
    def __init__(self):
        self.models = {}
        self.results = {}
    
    def train_all_models(self, df):
        print('Training Random Forest model...')
        X = df[['calories', 'protein', 'fat', 'carbs']].fillna(0)
        y = df['is_vegetarian'].fillna(0).astype(int)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        model = RandomForestClassifier()
        model.fit(X_train, y_train)
        acc = model.score(X_test, y_test)
        print(f'Accuracy: {acc:.2%}')
        joblib.dump(model, 'ml/saved_models/random_forest.pkl')
        return {'Random Forest': {'accuracy': acc}}, {'Random Forest': model}
