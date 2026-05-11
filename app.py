import streamlit as st
import pandas as pd
import gspread

# 1. POS Setup
st.set_page_config(page_title="NOIR POS TERMINAL", layout="centered")

# 2. Connection using the new JSON secrets
def connect_to_sheet():
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

sheet = connect_to_sheet()

# 3. Header
st.markdown("<h1 style='text-align: center; color: white;'>🖤 NOIR POS TERMINAL</h1>", unsafe_allow_html=True)
st.divider()

if sheet:
    # Fetch Data
    df = pd.DataFrame(sheet.get_all_records())

    # 4. Transaction Form
    st.subheader("🛒 New Transaction")
    with st.form("sale_form"):
        item_name = st.selectbox("Select Product", df['Name'].tolist())
        qty = st.number_input("Quantity Sold", min_value=1, step=1)
        submit = st.form_submit_button("Complete Sale ✅")

        if submit:
            # Find the exact row in Google Sheets
            cell = sheet.find(item_name)
            row = cell.row
            
            # Fetch current stock (Col 2) and current sales (Col 5)
            current_stock = int(sheet.cell(row, 2).value)
            current_sold = int(sheet.cell(row, 5).value or 0)
            
            if current_stock >= qty:
                # Deduct Stock and Add to Sales
                sheet.update_cell(row, 2, current_stock - qty)
                sheet.update_cell(row, 5, current_sold + qty)
                
                st.balloons()
                st.success(f"Transaction Complete! {qty} x {item_name} sold.")
                st.cache_data.clear()
            else:
                st.error(f"Insufficient Stock! Only {current_stock} remaining.")

    # 5. Live View
    st.divider()
    st.subheader("📊 Live Inventory Status")
    st.dataframe(df, use_container_width=True, hide_index=True)
