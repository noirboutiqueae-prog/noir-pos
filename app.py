import streamlit as st
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="NOIR BOUTIQUE POS", layout="wide")

# رابط ملفك الحقيقي الذي أرسلته
SHEET_ID = "1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

st.markdown("<h1 style='text-align: center; color: white;'>🖤 NOIR BOUTIQUE</h1>", unsafe_allow_html=True)

# زر لتحديث البيانات
if st.button('تحديث البيانات 🔄'):
    st.cache_data.clear()

try:
    # قراءة البيانات مباشرة من الرابط
    df = pd.read_csv(SHEET_URL)
    
    # تنظيف البيانات (إزالة الصفوف الفارغة)
    df = df.dropna(how='all')

    # عرض إحصائيات سريعة في الأعلى
    col1, col2 = st.columns(2)
    with col1:
        st.metric("عدد المنتجات", len(df))
    with col2:
        # يحسب إجمالي المبيعات إذا كان العمود الخامس (E) هو السعر
        if len(df.columns) >= 5:
            total = pd.to_numeric(df.iloc[:, 4], errors='coerce').sum()
            st.metric("إجمالي المبيعات التقريبي", f"{total} AED")

    # عرض الجدول بشكل أنيق
    st.markdown("### 📊 جدول المخزون والمبيعات")
    st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("خطأ: تأكد من جعل ملف قوقل شيت 'Anyone with the link can Edit'")
    st.info("إذا فعلت ذلك، اضغط على زر تحديث البيانات أعلاه.")
