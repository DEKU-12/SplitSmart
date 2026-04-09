import pandas as pd
import joblib

class GroceryRecommender:
    def __init__(self):
        self.df = pd.read_csv('data/processed/grocery_items.csv')
        try:
            self.model = joblib.load('ml/saved_models/random_forest.pkl')
            self.model_name = 'Random Forest'
        except:
            self.model = None
            self.model_name = 'Rule-based'
        print(f'Loaded {len(self.df)} items | Model: {self.model_name}')
    
    def recommend_for_diet(self, diet_type, top_n=20):
        if diet_type == 'Vegetarian':
            filtered = self.df[self.df['is_vegetarian'] == True]
            reason = 'Vegetarian items'
        elif diet_type == 'Vegan':
            filtered = self.df[self.df['is_vegan'] == True]
            reason = 'Vegan items'
        elif diet_type == 'High Protein':
            filtered = self.df[self.df['protein'] > 15]
            reason = 'High protein items'
        else:
            filtered = self.df
            reason = 'Balanced items'
        filtered = filtered.head(top_n)
        return filtered[['description', 'category', 'calories', 'protein', 'fat', 'carbs']].to_dict('records'), reason
    
    def get_stats(self):
        return {
            'total_items': len(self.df),
            'categories': self.df['category'].nunique(),
            'vegetarian': self.df['is_vegetarian'].sum(),
            'vegan': self.df['is_vegan'].sum(),
            'model_used': self.model_name
        }
