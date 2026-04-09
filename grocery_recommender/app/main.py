import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.recommender import GroceryRecommender

st.set_page_config(page_title='Smart Grocery Assistant', page_icon='🛒', layout='wide')

st.markdown('''
<div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); border-radius: 10px; margin-bottom: 2rem;'>
    <h1 style='color: white;'>🛒 Smart Grocery Assistant</h1>
    <p style='color: white;'>ML-Powered Recommendations for International Students in the DMV Area</p>
    <p style='color: #a8c8ff;'>📍 Washington DC | Maryland | Virginia</p>
</div>
''', unsafe_allow_html=True)


@st.cache_resource
def load_recommender():
    return GroceryRecommender()


recommender = load_recommender()
stats = recommender.get_stats()

with st.sidebar:
    st.header('🎯 Your Preferences')
    diet_type = st.selectbox('Select Your Diet',
                             ['Balanced', 'Vegetarian', 'Vegan', 'High Protein', 'Low Carb', 'Keto'])
    num_items = st.slider('Number of Items', 5, 30, 15)
    st.markdown('---')
    st.metric('Total Items', stats['total_items'])
    st.metric('Vegetarian', stats['vegetarian'])
    st.metric('Vegan', stats['vegan'])
    st.metric('ML Model', stats['model_used'])

if st.button('🎯 Get Recommendations', type='primary', use_container_width=True):
    with st.spinner('Generating recommendations...'):
        recommendations, reason = recommender.recommend_for_diet(diet_type, num_items)

    st.success(f'💡 {reason}')
    df_recs = pd.DataFrame(recommendations)

    for category in df_recs['category'].unique():
        st.subheader(f'📦 {category}')
        category_items = df_recs[df_recs['category'] == category]
        cols = st.columns(3)
        for idx, (_, item) in enumerate(category_items.iterrows()):
            with cols[idx % 3]:
                st.markdown(f'''
                <div style='background: #f8f9fa; padding: 0.8rem; border-radius: 8px; margin: 0.3rem 0;'>
                    <strong>{item['description'][:50]}</strong><br>
                    <small>🔥 {item['calories']:.0f} cal | 💪 {item['protein']:.1f}g protein</small>
                </div>
                ''', unsafe_allow_html=True)

    csv = df_recs.to_csv(index=False)
    st.download_button('📥 Download Shopping List', csv, f'{diet_type}_grocery_list.csv', 'text/csv')
else:
    st.info('👈 Select your diet in the sidebar and click Get Recommendations')