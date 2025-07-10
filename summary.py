def generate_summary(df):
    df_clean = df[df["amount"].notnull()].copy()
    total_orders = len(df_clean)
    total_spent = df_clean["amount"].sum()

    max_order = df_clean.loc[df_clean["amount"].idxmax()]
    min_order = df_clean.loc[df_clean["amount"].idxmin()]

    # Parse years
    df_clean["year"] = df_clean["order_date"].astype(str).str.extract(r"(\d{4})")
    yoy = df_clean.groupby("year")["amount"].sum().sort_index()

    # Items breakdown
    all_items = df_clean["items"].explode()
    item_freq = all_items.value_counts().head(5)

    summary = f"""
**📦 Total Orders Placed:** {total_orders}  
**💰 Total Amount Spent:** ₹{total_spent:,.2f}  
**📈 Highest Value Order:** ₹{max_order['amount']:.2f} at {max_order['restaurant']}  
**📉 Lowest Value Order:** ₹{min_order['amount']:.2f} at {min_order['restaurant']}  
"""

    summary += "\n**📅 Year-on-Year Spend:**\n"
    for year, amt in yoy.items():
        summary += f"- {year}: ₹{amt:,.2f}\n"

    summary += "\n**🍴 Most Ordered Items:**\n"
    for item, count in item_freq.items():
        summary += f"- {item} × {count}\n"

    return summary
