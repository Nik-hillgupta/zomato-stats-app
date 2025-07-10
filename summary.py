import pandas as pd

def generate_summary(df):
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    total_orders = len(df)
    total_amount = df["amount"].sum()

    max_row = df.loc[df["amount"].idxmax()] if not df["amount"].isnull().all() else None
    min_row = df.loc[df["amount"].idxmin()] if not df["amount"].isnull().all() else None

    max_text = f"₹{max_row['amount']} at {max_row['restaurant']}" if max_row is not None else "N/A"
    min_text = f"₹{min_row['amount']} at {min_row['restaurant']}" if min_row is not None else "N/A"

    yearwise = df.groupby(df["order_date"].dt.year)["amount"].sum().sort_index()
    yearwise_str = "".join([f"<li>{year}: ₹{amt:,.2f}</li>" for year, amt in yearwise.items()])

    return f"""
- 📦 <strong>Total Orders Placed:</strong> {total_orders}  
- 💰 <strong>Total Amount Spent:</strong> ₹{total_amount:,.2f}  
- 📈 <strong>Highest Value Order:</strong> {max_text}  
- 📉 <strong>Lowest Value Order:</strong> {min_text}  

📅 <strong>Year-on-Year Spend:</strong>
<ul>{yearwise_str}</ul>
"""
