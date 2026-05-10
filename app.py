import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import google.generativeai as genai

# --- 1. إعدادات الصفحة والثيم (الأسود والبيج) ---
st.set_page_config(page_title="Noir Boutique POS", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #E5E1D8; }
    [data-testid="stMetric"] { background-color: #ffffff; padding: 20px; border-radius: 15px; border-left: 5px solid #1A1A1A; }
    .stButton>button { background-color: #1A1A1A; color: white; border-radius: 10px; height: 3em; width: 100%; font-weight: bold; }
    h1, h2, h3 { color: #1A1A1A; text-align: center; font-family: 'serif'; }
    
    /* تنسيق خاص للطباعة */
    @media print {
        .stButton, .stTabs, [data-testid="stSidebar"], .stMarkdown:not(.print-only) {
            display: none !important;
        }
        .print-only {
            display: block !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الاتصال بقوقل شيت والذكاء الاصطناعي ---
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

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    ai_model = genai.GenerativeModel('gemini-pro')
except:
    pass

def load_data():
    doc = get_spreadsheet()
    if doc:
        sheet = doc.sheet1
        return pd.DataFrame(sheet.get_all_records())
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

# --- 3. تشغيل التطبيق ---
if 'df' not in st.session_state:
    st.session_state.df = load_data()

df = st.session_state.df
st.write("<h1>🖤 NOIR BOUTIQUE</h1>", unsafe_allow_html=True)

if not df.empty:
    # حساب الإحصائيات
    waste_loss = (df['Waste'].astype(float) * df['Cost'].astype(float)).sum()
    daily_profit = (df['Sold_Today'].astype(float) * (df['Sell'].astype(float) - df['Cost'].astype(float))).sum()
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("📦 Total Stems", int(df['Stock'].sum()))
    with col2: st.metric("🗑️ Waste Loss", f"{waste_loss:,.2f} AED")
    with col3: st.metric("💰 Today's Profit", f"{daily_profit:,.2f} AED")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["🛒 Sales & Stock", "🗑️ Waste", "📊 Inventory & Printing", "🤖 AI Advisor"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1: item = st.selectbox("Select Flower", df['Name'].unique())
        with c2: qty = st.number_input("Quantity", min_value=1, step=1)
        
        cb1, cb2 = st.columns(2)
        with cb1:
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
        with cb2:
            if st.button("Add To Stock ➕"):
                idx = df[df['Name'] == item].index[0]
                df.at[idx, 'Stock'] += qty
                save_to_gs(df)
                st.success("Stock Updated!")
                st.rerun()

    with tab2:
        w_item = st.selectbox("Damaged Item", df['Name'].unique(), key="w")
        w_qty = st.number_input("Wasted Qty", min_value=1, key="wq")
        if st.button("Confirm Waste 🗑️"):
            idx = df[df['Name'] == w_item].index[0]
            if df.at[idx, 'Stock'] >= w_qty:
                df.at[idx, 'Stock'] -= w_qty
                df.at[idx, 'Waste'] += w_qty
                save_to_gs(df)
                st.rerun()

    with tab3:
        st.subheader("Current Inventory Status")
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.write("### 🖨️ Reporting")
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            # زر الطباعة الفوري (يستخدم جافا سكريبت لفتح نافذة طباعة المتصفح)
            if st.button("🖨️ Print Daily Report"):
                st.markdown("""
                    <script>
                        window.print();
                    </script>
                """, unsafe_allow_html=True)
                
                # شكل التقرير الذي سيظهر عند الطباعة فقط
                st.markdown(f"""
                    <div class="print-only" style="display:none; color: black; padding: 30px;">
                        <h1 style="text-align:center;">NOIR BOUTIQUE - DAILY REPORT</h1>
                        <p style="text-align:center;">Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                        <hr>
                        <h3>Summary:</h3>
                        <ul>
                            <li>Total Profit: {daily_profit:,.2f} AED</li>
                            <li>Total Waste Loss: {waste_loss:,.2f} AED</li>
                        </ul>
                        <table border="1" style="width:100%; border-collapse: collapse; text-align: left;">
                            <tr style="background-color: #f2f2f2;">
                                <th>Item Name</th><th>Stock Left</th><th>Sold Today</th><th>Waste</th>
                            </tr>
                            {''.join([f"<tr><td>{row['Name']}</td><td>{row['Stock']}</td><td>{row['Sold_Today']}</td><td>{row['Waste']}</td></tr>" for _, row in df.iterrows()])}
                        </table>
                        <br>
                        <p style="text-align:right;">Authorized Signature: __________________</p>
                    </div>
                """, unsafe_allow_html=True)

        with col_p2:
            # خيار تحميل التقرير كـ CSV (لفتحه في إكسل)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Download Excel (CSV)",
                data=csv,
                file_name=f"Noir_Report_{datetime.now().strftime('%Y-%m-%d')}.csv",
                mime='text/csv',
            )

    with tab4:
        st.subheader("🤖 NOIR Luxury Advisor")
        user_input = st.text_area("How can I help you?", placeholder="Ask anything about your boutique...")
        if st.button("✨ Get Expert Advice"):
            if user_input:
                inventory_info = df[['Name', 'Stock', 'Sold_Today']].to_string()
                prompt = f"Context: {inventory_info}\nTask: {user_input}"
                response = ai_model.generate_content(prompt)
                st.write(response.text)
