import re
from bs4 import BeautifulSoup

def parse_email(html, fallback_date=None):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")

    # Early skip
    if any(x in text for x in ["Login Alert", "Zomato Gold", "Congratulations", "Your order has been cancelled", "Your bill payment"]):
        return None

    # Amount
    amount = None
    match = re.search(r"₹\s?([\d,]+\.\d{2})", text)
    if match:
        try:
            amount = float(match.group(1).replace(",", ""))
        except:
            amount = None

    # Name
    name_match = re.search(r"Hi\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text)
    name = name_match.group(1) if name_match else "N/A"

    # Restaurant
    restaurant_match = re.search(r"Thank you for ordering (?:from|at)\s+([^\n]+)", text)
    restaurant = restaurant_match.group(1).strip() if restaurant_match else "N/A"

    # Address
    address_match = re.search(r"Issued on behalf of\s+" + re.escape(restaurant) + r"\s+(.+?)(?:Bangalore|Mumbai|Delhi|Chennai|Pune)?.*\n", text, re.IGNORECASE) if restaurant else None
    address = address_match.group(1).strip() if address_match else "N/A"

    # Order Date
    date_match = re.search(r"(?:Delivered on|Ordered on)\s+(\d{1,2} \w+ \d{4})", text)
    order_date = date_match.group(1) if date_match else fallback_date.strftime("%d %b %Y") if fallback_date else "N/A"

    # Items
    lines = text.split("\n")
    item_lines = [line.strip() for line in lines if re.search(r"\d+ ?[xX] ", line) or "₹" in line]
    items = []
    for line in item_lines:
        item_match = re.search(r"(\d+ ?[xX])? ?(.+?) ?-? ?₹\s?([\d.]+)", line)
        if item_match:
            qty = item_match.group(1) or "1X"
            name_item = item_match.group(2).strip()
            price = item_match.group(3).strip()
            items.append(f"{qty} {name_item} - ₹{price}")
    if not items:
        items = ["N/A"]

    return {
        "name": name,
        "restaurant": restaurant,
        "restaurant_address": address,
        "order_date": order_date,
        "items": items,
        "amount": amount
    }
