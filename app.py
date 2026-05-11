import streamlit as st
import pandas as pd
import gspread
import plotly.express as px

# 1. POS Terminal Setup
st.set_page_config(page_title="NOIR POS TERMINAL", layout="centered")

# 2. Connection using the service account secrets
def connect_sheet():
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        # Spreadsheet ID from your provided URL
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

sheet = connect_sheet()

# 3. Header & UI
st.markdown("<h1 style='text-align: center;'>🖤 NOIR POS TERMINAL</h1>", unsafe_allow_html=True)
st.divider()

if sheet:
    # Refresh data
    if st.button("Refresh Inventory 🔄"):
        st.cache_data.clear()

    # Get data and columns
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # 4. Sale Transaction Form
    st.subheader("🛒 Record a New Sale")
    with st.form("sale_form", clear_on_submit=True):
        item_name = st.selectbox("Select Product", df['Name'].tolist())
        qty_sold = st.number_input("Quantity", min_value=1, step=1)
        submit = st.form_submit_button("Confirm Transaction ✅")

        if submit:
            cell = sheet.find(item_name)
            row_idx = cell.row
            
            # Stock is Col 2, Sold_Today is Col 5 (Based on your sheet structure)
            current_stock = int(sheet.cell(row_idx, 2).value)
            current_sold = int(sheet.cell(row_idx, 5).value or 0)
            
            if current_stock >= qty_sold:
                # Update Google Sheet
                sheet.update_cell(row_idx, 2, current_stock - qty_sold)
                sheet.update_cell(row_idx, 5, current_sold + qty_sold)
                
                st.balloons()
                st.success(f"Transaction successful! {qty_sold} unit(s) deducted from {item_name}.")
                st.cache_data.clear()
            else:
                st.error(f"Insufficient Stock! Only {current_stock} remaining.")

    # 5. Live Inventory Display
    st.divider()
    st.subheader("📊 Live Inventory Status")
    st.dataframe(df, use_container_width=True, hide_index=True)
