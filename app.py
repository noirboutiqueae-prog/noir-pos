import streamlit as st
import pandas as pd
import gspread

# 1. POS UI Setup
st.set_page_config(page_title="NOIR POS TERMINAL", layout="centered")

def get_connection():
    try:
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        gc = gspread.service_account_from_dict(info)
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"⚠️ Connection Diagnostic: {e}")
        return None

sheet = get_connection()

st.markdown("<h1 style='text-align: center;'>🖤 NOIR POS TERMINAL</h1>", unsafe_allow_html=True)

if sheet:
    # Refresh logic
    if st.sidebar.button("Refresh Inventory 🔄"):
        st.cache_data.clear()

    # Load and Clean Data
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # تحويل كافة الأعمدة الرقمية إلى أرقام فعلية لضمان عدم حدوث أخطاء Arrow
    cols_to_fix = ['Stock', 'Cost', 'Sell', 'Sold_Today', 'Waste']
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 2. Transaction Form
    st.subheader("🛒 New Transaction")
    with st.form("pos_sale", clear_on_submit=True):
        product = st.selectbox("Select Item", df['Name'].tolist())
        amount = st.number_input("Quantity", min_value=1, step=1)
        confirm = st.form_submit_button("Complete Sale ✅")

        if confirm:
            with st.spinner("Processing..."):
                cell = sheet.find(product)
                row = cell.row
                # Update Column B (Stock) and Column E (Sold_Today)
                current_stock = int(df.loc[df['Name'] == product, 'Stock'].values[0])
                current_sold = int(df.loc[df['Name'] == product, 'Sold_Today'].values[0])
                
                if current_stock >= amount:
                    sheet.update_cell(row, 2, current_stock - amount)
                    sheet.update_cell(row, 5, current_sold + amount)
                    st.balloons()
                    st.success(f"Successfully sold {amount} units of {product}!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Insufficient Stock!")

    # 3. Inventory Table
    st.divider()
    st.subheader("📊 Inventory Overview")
    # عرض الجدول بطريقة تمنع أخطاء التنسيق
    st.dataframe(df, use_container_width=True, hide_index=True)
