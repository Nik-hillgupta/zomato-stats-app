def generate_summary(df):
    total_orders = len(df)
    total_spent = df["amount"].sum()
    max_order = df.loc[df["amount"].idxmax()]
    min_order = df.loc[df["amount"].idxmin()]

    max_amt = f"₹{max_order['amount']:.2f}"
    min_amt = f"₹{min_order['amount']:.2f}"

    yearwise = df.groupby(df["order_date"].dt.year)["amount"].sum().sort_index()
    summary = f"""
### 📦 Total Orders Placed: {total_orders}
### 💰 Total Amount Spent: ₹{total_spent:,.2f}
### 📈 Highest Value Order: {max_amt} at {max_order['restaurant']}
### 📉 Lowest Value Order: {min_amt} at {min_order['restaurant']}

📅 **Year-on-Year Spend:**
"""
    for year, amt in yearwise.items():
        summary += f"- {year}: ₹{amt:,.2f}\n"

    return summary
