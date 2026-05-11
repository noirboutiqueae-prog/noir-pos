import streamlit as st
import pandas as pd
import gspread

# 1. Page Configuration
st.set_page_config(page_title="NOIR Inventory & POS", layout="wide")

def get_connection():
    try:
        # Fetching secrets from Streamlit
        info = dict(st.secrets["gcp_service_account"])
        # Cleaning the private key for security & compatibility
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        gc = gspread.service_account_from_dict(info)
        # Connect via Spreadsheet ID
        sh = gc.open_by_key("1SDelm476fA-dJ2_ZWQI0hyMl8yKSxrYhMIdDoWWExfU")
        return sh.sheet1
    except Exception as e:
        st.error(f"⚠️ Connection Failed: {e}")
        return None

sheet = get_connection()

# 2. Sidebar Navigation
st.sidebar.title("🖤 NOIR Management")
choice = st.sidebar.radio("Navigate to:", ["POS Terminal", "Add New Product", "Daily Sales Report"])

if sheet:
    # Fetch Data and Clean Numeric Columns
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Ensure numeric columns are handled correctly to avoid "Arrow" errors
    numeric_cols = ['Stock', 'Cost', 'Sell', 'Sold_Today']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # --- Section 1: POS Terminal ---
    if choice == "POS Terminal":
        st.title("🛒 Record a Sale")
        with st.form("sale_form", clear_on_submit=True):
            product = st.selectbox("Select Product", df['Name'].tolist())
            amount = st.number_input("Quantity Sold", min_value=1, step=1)
            
            if st.form_submit_button("Complete Sale ✅"):
                # Find product in sheet
                cell = sheet.find(product)
                row = cell.row
                
                # Get current values
                curr_stock = int(df.loc[df['Name'] == product, 'Stock'].values[0])
                curr_sold = int(df.loc[df['Name'] == product, 'Sold_Today'].values[0])
                
                if curr_stock >= amount:
                    # Update Google Sheet (Stock in Col 2, Sold_Today in Col 5)
                    sheet.update_cell(row, 2, curr_stock - amount)
                    sheet.update_cell(row, 5, curr_sold + amount)
                    
                    st.success(f"Sold {amount} units of {product}")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Insufficient Stock!")

    # --- Section 2: Add New Product ---
    elif choice == "Add New Product":
        st.title("➕ Add Product to Inventory")
        with st.form("add_product_form", clear_on_submit=True):
            new_name = st.text_input("Product Name")
            new_stock = st.number_input("Initial Stock Quantity", min_value=0, step=1)
            new_cost = st.number_input("Cost Price", min_value=0.0)
            new_sell = st.number_input("Selling Price", min_value=0.0)
            
            if st.form_submit_button("Add Product 💾"):
                if new_name:
                    # Append new row (Name, Stock, Cost, Sell, Sold_Today=0)
                    sheet.append_row([new_name, new_stock, new_cost, new_sell, 0])
                    st.success(f"Successfully added {new_name} to inventory!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Please provide a product name.")

    # --- Section 3: Daily Sales Report ---
    elif choice == "Daily Sales Report":
        st.title("📊 Daily Sales Report")
        
        # Calculations
        df['Total_Revenue'] = df['Sold_Today'] * df['Sell']
        total_qty = df['Sold_Today'].sum()
        total_revenue = df['Total_Revenue'].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Items Sold", f"{int(total_qty)} units")
        col2.metric("Total Daily Revenue", f"${total_revenue:,.2f}")
        
        st.write("### Sales Breakdown")
        report_df = df[df['Sold_Today'] > 0][['Name', 'Sold_Today', 'Sell', 'Total_Revenue']]
        
        if not report_df.empty:
            st.table(report_df)
            
            # Print/Download Button
            csv = report_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="Download Report for Printing 🖨️",
                data=csv,
                file_name='daily_sales_report.csv',
                mime='text/csv',
            )
        else:
            st.info("No sales recorded yet for today.")

    # Always display inventory at the bottom
    st.divider()
    st.subheader("📦 Current Inventory Status")
    st.dataframe(df[['Name', 'Stock', 'Sell', 'Sold_Today']], use_container_width=True, hide_index=True)
