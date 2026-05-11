import streamlit as st
import pandas as pd
import gspread

# 1. POS Terminal Configuration
st.set_page_config(page_title="NOIR POS", layout="centered")

def get_connection():
    try:
        # Fetching secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # التنظيف الذاتي للمفتاح لمنع خطأ الـ 65 حرفاً
        clean_key = creds_dict["private_key"].replace("\\n", "\n").strip()
        creds_dict["private_key"] = clean_key
        
        gc = gspread.service_account_from_dict(creds_dict)
        # Using your Sheet ID
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

sheet = get_connection()

st.title("🖤 NOIR POS TERMINAL")

if sheet:
    # Refresh logic
    if st.button("Refresh Inventory 🔄"):
        st.cache_data.clear()

    # Load data
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # POS Sale Form
    st.subheader("🛒 New Transaction")
    with st.form("pos_sale", clear_on_submit=True):
        product = st.selectbox("Select Item", df['Name'].tolist())
        amount = st.number_input("Quantity", min_value=1, step=1)
        confirm = st.form_submit_button("Complete Sale ✅")

        if confirm:
            cell = sheet.find(product)
            row = cell.row
            
            # Stock is Col 2, Sold_Today is Col 5
            curr_stock = int(sheet.cell(row, 2).value)
            curr_sold = int(sheet.cell(row, 5).value or 0)
            
            if curr_stock >= amount:
                # Update Inventory
                sheet.update_cell(row, 2, curr_stock - amount)
                sheet.update_cell(row, 5, curr_sold + amount)
                st.balloons()
                st.success(f"Sold {amount} of {product}!")
                st.cache_data.clear()
            else:
                st.error("Insufficient Stock!")

    st.divider()
    st.subheader("📊 Inventory Overview")
    st.dataframe(df, use_container_width=True, hide_index=True)
