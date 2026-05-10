import streamlit as st
import pandas as pd
import google.generativeai as genai

# إعدادات الصفحة
st.set_page_config(page_title="NOIR BOUTIQUE POS", layout="wide")

# رابط ملفك (تأكد أن هذا هو رابط ملفك الصحيح)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU/edit?gid=0#gid=0"
CSV_URL = SHEET_URL.replace('/edit#gid=', '/export?format=csv&gid=')

st.title("🖤 NOIR BOUTIQUE")

# زر لتحديث البيانات
if st.button('تحديث البيانات 🔄'):
    st.cache_data.clear()

try:
    # قراءة البيانات مباشرة من الرابط العام
    df = pd.read_csv(CSV_URL)
    
    # عرض إجمالي المبيعات (بفرض أن العمود E هو السعر)
    total_sales = df.iloc[:, 4].sum() if len(df.columns) > 4 else 0
    st.metric("إجمالي المبيعات", f"{total_sales} AED")

    # عرض الجدول
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error("تأكد من جعل ملف قوقل شيت 'Anyone with the link can Edit'")
    st.info("رابط الملف المستخدم: " + SHEET_URL)
