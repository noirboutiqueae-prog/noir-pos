import streamlit as st
import pandas as pd
import gspread

# 1. إعدادات الصفحة
st.set_page_config(page_title="NOIR Inventory & POS", layout="wide")

def get_connection():
    try:
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        gc = gspread.service_account_from_dict(info)
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال: {e}")
        return None

sheet = get_connection()

# 2. القائمة الجانبية للتنقل
st.sidebar.title("🖤 NOIR Management")
choice = st.sidebar.radio("انتقل إلى:", ["نقطة البيع (POS)", "إضافة منتج جديد", "تقرير المبيعات اليومي"])

if sheet:
    # سحب البيانات وتنظيفها
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    for col in ['Stock', 'Cost', 'Sell', 'Sold_Today']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # --- القسم الأول: نقطة البيع ---
    if choice == "نقطة البيع (POS)":
        st.title("🛒 تسجيل عملية بيع")
        with st.form("sale_form", clear_on_submit=True):
            product = st.selectbox("اختر المنتج", df['Name'].tolist())
            amount = st.number_input("الكمية المبيعة", min_value=1, step=1)
            if st.form_submit_button("إتمام البيع ✅"):
                cell = sheet.find(product)
                row = cell.row
                curr_stock = int(df.loc[df['Name'] == product, 'Stock'].values[0])
                curr_sold = int(df.loc[df['Name'] == product, 'Sold_Today'].values[0])
                
                if curr_stock >= amount:
                    sheet.update_cell(row, 2, curr_stock - amount) # تحديث المخزون (B)
                    sheet.update_cell(row, 5, curr_sold + amount)   # تحديث المبيعات اليومية (E)
                    st.success(f"تم بيع {amount} من {product}")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("المخزون غير كافٍ!")

    # --- القسم الثاني: إضافة منتج جديد ---
    elif choice == "إضافة منتج جديد":
        st.title("➕ إضافة منتج للمخزون")
        with st.form("add_product_form", clear_on_submit=True):
            new_name = st.text_input("اسم المنتج الجديد")
            new_stock = st.number_input("الكمية المتوفرة", min_value=0, step=1)
            new_cost = st.number_input("سعر التكلفة", min_value=0.0)
            new_sell = st.number_input("سعر البيع", min_value=0.0)
            if st.form_submit_button("إضافة المنتج 💾"):
                if new_name:
                    # إضافة سطر جديد للملف (الاسم، المخزون، التكلفة، سعر البيع، مبيعات اليوم=0)
                    sheet.append_row([new_name, new_stock, new_cost, new_sell, 0])
                    st.success(f"تم إضافة {new_name} بنجاح!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("يرجى إدخال اسم المنتج")

    # --- القسم الثالث: تقرير المبيعات ---
    elif choice == "تقرير المبيعات اليومي":
        st.title("📊 تقرير المبيعات اليومية")
        
        # حساب الإحصائيات
        df['Total_Revenue'] = df['Sold_Today'] * df['Sell']
        total_qty = df['Sold_Today'].sum()
        total_money = df['Total_Revenue'].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("إجمالي الكميات المبيعة", f"{total_qty} قطعة")
        col2.metric("إجمالي الدخل اليومي", f"{total_money} ريال/درهم")
        
        st.write("### تفاصيل المبيعات لكل منتج")
        report_df = df[df['Sold_Today'] > 0][['Name', 'Sold_Today', 'Sell', 'Total_Revenue']]
        st.table(report_df)
        
        # زر الطباعة (تحويل التقرير لملف Excel/CSV للطباعة)
        csv = report_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="تحميل التقرير للطباعة 🖨️",
            data=csv,
            file_name='daily_report.csv',
            mime='text/csv',
        )

    # عرض جدول المخزون العام دائماً في الأسفل
    st.divider()
    st.subheader("📦 حالة المخزون الحالي")
    st.dataframe(df[['Name', 'Stock', 'Sell', 'Sold_Today']], use_container_width=True, hide_index=True)
