import pandas as pd

def generate_summary(df: pd.DataFrame) -> str:
    # --- Ensure 'amount' is numeric and 'order_date' is datetime ---
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    
    # --- Compute totals ---
    total_orders = len(df)
    total_amount = df["amount"].sum()
    
    # --- Highest & Lowest Orders ---
    highest_order = df.loc[df["amount"].idxmax()]
    lowest_order = df.loc[df["amount"].idxmin()]
    
    # --- Year-wise Spend ---
    df["year"] = df["order_date"].dt.year
    yearwise = df.groupby("year")["amount"].sum().sort_index()

    # --- Build Markdown Summary ---
    summary_lines = [
        "### 📊 Order Summary",
        f"📦 **Total Orders Placed**: {total_orders}",
        f"💰 **Total Amount Spent**: ₹{total_amount:,.2f}",
        f"📈 **Highest Value Order**: ₹{highest_order['amount']} at {highest_order.get('restaurant', 'N/A')}",
        f"📉 **Lowest Value Order**: ₹{lowest_order['amount']} at {lowest_order.get('restaurant', 'N/A')}",
        "",
        "### 📅 Year-on-Year Spend:",
    ]
    
    for year, amt in yearwise.items():
        summary_lines.append(f"- **{int(year)}**: ₹{amt:,.2f}")

    return "\n".join(summary_lines)
