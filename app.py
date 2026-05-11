import streamlit as st
import pandas as pd
import gspread
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="NOIR Flowers POS", layout="wide")

def get_connection():
    try:
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
choice = st.sidebar.radio("Navigate to:", ["POS Terminal", "Add New Stock", "Daily Sales & Stock Aging"])

if sheet:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Ensure numeric columns are handled correctly
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
                    sheet.update_cell(row, 2, curr_stock - amount)
                    sheet.update_cell(row, 5, curr_sold + amount)
                    st.balloons()
                    st.success(f"Sold {amount} of {product}")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Out of Stock!")

    # --- Section 2: Add New Stock ---
    elif choice == "Add New Stock":
        st.title("➕ Add New Flower Batch")
        with st.form("add_product_form", clear_on_submit=True):
            new_name = st.text_input("Flower Name")
            new_stock = st.number_input("Initial Quantity", min_value=0, step=1)
            new_cost = st.number_input("Cost per Item", min_value=0.0)
            new_sell = st.number_input("Selling Price", min_value=0.0)
            today_date = datetime.now().strftime("%Y-%m-%d")
            
            if st.form_submit_button("Add to Inventory 💾"):
                if new_name:
                    sheet.append_row([new_name, new_stock, new_cost, new_sell, 0, today_date])
                    st.success(f"Added {new_name} on {today_date}")
                    st.cache_data.clear()
                    st.rerun()

    # --- Section 3: Daily Sales & Aging (Fixed and Updated) ---
    elif choice == "Daily Sales & Stock Aging":
        st.title("📊 Daily Report & Stock Aging")
        
        # 1. Sales Calculation (Total Revenue)
        df['Total_Revenue'] = df['Sold_Today'] * df['Sell']
        grand_total = df['Total_Revenue'].sum()
        
        # 2. Aging Calculation
        if 'Date_Added' in df.columns:
            df['Date_Added'] = pd.to_datetime(df['Date_Added'], errors='coerce')
            today = pd.Timestamp(datetime.now().date())
            df['Days_in_Stock'] = (today - df['Date_Added']).dt.days.fillna(0).astype(int)
        
        col1, col2 = st.columns(2)
        col1.metric("Items Sold Today", f"{int(df['Sold_Today'].sum())} units")
        col2.metric("Total Daily Revenue", f"${grand_total:,.2f}")
        
        st.write("### 💰 Sales Breakdown")
        sales_df = df[df['Sold_Today'] > 0][['Name', 'Sold_Today', 'Sell', 'Total_Revenue']]
        if not sales_df.empty:
            st.table(sales_df)
        else:
            st.info("No sales yet today.")

        st.divider()
        st.write("### 🥀 Stock Aging (Freshness)")
        
        # Fixed Style logic (map instead of applymap)
        def highlight_aging(val):
            return 'color: red; font-weight: bold' if val > 3 else 'color: green'
        
        aging_display = df[['Name', 'Stock', 'Date_Added', 'Days_in_Stock']].copy()
        aging_display['Date_Added'] = aging_display['Date_Added'].dt.date
        
        st.dataframe(aging_display.style.map(highlight_aging, subset=['Days_in_Stock']), use_container_width=True)
        st.info("💡 Items in RED have been in stock for more than 3 days.")

    # Bottom Inventory View
    st.divider()
    st.subheader("📦 Live Inventory View")
    st.dataframe(df[['Name', 'Stock', 'Sell', 'Sold_Today']], use_container_width=True, hide_index=True)
