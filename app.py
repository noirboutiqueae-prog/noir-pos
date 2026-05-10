import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px

# 1. Page Configuration & AI Setup
st.set_page_config(page_title="NOIR BOUTIQUE PRO", layout="wide")

# AI Setup (Make sure GEMINI_API_KEY is in your Secrets)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
except:
    st.warning("⚠️ Note: AI System requires GEMINI_API_KEY to function.")

# 2. Data Fetching
SHEET_ID = "1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

def load_data():
    df = pd.read_csv(SHEET_URL)
    df = df.dropna(how='all')
    # Convert columns to numeric for calculations
    for col in df.columns[1:]: 
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df = load_data()

# 3. UI Header
st.markdown("<h1 style='text-align: center; color: #BB86FC;'>🖤 NOIR BOUTIQUE POS PRO</h1>", unsafe_allow_html=True)
st.divider()

# 4. Sidebar Navigation
with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/ffffff/luxury.png") 
    st.title("Control Panel")
    page = st.radio("Navigate to:", ["📊 Sales & Inventory", "🤖 NOIR AI Assistant", "📈 Performance Analysis"])
    
    if st.button('Refresh Data 🔄'):
        st.cache_data.clear()
        st.rerun()

# --- Page 1: Sales & Inventory ---
if page == "📊 Sales & Inventory":
    # Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Models", len(df))
    with c2:
        total_sales = df.iloc[:, 4].sum() # Price column (E)
        st.metric("Total Revenue", f"{total_sales:,.0f} AED")
    with c3:
        total_stock = df.iloc[:, 1].sum() # Stock column (B)
        st.metric("Available Stock", int(total_stock))
    with c4:
        low_stock = len(df[df.iloc[:, 1] < 5])
        st.metric("Low Stock Items", low_stock, delta_color="inverse")

    # Search and Table
    search = st.text_input("🔍 Search for a model or item...")
    if search:
        filtered_df = df[df.iloc[:, 0].astype(str).str.contains(search, case=False, na=False)]
    else:
        filtered_df = df

    st.subheader("📦 Current Inventory Status")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# --- Page 2: NOIR AI Assistant ---
elif page == "🤖 NOIR AI Assistant":
    st.subheader("💬 Chat with NOIR Intelligence")
    user_q = st.text_input("Ask me anything (e.g., How can I improve sales this month?)")
    if user_q:
        with st.spinner('Analyzing data...'):
            try:
                prompt = f"You are an expert business consultant for a high-end fashion boutique named NOIR. Here is the current inventory/sales data: {df.to_string()}. Answer this question professionally: {user_q}"
                response = model.generate_content(prompt)
                st.info(response.text)
            except:
                st.error("AI Error: Please verify your GEMINI_API_KEY in Secrets.")

# --- Page 3: Performance Analysis ---
elif page == "📈 Performance Analysis":
    st.subheader("📈 Product Pricing Analysis")
    fig = px.bar(df, x=df.columns[0], y=df.columns[4], 
                 title="Price Comparison per Model",
                 labels={'x': 'Product Name', 'y': 'Price (AED)'},
                 color=df.columns[4], color_continuous_scale='Purples')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📉 Inventory Distribution")
    fig2 = px.pie(df, values=df.columns[1], names=df.columns[0], title="Stock Level Distribution")
    st.plotly_chart(fig2, use_container_width=True)
