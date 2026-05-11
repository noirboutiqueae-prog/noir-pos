import streamlit as st
import gspread

st.title("🔍 NOIR System Diagnostic")

try:
    # 1. فحص وجود السكرت
    if "gcp_service_account" in st.secrets:
        st.success("✅ Secrets found in Streamlit.")
    else:
        st.error("❌ Secrets are MISSING in Streamlit settings!")

    # 2. محاولة الاتصال بقوقل
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
    sheet = sh.sheet1
    st.success("✅ Connected to Google Sheets successfully!")

    # 3. فحص البيانات
    data = sheet.get_all_values()
    if data:
        st.success(f"✅ Found {len(data)} rows of data.")
        st.write("Headers found:", data[0]) # بيطبع لك أول سطر في ملفك
    else:
        st.warning("❓ Sheet is empty.")

except Exception as e:
    st.error(f"🚨 The Real Error is: {str(e)}")
