import streamlit as st
import pandas as pd
import gspread

# 1. Page Config
st.set_page_config(page_title="NOIR POS SYSTEM", layout="centered")

# 2. Connection Logic (Modern & Fast)
def connect_to_sheet():
    try:
        # Connect using the dict in secrets
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        # Open your specific sheet
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

sheet = connect_to_sheet()

# 3. UI Header
st.markdown("<h1 style='text-align: center; color: #BB86FC;'>🖤 NOIR POS TERMINAL</h1>", unsafe_allow_html=True)
st.divider()

if sheet:
    # Get all records
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # 4. Sales Section
    st.subheader("🛒 New Transaction")
    with st.form("pos_form"):
        # Select product from Column 'Name'
        item = st.selectbox("Select Product", df['Name'].tolist())
        qty = st.number_input("Quantity to Sell", min_value=1, value=1)
        submit = st.form_submit_button("Confirm Sale ✅")

        if submit:
            # Find the row of the item
            cell = sheet.find(item)
            # Assuming Stock is in the 2nd Column (B)
            current_stock = int(sheet.cell(cell.row, 2).value)
            
            if current_stock >= qty:
                new_stock = current_stock - qty
                sheet.update_cell(cell.row, 2, new_stock)
                st.balloons()
                st.success(f"Successfully sold {qty} of {item}! Stock is now {new_stock}.")
                st.cache_data.clear()
            else:
                st.error(f"Not enough stock! Current stock is only {current_stock}.")

    # 5. Live Inventory View
    st.divider()
    st.subheader("📦 Live Inventory")
    st.dataframe(df, use_container_width=True, hide_index=True)
