import streamlit as st
import pandas as pd
import gspread

# 1. POS Terminal UI
st.set_page_config(page_title="NOIR POS TERMINAL", layout="centered")

# 2. Connection Logic with Debugging
def connect_to_sheet():
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("Key 'gcp_service_account' is missing from Secrets!")
            return None
        
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        # Your specific spreadsheet ID
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"⚠️ Connection Error: {str(e)}")
        return None

sheet = connect_to_sheet()

st.markdown("<h1 style='text-align: center;'>🖤 NOIR POS TERMINAL</h1>", unsafe_allow_html=True)
st.divider()

if sheet:
    # Button to force data refresh
    if st.button("Refresh Inventory 🔄"):
        st.cache_data.clear()

    # Load data once and cache it
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # 3. POS Transaction Section
    st.subheader("🛒 Process a New Sale")
    with st.form("pos_sale", clear_on_submit=True):
        selected_item = st.selectbox("Select Product", df['Name'].tolist())
        amount_sold = st.number_input("Quantity", min_value=1, step=1)
        complete_sale = st.form_submit_button("Complete Transaction ✅")

        if complete_sale:
            with st.spinner("Recording sale..."):
                try:
                    # Find product row
                    cell = sheet.find(selected_item)
                    row = cell.row
                    
                    # Columns from your sheet: 
                    # Stock = Column 2 (B), Sold_Today = Column 5 (E)
                    current_stock = int(sheet.cell(row, 2).value)
                    current_sold_today = int(sheet.cell(row, 5).value or 0)
                    
                    if current_stock >= amount_sold:
                        # Transaction execution
                        sheet.update_cell(row, 2, current_stock - amount_sold)
                        sheet.update_cell(row, 5, current_sold_today + amount_sold)
                        
                        st.balloons()
                        st.success(f"Sale of {amount_sold} {selected_item} recorded successfully!")
                        st.cache_data.clear()
                    else:
                        st.error(f"Not enough stock! Available: {current_stock}")
                except Exception as ex:
                    st.error(f"Failed to update sheet: {ex}")

    # 4. Table Preview
    st.divider()
    st.subheader("📊 Current Stock Overview")
    st.dataframe(df, use_container_width=True, hide_index=True)
