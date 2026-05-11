import streamlit as st
import pandas as pd
import gspread
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="NOIR Flowers POS", layout="wide")

def get_connection():
    try:
        # استرجاع المفاتيح وتنظيفها
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        gc = gspread.service_account_from_dict(info)
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"⚠️ Connection Failed: {e}")
        return None

sheet = get_connection()

# Sidebar Navigation
st.sidebar.title("🌸 NOIR Flowers")
choice = st.sidebar.radio("Navigate to:", ["POS Terminal", "Restock / Add New", "Daily Sales & Stock Aging"])

if sheet:
    # جلب البيانات وتنظيف الأنواع لتجنب أخطاء Arrow
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    numeric_cols = ['Stock', 'Cost', 'Sell', 'Sold_Today']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # --- Section 1: POS Terminal ---
    if choice == "POS Terminal":
        st.title("🛒 Flower Sale")
        with st.form("sale_form", clear_on_submit=True):
            product = st.selectbox("Select Flower", df['Name'].tolist())
            amount = st.number_input("Quantity Sold", min_value=1, step=1)
            if st.form_submit_button("Complete Sale ✅"):
                cell = sheet.find(product)
                row = cell.row
                curr_stock = int(df.loc[df['Name'] == product, 'Stock'].values[0])
                curr_sold = int(df.loc[df['Name'] == product, 'Sold_Today'].values[0])
                
                if curr_stock >= amount:
                    # تحديث المخزون (Col 2) والمبيعات اليومية (Col 5)
                    sheet.update_cell(row, 2, curr_stock - amount)
                    sheet.update_cell(row, 5, curr_sold + amount)
                    st.balloons()
                    st.success(f"Sold {amount} of {product}!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Insufficient Stock!")

    # --- Section 2: Restock / Add New ---
    elif choice == "Restock / Add New":
        st.title("➕ Stock Management")
        tab1, tab2 = st.tabs(["Update Existing Stock", "Add Completely New Product"])
        
        with tab1:
            st.subheader("Add quantity to existing inventory")
            with st.form("restock_form", clear_on_submit=True):
                exist_product = st.selectbox("Product to Restock", df['Name'].tolist())
                add_qty = st.number_input("Additional Quantity", min_value=1, step=1)
                update_date = st.checkbox("Refresh 'Date Added' to today? (Reset Aging)")
                
                if st.form_submit_button("Update Stock 📈"):
                    cell = sheet.find(exist_product)
                    row = cell.row
                    old_stock = int(df.loc[df['Name'] == exist_product, 'Stock'].values[0])
                    sheet.update_cell(row, 2, old_stock + add_qty)
                    
                    if update_date:
                        sheet.update_cell(row, 6, datetime.now().strftime("%Y-%m-%d"))
                    
                    st.success(f"Updated {exist_product}! New stock: {old_stock + add_qty}")
                    st.cache_data.clear()
                    st.rerun()

        with tab2:
            st.subheader("Add a brand new type of flower")
            with st.form("new_product_form", clear_on_submit=True):
                new_name = st.text_input("Flower Name")
                new_stock = st.number_input("Initial Quantity", min_value=1, step=1)
                new_cost = st.number_input("Cost per Item", min_value=0.0)
                new_sell = st.number_input("Selling Price", min_value=0.0)
                if st.form_submit_button("Add New Product 💾"):
                    if new_name and new_name not in df['Name'].tolist():
                        sheet.append_row([new_name, new_stock, new_cost, new_sell, 0, datetime.now().strftime("%Y-%m-%d")])
                        st.success(f"Added {new_name} to database!")
                        st.cache_data.clear()
                        st.rerun()

    # --- Section 3: Daily Sales & Aging (The Fix) ---
    elif choice == "Daily Sales & Stock Aging":
        st.title("📊 Daily Performance & Aging")
        
        # إضافة خانة المجموع (Total Revenue)
        df['Total_Revenue'] = df['Sold_Today'] * df['Sell']
        grand_total = df['Total_Revenue'].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Items Sold", f"{int(df['Sold_Today'].sum())} Units")
        col2.metric("Total Daily Revenue", f"${grand_total:,.2f}")
        
        st.write("### 💰 Sales Report (Total Revenue per Item)")
        sales_df = df[df['Sold_Today'] > 0][['Name', 'Sold_Today', 'Sell', 'Total_Revenue']]
        st.table(sales_df if not sales_df.empty else pd.DataFrame(columns=['Name', 'Sold_Today', 'Sell', 'Total_Revenue']))

        st.divider()
        st.write("### 🥀 Freshness Tracking (Aging)")
        if 'Date_Added' in df.columns:
            df['Date_Added'] = pd.to_datetime(df['Date_Added'], errors='coerce')
            today = pd.Timestamp(datetime.now().date())
            df['Days_in_Stock'] = (today - df['Date_Added']).dt.days.fillna(0).astype(int)
            
            # تصحيح خطأ applymap باستخدام map
            def highlight_aging(val):
                return 'color: red; font-weight: bold' if val > 3 else 'color: green'
            
            aging_display = df[['Name', 'Stock', 'Date_Added', 'Days_in_Stock']].copy()
            aging_display['Date_Added'] = aging_display['Date_Added'].dt.date
            st.dataframe(aging_display.style.map(highlight_aging, subset=['Days_in_Stock']), use_container_width=True)

    # عرض المخزون في الأسفل دائماً
    st.divider()
    st.subheader("📦 Current Inventory View")
    st.dataframe(df[['Name', 'Stock', 'Sell', 'Sold_Today']], use_container_width=True, hide_index=True)
