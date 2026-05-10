import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px

# 1. إعدادات الصفحة والذكاء الاصطناعي
st.set_page_config(page_title="NOIR BOUTIQUE PRO", layout="wide")

# جلب المفتاح من Secrets (تأكد أنك وضعت GEMINI_API_KEY في السكرت)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
except:
    st.warning("⚠️ ملاحظة: نظام الذكاء الاصطناعي يحتاج مفتاح GEMINI_API_KEY ليعمل.")

# 2. جلب البيانات
SHEET_ID = "1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

def load_data():
    df = pd.read_csv(SHEET_URL)
    df = df.dropna(how='all')
    # تحويل الأعمدة لأرقام لضمان الحسابات الصحيحة
    for col in df.columns[1:]: # تحويل الأعمدة بعد الاسم لأرقام
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df = load_data()

# 3. واجهة المستخدم (العنوان)
st.markdown("<h1 style='text-align: center; color: #BB86FC;'>🖤 NOIR BOUTIQUE POS PRO</h1>", unsafe_allow_html=True)
st.divider()

# 4. شريط جانبي للتنقل والذكاء الاصطناعي
with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/ffffff/luxury.png") # أيقونة بسيطة
    st.title("لوحة التحكم")
    page = st.radio("انتقل إلى:", ["📊 المبيعات والمخزون", "🤖 مساعد NOIR الذكي", "📈 تحليل الأداء"])
    
    if st.button('تحديث البيانات 🔄'):
        st.cache_data.clear()
        st.rerun()

# --- الصفحة الأولى: المبيعات والمخزون ---
if page == "📊 المبيعات والمخزون":
    # كروت الإحصائيات
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("عدد الموديلات", len(df))
    with c2:
        total_sales = df.iloc[:, 4].sum() # عمود السعر (E)
        st.metric("إجمالي الدخل", f"{total_sales:,.0f} AED")
    with c3:
        total_stock = df.iloc[:, 1].sum() # عمود المخزون (B)
        st.metric("القطع المتوفرة", int(total_stock))
    with c4:
        low_stock = len(df[df.iloc[:, 1] < 5])
        st.metric("قطع قاربت على النفاد", low_stock, delta_color="inverse")

    # البحث والجدول
    search = st.text_input("🔍 ابحث عن موديل أو قطعة...")
    if search:
        filtered_df = df[df.iloc[:, 0].str.contains(search, case=False, na=False)]
    else:
        filtered_df = df

    st.subheader("📦 حالة المخزون الحالية")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# --- الصفحة الثانية: مساعد NOIR الذكي ---
elif page == "🤖 مساعد NOIR الذكي":
    st.subheader("💬 اسأل مساعد بوتيك نوار")
    user_q = st.text_input("مثال: كيف أزيد مبيعاتي هذا الشهر؟ أو حلل لي بضاعتي.")
    if user_q:
        with st.spinner('جاري التفكير...'):
            try:
                prompt = f"أنت مساعد ذكي لبوتيك ملابس اسمه NOIR. هذه بياناتي الحالية: {df.to_string()}. أجب على هذا السؤال: {user_q}"
                response = model.generate_content(prompt)
                st.info(response.text)
            except:
                st.error("تأكد من تفعيل GEMINI_API_KEY في إعدادات Secrets")

# --- الصفحة الثالثة: تحليل الأداء ---
elif page == "📈 تحليل الأداء":
    st.subheader("📈 تحليل بياني للمنتجات")
    fig = px.bar(df, x=df.columns[0], y=df.columns[4], 
                 title="مقارنة الأسعار بين الموديلات",
                 labels={'x': 'الموديل', 'y': 'السعر'},
                 color=df.columns[4], color_continuous_scale='Purples')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📉 حالة التوفر في المستودع")
    fig2 = px.pie(df, values=df.columns[1], names=df.columns[0], title="توزيع المخزون")
    st.plotly_chart(fig2, use_container_width=True)
