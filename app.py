import streamlit as st
import pandas as pd
import gspread

# 1. POS Terminal UI Setup
st.set_page_config(page_title="NOIR POS TERMINAL", layout="centered")

# 2. Advanced Debugging Connection
def connect_to_google():
    try:
        # Check if secrets exist
        if "gcp_service_account" not in st.secrets:
            st.error("Secrets are missing! Please check the white box in Settings.")
            return None
        
        # Connect using Service Account
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"⚠️ Connection Failed: {str(e)}")
        return None

sheet = connect_to_google()

# 3. Application Interface
st.markdown("<h1 style='text-align: center;'>🖤 NOIR POS TERMINAL</h1>", unsafe_allow_html=True)
st.divider()

if sheet:
    # Fetch all data
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # 4. Sale Transaction Form
    st.subheader("🛒 Transaction Entry")
    with st.form("pos_form", clear_on_submit=True):
        item_name = st.selectbox("Select Product", df['Name'].tolist())
        qty = st.number_input("Quantity Sold", min_value=1, step=1)
        price_paid = st.number_input("Price per Unit (Optional)", value=0)
        submit = st.form_submit_button("Complete Sale ✅")

        if submit:
            with st.spinner("Processing transaction..."):
                try:
                    cell = sheet.find(item_name)
                    row_idx = cell.row
                    
                    # Columns Mapping: Stock=Col 2, Sold_Today=Col 5
                    current_stock = int(sheet.cell(row_idx, 2).value)
                    current_sold = int(sheet.cell(row_idx, 5).value or 0)
                    
                    if current_stock >= qty:
                        # Execution
                        sheet.update_cell(row_idx, 2, current_stock - qty)
                        sheet.update_cell(row_idx, 5, current_sold + qty)
                        st.balloons()
                        st.success(f"Sale recorded! {item_name} stock updated successfully.")
                        st.cache_data.clear()
                    else:
                        st.error(f"Insufficient stock! Available: {current_stock}")
                except Exception as ex:
                    st.error(f"Transaction Error: {ex}")

    # 5. Inventory Table View
    st.divider()
    st.subheader("📊 Current Inventory")
    st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.info("System is waiting for a valid connection. Please verify the Secrets format.")
