import streamlit as st
import pandas as pd
from datetime import datetime
import os

# إعدادات الصفحة لتناسب الآيباد
st.set_page_config(page_title="Noir Boutique POS", layout="wide")

# تصميم الثيم (اللون البيج والأسود)
st.markdown("""
    <style>
    .main { background-color: #E5E1D8; }
    .stButton>button { background-color: #1A1A1A; color: white; border-radius: 10px; height: 3em; width: 100%; }
    .summary-card { background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid #1A1A1A; }
    </style>
    """, unsafe_allow_html=True)

# البيانات الأولية من الإكسل
INITIAL_DATA = [
    {"name": "Rose (Standard)", "cost": 8, "sell": 12},
    {"name": "Rose (Ecuador Premium)", "cost": 12, "sell": 18},
    {"name": "Spray Rose", "cost": 10, "sell": 15},
    {"name": "Peony", "cost": 25, "sell": 35},
    {"name": "Hydrangea", "cost": 25, "sell": 35},
    {"name": "Tulip", "cost": 6, "sell": 10},
    {"name": "Lily (Oriental)", "cost": 15, "sell": 25},
    {"name": "Calla Lily", "cost": 15, "sell": 25},
    {"name": "Orchid Stem (Phalaenopsis)", "cost": 30, "sell": 45},
    {"name": "Cymbidium Orchid", "cost": 25, "sell": 35},
    {"name": "Lisianthus", "cost": 10, "sell": 15},
    {"name": "Ranunculus", "cost": 12, "sell": 18},
    {"name": "Anemone", "cost": 12, "sell": 18},
    {"name": "Gerbera", "cost": 5, "sell": 8},
    {"name": "Carnation (Standard)", "cost": 4, "sell": 6},
    {"name": "Spray Carnation", "cost": 5, "sell": 8},
    {"name": "Chrysanthemum", "cost": 6, "sell": 10},
    {"name": "Alstroemeria", "cost": 8, "sell": 12},
    {"name": "Sunflower", "cost": 10, "sell": 15},
    {"name": "Daisy", "cost": 5, "sell": 8},
    {"name": "Baby’s Breath (Gypsophila)", "cost": 10, "sell": 15},
    {"name": "Wax Flower", "cost": 10, "sell": 15},
    {"name": "Eucalyptus", "cost": 8, "sell": 12},
    {"name": "Italian Ruscus", "cost": 10, "sell": 15},
    {"name": "Leather Leaf", "cost": 5, "sell": 8},
    {"name": "Limonium", "cost": 6, "sell": 10},
    {"name": "Solidago", "cost": 6, "sell": 10}
]

# وظائف إدارة البيانات
def load_data():
    if os.path.exists("noir_data.csv"):
        return pd.read_csv("noir_data.csv")
    return pd.DataFrame([
        {"Name": i["name"], "Stock": 0, "Cost": i["cost"], "Sell": i["sell"], "Waste_Qty": 0} 
        for i in INITIAL_DATA
    ])

def save_data(df):
    df.to_csv("noir_data.csv", index=False)

# تحميل البيانات في الـ Session State
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- واجهة المستخدم ---
st.title("🖤 NOIR BOUTIQUE | Dashboard")

# شريط إحصائيات علوي (Cards)
df = st.session_state.df
total_stems = df['Stock'].sum()
total_waste_loss = (df['Waste_Qty'] * df['Cost']).sum()
total_profit = ((df['Sell'] - df['Cost']) * df['Stock']).sum()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<div class='summary-card'><h3>📦 Total Stems</h3><h2>{total_stems}</h2></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='summary-card'><h3>💸 Waste Loss</h3><h2 style='color:red;'>{total_waste_loss:,.2f} AED</h2></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='summary-card'><h3>💰 Est. Profit</h3><h2 style='color:green;'>{total_profit:,.2f} AED</h2></div>", unsafe_allow_html=True)

st.divider()

# منطقة العمليات (Tabs)
tab1, tab2, tab3 = st.tabs(["🛒 Sales & Stock", "🗑️ Waste Management", "📊 Inventory Editor"])

with tab1:
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        item = st.selectbox("Select Flower", df['Name'].unique(), key="sale_item")
    with c2:
        qty = st.number_input("Quantity", min_value=1, value=1, key="sale_qty")
    with c3:
        st.write("##")
        if st.button("Confirm Sale ✅"):
            idx = df[df['Name'] == item].index[0]
            if df.at[idx, 'Stock'] >= qty:
                df.at[idx, 'Stock'] -= qty
                save_data(df)
                st.success("Sale Recorded!")
                st.rerun()
            else:
                st.error("Not enough stock!")
        
        if st.button("Add To Stock ➕"):
            idx = df[df['Name'] == item].index[0]
            df.at[idx, 'Stock'] += qty
            save_data(df)
            st.success("Stock Updated!")
            st.rerun()

with tab2:
    st.subheader("Record Damaged Flowers")
    w_col1, w_col2 = st.columns(2)
    with w_col1:
        w_item = st.selectbox("Damaged Item", df['Name'].unique())
    with w_col2:
        w_qty = st.number_input("Wasted Quantity", min_value=1, value=1)
    
    if st.button("Confirm Waste 🗑️"):
        idx = df[df['Name'] == w_item].index[0]
        if df.at[idx, 'Stock'] >= w_qty:
            df.at[idx, 'Stock'] -= w_qty
            df.at[idx, 'Waste_Qty'] += w_qty
            save_data(df)
            st.warning("Waste Recorded")
            st.rerun()

with tab3:
    st.subheader("Inventory Status")
    # عرض الجدول بشكل تفاعلي
    st.dataframe(df, use_container_width=True)
    
    if st.button("Export Report 📄"):
        df.to_csv(f"Report_{datetime.now().strftime('%Y-%m-%d')}.csv")
        st.info("Report Saved to Server")
