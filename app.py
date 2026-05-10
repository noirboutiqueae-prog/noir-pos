import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Config
st.set_page_config(page_title="NOIR POS PRO", layout="wide")

# 2. Data Fetching
SHEET_ID = "1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df = df.dropna(how='all')
        # Ensure numeric columns are correct
        numeric_cols = df.columns[1:] 
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

df = load_data()

# 3. Header
st.markdown("<h1 style='text-align: center; color: #BB86FC;'>🖤 NOIR BOUTIQUE - INVENTORY MANAGEMENT</h1>", unsafe_allow_html=True)
st.divider()

# 4. Sidebar with "Quick Action"
with st.sidebar:
    st.title("Settings")
    if st.button('🔄 Refresh Data'):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    st.info("💡 **How to add items?**\nClick the button below to open your Google Sheet, add a new row, then come back and hit Refresh.")
    # زر يفتح لك ملف قوقل شيت مباشرة للإضافة
    st.link_button("➕ Open Sheet to Add Items", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")

if not df.empty:
    # 5. Dashboard Metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Items", len(df))
    with c2:
        st.metric("Total Stock Value", f"{df.iloc[:, 4].sum():,.0f} AED")
    with c3:
        # إذا أضفت عمود النوع (Category) في العمود الثالث (C)
        if len(df.columns) > 2:
            types_count = df.iloc[:, 2].nunique()
            st.metric("Total Categories", types_count)

    st.divider()

    # 6. Advanced Filters
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search = st.text_input("🔍 Search by Model Name")
    with col_filter:
        if len(df.columns) > 2:
            categories = ["All"] + list(df.iloc[:, 2].unique())
            selected_cat = st.selectbox("📁 Filter by Type", categories)

    # Filter Logic
    filtered_df = df.copy()
    if search:
        filtered_df = filtered_df[filtered_df.iloc[:, 0].astype(str).str.contains(search, case=False)]
    if len(df.columns) > 2 and selected_cat != "All":
        filtered_df = filtered_df[filtered_df.iloc[:, 2] == selected_cat]

    # 7. Display Table
    st.subheader("Inventory List")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    # 8. Charts
    if len(df.columns) > 2:
        st.subheader("📈 Stock Distribution by Type")
        fig = px.pie(df, values=df.columns[1], names=df.columns[2], hole=0.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Could not load data. Please check your Google Sheet connection.")
