import pandas as pd

def generate_summary(df):
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["amount"] = df["amount"].astype(float)

    total_orders = len(df)
    total_spent = df["amount"].sum()

    max_row = df.loc[df["amount"].idxmax()]
    min_row = df.loc[df["amount"].idxmin()]

    max_order = f"₹{max_row['amount']:.2f} at {max_row.get('restaurant', 'N/A')}"
    min_order = f"₹{min_row['amount']:.2f} at {min_row.get('restaurant', 'N/A')}"

    df["year"] = df["order_date"].dt.year
    yearwise = df.groupby("year")["amount"].sum().sort_index()

    summary = f"""
**📦 Total Orders Placed:** {total_orders}  
**💰 Total Amount Spent:** ₹{total_spent:,.2f}  
**📈 Highest Value Order:** {max_order}  
**📉 Lowest Value Order:** {min_order}  

📅 **Year-on-Year Spend:**
"""
    for year, amt in yearwise.items():
        summary += f"- {int(year)}: ₹{amt:,.2f}\n"

    return summary
