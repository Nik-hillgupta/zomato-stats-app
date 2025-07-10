import pandas as pd
from collections import Counter

def compute_summary(df: pd.DataFrame) -> list[str]:
    lines = []
    df = df.copy()

    total_orders = len(df)
    total_amount = df["amount"].sum(skipna=True)

    lines.append(f"• Total orders placed: **{total_orders}**")
    lines.append(f"• Total amount spent: **₹{total_amount:,.2f}**")

    # Highest and lowest
    if not df["amount"].isna().all():
        max_row = df.loc[df["amount"].idxmax()]
        min_row = df.loc[df["amount"].idxmin()]

        lines.append(f"• Highest order: **₹{max_row['amount']:.2f}** from **{max_row['restaurant']}**")
        lines.append(f"• Lowest order: **₹{min_row['amount']:.2f}** from **{min_row['restaurant']}**")

    # Year-wise spend
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["year"] = df["order_date"].dt.year
    yearly = df.groupby("year")["amount"].sum().dropna().sort_index()

    if not yearly.empty:
        lines.append("• Year-on-Year Spend:")
        for year, amt in yearly.items():
            lines.append(f"  - {int(year)}: ₹{amt:,.2f}")

    # Most ordered items
    all_items = []
    for i in df["items"]:
        all_items.extend(i)
    counter = Counter(all_items)
    top_items = counter.most_common(5)

    if top_items:
        lines.append("• Most Ordered Items:")
        for item, count in top_items:
            lines.append(f"  - {item} ({count} times)")

    return lines
