import streamlit as st
import pandas as pd
import gspread

# 1. Config
st.set_page_config(page_title="NOIR POS", layout="centered")

# 2. Connection
def connect_to_sheet():
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"Error: {e}")
        return None

sheet = connect_to_sheet()

st.title("🖤 NOIR POS TERMINAL")

if sheet:
    # Refresh button
    if st.button("Refresh Data 🔄"):
        st.cache_data.clear()

    # Get data
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # POS Sale Form
    st.subheader("🛒 Process a Sale")
    with st.form("pos_form", clear_on_submit=True):
        item = st.selectbox("Select Item", df['Name'].tolist())
        qty = st.number_input("Quantity", min_value=1, step=1)
        confirm = st.form_submit_button("Complete Sale ✅")

        if confirm:
            cell = sheet.find(item)
            # Stock is Col 2, Sold_Today is Col 5
            current_stock = int(sheet.cell(cell.row, 2).value)
            current_sold = int(sheet.cell(cell.row, 5).value or 0)
            
            if current_stock >= qty:
                sheet.update_cell(cell.row, 2, current_stock - qty)
                sheet.update_cell(cell.row, 5, current_sold + qty)
                st.balloons()
                st.success(f"Sold {qty} of {item}!")
                st.cache_data.clear()
            else:
                st.error("Not enough stock!")

    st.divider()
    st.subheader("📊 Live Inventory")
    st.dataframe(df, use_container_width=True, hide_index=True)
