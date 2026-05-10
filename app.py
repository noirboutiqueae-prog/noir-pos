import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import google.generativeai as genai  # عدنا للطريقة المستقرة لضمان عمل البرنامج فوراً

# --- 1. إعدادات الصفحة والثيم (Noir Boutique Style) ---
st.set_page_config(page_title="Noir Boutique POS", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #E5E1D8; }
    [data-testid="stMetric"] { background-color: #ffffff; padding: 20px; border-radius: 15px; border-left: 5px solid #1A1A1A; }
    .stButton>button { background-color: #1A1A1A; color: white; border-radius: 10px; height: 3em; width: 100%; font-weight: bold; }
    h1, h2, h3 { color: #1A1A1A; text-align: center; font-family: 'serif'; }
    @media print {
        .stButton, .stTabs, [data-testid="stSidebar"], .stHeader { display: none !important; }
        .print-only { display: block !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الاتصال والبيانات ---
def get_spreadsheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open("NOIR_POS_DATA")
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

# إعداد الذكاء الاصطناعي
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    ai_model = genai.GenerativeModel('gemini-pro')
except:
    pass

def load_data():
    doc = get_spreadsheet()
    if doc:
        sheet = doc.sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        # التأكد من أسماء الأعمدة لتجنب الـ KeyError
        if 'Waste_Qty' not in df.columns and 'Waste' in df.columns:
            df.rename(columns={'Waste': 'Waste_Qty'}, inplace=True)
        return df
    return pd.DataFrame()

def save_to_gs(df):
    doc = get_spreadsheet()
    if doc:
        sheet = doc.sheet1
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())

def log_transaction(item_name, qty, unit_price, total_price):
    doc = get_spreadsheet()
    if doc:
        try:
            log_sheet = doc.worksheet("SALES_LOG")
            uae_time = datetime.utcnow() + timedelta(hours=4)
            date_str = uae_time.strftime("%Y-%m-%d %H:%M:%S")
            log_sheet.append_row([date_str, item_name, qty, unit_price, total_price])
        except: pass

# --- 3. تشغيل الواجهة ---
if 'df' not in st.session_state:
    st.session_state.df = load_data()

df = st.session_state.df
st.write("<h1>🖤 NOIR BOUTIQUE</h1>", unsafe_allow_html=True)

if not df.empty:
    # حساب الإحصائيات مع التأكد من نوع البيانات
    df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce').fillna(0)
    df['Sell'] = pd.to_numeric(df['Sell'], errors='coerce').fillna(0)
    df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0)
    df['Sold_Today'] = pd.to_numeric(df['Sold_Today'], errors='coerce').fillna(0)
    df['Waste_Qty'] = pd.to_numeric(df.get('Waste_Qty', 0), errors='coerce').fillna(0)

    waste_loss = (df['Waste_Qty'] * df['Cost']).sum()
    daily_profit = (df['Sold_Today'] * (df['Sell'] - df['Cost'])).sum()
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("📦 Total Stems", int(df['Stock'].sum()))
    with col2: st.metric("💸 Waste Loss", f"{waste_loss:,.2f} AED")
    with col3: st.metric("💰 Today's Profit", f"{daily_profit:,.2f} AED")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["🛒 Sales", "🗑️ Waste", "📊 Inventory", "🤖 AI Advisor"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1: item = st.selectbox("Select Flower", df['Name'].unique())
        with c2: qty = st.number_input("Quantity", min_value=1, step=1)
        
        if st.button("Confirm Sale ✅"):
            idx = df[df['Name'] == item].index[0]
            if df.at[idx, 'Stock'] >= qty:
                u_price = float(df.at[idx, 'Sell'])
                df.at[idx, 'Stock'] -= qty
                df.at[idx, 'Sold_Today'] += qty
                save_to_gs(df)
                log_transaction(item, qty, u_price, u_price * qty)
                st.success("Sale Recorded!")
                st.rerun()
            else: st.error("Out of stock!")

    with tab2:
        w_item = st.selectbox("Damaged Item", df['Name'].unique(), key="w")
        w_qty = st.number_input("Qty", min_value=1, key="wq")
        if st.button("Confirm Waste 🗑️"):
            idx = df[df['Name'] == w_item].index[0]
            if df.at[idx, 'Stock'] >= w_qty:
                df.at[idx, 'Stock'] -= w_qty
                df.at[idx, 'Waste_Qty'] += w_qty
                save_to_gs(df)
                st.rerun()

    with tab3:
        st.dataframe(df, width='stretch')
        if st.button("🖨️ Print Daily Report"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    with tab4:
        st.subheader("🤖 AI Smart Advisor")
        user_input = st.text_area("How can I help you?", placeholder="Tap mic to speak...")
        if st.button("✨ Ask AI"):
            if user_input:
                inventory_context = df[['Name', 'Stock', 'Sold_Today']].to_string()
                response = ai_model.generate_content(f"Context: {inventory_context}. User: {user_input}")
                st.write(response.text)
