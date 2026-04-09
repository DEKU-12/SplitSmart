import subprocess
import sys
import pandas as pd
import os


def run_full_pipeline():
    print('=' * 60)
    print('SMART GROCERY ASSISTANT')
    print('=' * 60)

    # Check data
    if not os.path.exists('data/processed/grocery_items.csv'):
        print('❌ Error: grocery_items.csv not found!')
        return

    df = pd.read_csv('data/processed/grocery_items.csv')
    print(f'✅ Loaded {len(df)} grocery items')

    # Train models
    print('\n🤖 Training ML models...')
    from ml.train_models import ModelTrainer
    trainer = ModelTrainer()
    results, models = trainer.train_all_models(df)

    # Launch app
    print('\n🚀 Launching Streamlit app...')
    print('=' * 60)
    subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'app/main.py'])


if __name__ == '__main__':
    run_full_pipeline()