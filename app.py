import streamlit as st
import pandas as pd
import gspread

st.set_page_config(page_title="NOIR POS TERMINAL", layout="centered")

def connect_sheet():
    try:
        # استخراج البيانات من السكرت
        info = dict(st.secrets["gcp_service_account"])
        
        # أهم سطر: تنظيف المفتاح من أي رموز إضافية أو مسافات
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
    df = pd.DataFrame(sheet.get_all_records())
    
    with st.form("sale_form"):
        item = st.selectbox("Product", df['Name'].tolist())
        qty = st.number_input("Quantity", min_value=1, step=1)
        if st.form_submit_button("Complete Sale ✅"):
            cell = sheet.find(item)
            current_stock = int(sheet.cell(cell.row, 2).value)
            if current_stock >= qty:
                sheet.update_cell(cell.row, 2, current_stock - qty)
                st.balloons()
                st.success("Updated!")
                st.cache_data.clear()
            else:
                st.error("No Stock!")
    
    st.dataframe(df, use_container_width=True, hide_index=True)
