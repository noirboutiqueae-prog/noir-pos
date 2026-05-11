import streamlit as st
import pandas as pd
import gspread

# 1. Page Configuration
st.set_page_config(page_title="NOIR Inventory & POS", layout="wide")

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

# 2. Sidebar Navigation
st.sidebar.title("🖤 NOIR Management")
choice = st.sidebar.radio("Navigate to:", ["POS Terminal", "Add New Product", "Daily Sales Report"])

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
        st.title("🛒 Record a Sale")
        with st.form("sale_form", clear_on_submit=True):
            product = st.selectbox("Select Product", df['Name'].tolist())
            amount = st.number_input("Quantity Sold", min_value=1, step=1)
            
            if st.form_submit_button("Complete Sale ✅"):
                cell = sheet.find(product)
                row = cell.row
                curr_stock = int(df.loc[df['Name'] == product, 'Stock'].values[0])
                curr_sold = int(df.loc[df['Name'] == product, 'Sold_Today'].values[0])
                
                if curr_stock >= amount:
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
                    sheet.append_row([new_name, new_stock, new_cost, new_sell, 0])
                    st.success(f"Successfully added {new_name}!")
                    st.cache_data.clear()
                    st.rerun()

    # --- Section 3: Daily Sales Report (Updated with Total Revenue) ---
    elif choice == "Daily Sales Report":
        st.title("📊 Daily Sales Report")
        
        # Calculate Revenue per item
        df['Total_Revenue'] = df['Sold_Today'] * df['Sell']
        
        # Grand Totals
        total_qty = df['Sold_Today'].sum()
        grand_total_revenue = df['Total_Revenue'].sum()
        
        # Display Key Metrics
        col1, col2 = st.columns(2)
        col1.metric("Total Items Sold Today", f"{int(total_qty)} Units")
        col2.metric("Grand Total Revenue", f"${grand_total_revenue:,.2f}")
        
        st.write("### Detailed Sales Breakdown")
        # Filter only items that were sold today
        report_df = df[df['Sold_Today'] > 0][['Name', 'Sold_Today', 'Sell', 'Total_Revenue']]
        
        if not report_df.empty:
            # Display the table with the Total_Revenue column
            st.table(report_df)
            
            # Summary footer for the table
            st.info(f"Summary: You have sold {int(total_qty)} items with a total value of ${grand_total_revenue:,.2f}")
            
            csv = report_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="Download Report 🖨️",
                data=csv,
                file_name='daily_sales_report.csv',
                mime='text/csv',
            )
        else:
            st.info("No sales recorded for today yet.")

    # Inventory View at the bottom
    st.divider()
    st.subheader("📦 Inventory Snapshot")
    st.dataframe(df[['Name', 'Stock', 'Sell', 'Sold_Today']], use_container_width=True, hide_index=True)
