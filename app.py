import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. POS Configuration
st.set_page_config(page_title="NOIR POS SYSTEM", layout="centered")

# 2. Connect to Google Sheets via Service Account
def connect_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # Opening your sheet by ID
    return client.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU").sheet1

sheet = connect_sheet()

def get_data():
    return pd.DataFrame(sheet.get_all_records())

# 3. UI Design
st.markdown("<h1 style='text-align: center; color: #BB86FC;'>🖤 NOIR POS TERMINAL</h1>", unsafe_allow_html=True)
st.divider()

df = get_data()

# 4. Transaction Section
st.subheader("New Sale Transaction")
with st.form("sale_form"):
    product_name = st.selectbox("Select Product", df.iloc[:, 0].tolist())
    quantity = st.number_input("Quantity", min_value=1, value=1)
    submit = st.form_submit_button("Complete Sale ✅")

    if submit:
        # Find product row
        cell = sheet.find(product_name)
        current_stock = int(sheet.cell(cell.row, 2).value) # Stock is in column B
        
        if current_stock >= quantity:
            new_stock = current_stock - quantity
            sheet.update_cell(cell.row, 2, new_stock) # Update Column B
            st.success(f"Sold {quantity} of {product_name}. Stock updated!")
            st.cache_data.clear()
        else:
            st.error("Insufficient Stock!")

# 5. Inventory Overview
st.divider()
st.subheader("Current Inventory Status")
st.dataframe(get_data(), use_container_width=True, hide_index=True)
