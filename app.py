import streamlit as st
import pandas as pd
import gspread

# 1. POS Terminal Setup
st.set_page_config(page_title="NOIR POS TERMINAL", layout="centered")

# 2. Connection to Google Sheets
def connect_sheet():
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

sheet = connect_sheet()

# 3. Design & Header
st.markdown("<h1 style='text-align: center;'>🖤 NOIR POS TERMINAL</h1>", unsafe_allow_html=True)
st.divider()

if sheet:
    # Refresh data button
    if st.button("Refresh Inventory 🔄"):
        st.cache_data.clear()

    # Get data and columns
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # 4. Sale Transaction Form
    st.subheader("🛒 New Sale")
    with st.form("transaction_form", clear_on_submit=True):
        product = st.selectbox("Select Item", df['Name'].tolist())
        quantity = st.number_input("Quantity Sold", min_value=1, step=1)
        submit_sale = st.form_submit_button("Confirm Transaction ✅")

        if submit_sale:
            cell = sheet.find(product)
            row_idx = cell.row
            
            # Col 2 is 'Stock', Col 5 is 'Sold_Today'
            current_stock = int(sheet.cell(row_idx, 2).value)
            current_sold = int(sheet.cell(row_idx, 5).value or 0)
            
            if current_stock >= quantity:
                # Deduction Logic
                sheet.update_cell(row_idx, 2, current_stock - quantity)
                sheet.update_cell(row_idx, 5, current_sold + quantity)
                st.balloons()
                st.success(f"Sale successful! Deducted {quantity} from {product} stock.")
                st.cache_data.clear()
            else:
                st.error(f"Not enough stock! Current inventory: {current_stock}")

    # 5. Live Inventory Display
    st.divider()
    st.subheader("📊 Live Inventory Status")
    st.dataframe(df, use_container_width=True, hide_index=True)
