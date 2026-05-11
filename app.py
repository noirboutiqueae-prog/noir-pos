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
choice = st.sidebar.radio("Navigate to:", ["POS Terminal", "Add New Stock", "Sales & Stock Aging"])

if sheet:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Clean Numeric Columns
    numeric_cols = ['Stock', 'Cost', 'Sell', 'Sold_Today']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # --- Section 1: POS Terminal ---
    if choice == "POS Terminal":
        st.title("🛒 Flower Sale")
        with st.form("sale_form", clear_on_submit=True):
            product = st.selectbox("Select Flower/Bouquet", df['Name'].tolist())
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

    # --- Section 2: Add New Stock (With Date) ---
    elif choice == "Add New Stock":
        st.title("➕ Add New Flower Batch")
        with st.form("add_product_form", clear_on_submit=True):
            new_name = st.text_input("Flower Name (e.g., Red Roses)")
            new_stock = st.number_input("Initial Quantity", min_value=0, step=1)
            new_cost = st.number_input("Cost per Item", min_value=0.0)
            new_sell = st.number_input("Selling Price", min_value=0.0)
            # Automatic Date Capture
            today_date = datetime.now().strftime("%Y-%m-%d")
            
            if st.form_submit_button("Add to Inventory 💾"):
                if new_name:
                    # Append: Name, Stock, Cost, Sell, Sold_Today, Date_Added
                    sheet.append_row([new_name, new_stock, new_cost, new_sell, 0, today_date])
                    st.success(f"Added {new_name} on {today_date}")
                    st.cache_data.clear()
                    st.rerun()

    # --- Section 3: Sales & Stock Aging (The New Feature) ---
    elif choice == "Sales & Stock Aging":
        st.title("📅 Stock Aging & Sales Report")
        
        # Calculate Aging
        if 'Date_Added' in df.columns:
            df['Date_Added'] = pd.to_datetime(df['Date_Added'], errors='coerce')
            today = pd.Timestamp(datetime.now().date())
            df['Days_in_Stock'] = (today - df['Date_Added']).dt.days
        
        # Metrics
        df['Total_Revenue'] = df['Sold_Today'] * df['Sell']
        st.metric("Total Today's Revenue", f"${df['Total_Revenue'].sum():,.2f}")
        
        st.write("### 📊 Inventory Aging Details")
        # Custom display to highlight old flowers
        def highlight_old(val):
            color = 'red' if val > 3 else 'black'
            return f'color: {color}'
        
        aging_df = df[['Name', 'Stock', 'Date_Added', 'Days_in_Stock']].copy()
        aging_df['Date_Added'] = aging_df['Date_Added'].dt.date
        st.dataframe(aging_df.style.applymap(highlight_old, subset=['Days_in_Stock']), use_container_width=True)
        st.info("💡 Note: Flowers in RED have been in stock for more than 3 days.")

    # Bottom Inventory View
    st.divider()
    st.subheader("📦 Live Inventory Snapshot")
    st.dataframe(df[['Name', 'Stock', 'Sell', 'Sold_Today']], use_container_width=True, hide_index=True)
