import streamlit as st
import pandas as pd
import gspread

st.set_page_config(page_title="NOIR POS TERMINAL", layout="centered")

def connect_sheet():
    try:
        # Fetch dictionary from secrets
        info = dict(st.secrets["gcp_service_account"])
        
        # Clean the key: Handle Streamlit's newline escaping
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        
        gc = gspread.service_account_from_dict(info)
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

sheet = connect_sheet()

st.markdown("<h1 style='text-align: center;'>🖤 NOIR POS TERMINAL</h1>", unsafe_allow_html=True)
st.divider()

if sheet:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    with st.form("sale_form"):
        item = st.selectbox("Product", df['Name'].tolist())
        qty = st.number_input("Quantity", min_value=1, step=1)
        if st.form_submit_button("Complete Sale ✅"):
            cell = sheet.find(item)
            current_stock = int(sheet.cell(cell.row, 2).value)
            if current_stock >= qty:
                # Deduction: Column B is Stock, Column E is Sold_Today
                sheet.update_cell(cell.row, 2, current_stock - qty)
                current_sold = int(sheet.cell(cell.row, 5).value or 0)
                sheet.update_cell(cell.row, 5, current_sold + qty)
                st.balloons()
                st.success(f"Sold {qty} {item}!")
                st.cache_data.clear()
            else:
                st.error("Insufficient Stock!")
    
    st.dataframe(df, use_container_width=True, hide_index=True)
