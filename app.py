import streamlit as st
import pandas as pd
import gspread

# 1. POS Interface Setup
st.set_page_config(page_title="NOIR POS TERMINAL", layout="centered")

# 2. Connection with Error Handling
def connect_to_google():
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        # Spreadsheet ID from your URL
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"⚠️ Connection Error: {str(e)}")
        return None

sheet = connect_to_google()

st.markdown("<h1 style='text-align: center;'>🖤 NOIR POS TERMINAL</h1>", unsafe_allow_html=True)
st.divider()

if sheet:
    # Refreshing Data
    if st.button("Refresh Inventory 🔄"):
        st.cache_data.clear()

    # Getting all rows
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # 3. Sales Transaction Form
    st.subheader("🛒 Record a New Sale")
    with st.form("sale_entry", clear_on_submit=True):
        selected_item = st.selectbox("Select Product", df['Name'].tolist())
        quantity_to_sell = st.number_input("Quantity", min_value=1, step=1)
        confirm_btn = st.form_submit_button("Complete Sale ✅")

        if confirm_btn:
            with st.spinner("Updating Google Sheets..."):
                try:
                    # Find exact row
                    cell = sheet.find(selected_item)
                    row_idx = cell.row
                    
                    # Columns: Stock is B (2), Sold_Today is E (5)
                    current_stock = int(sheet.cell(row_idx, 2).value)
                    current_sold = int(sheet.cell(row_idx, 5).value or 0)
                    
                    if current_stock >= quantity_to_sell:
                        # Transaction Execution
                        sheet.update_cell(row_idx, 2, current_stock - quantity_to_sell)
                        sheet.update_cell(row_idx, 5, current_sold + quantity_to_sell)
                        st.balloons()
                        st.success(f"Sale successful! {quantity_to_sell} units deducted from {selected_item}.")
                        st.cache_data.clear()
                    else:
                        st.error(f"Insufficient stock! Only {current_stock} available.")
                except Exception as ex:
                    st.error(f"Transaction failed: {ex}")

    # 4. Inventory List View
    st.divider()
    st.subheader("📊 Current Stock Levels")
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.warning("Please check your Secrets configuration and ensure the Service Account email has 'Editor' access to the Sheet.")
