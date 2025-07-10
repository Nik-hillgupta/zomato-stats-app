import re
from bs4 import BeautifulSoup

def parse_email(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    text = re.sub(r"[ \t]+", " ", text)

    if any(x in text for x in ["Login Alert", "Zomato Gold", "Congratulations", "cancelled", "bill payment"]):
        return None

    # Amount
    amount = None
    match = re.search(r"Total (paid|cost)\s*[₹Rs.]?\s?([\d,]+\.\d{2})", text)
    if not match:
        match = re.search(r"Paid\s*[₹Rs.]?\s?([\d,]+\.\d{2})", text)
    if not match:
        match = re.search(r"₹\s?([\d,]+\.\d{2})", text)
    if match:
        try:
            amount = float(match.group(2 if match.lastindex == 2 else 1).replace(",", ""))
        except:
            amount = None

    # Name
    name_match = re.search(r"Hi\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text)
    customer_name = name_match.group(1).strip() if name_match else "N/A"

    # Restaurant
    restaurant = None
    m = re.search(r"Thank you for ordering (?:from|food online on Zomato,)\s+([^\n]+)", text)
    if m:
        restaurant = m.group(1).strip()
    restaurant = restaurant or "N/A"

    # Address
    restaurant_address = None
    addr_match = re.search(r"Issued on behalf of\s+" + re.escape(restaurant) + r"\s+(.+?Bangalore.*?)\n", text, re.IGNORECASE)
    if addr_match:
        restaurant_address = addr_match.group(1).strip()
    restaurant_address = restaurant_address or "N/A"

    # Order date
    date_match = re.search(r"(\w{3}, \w{3} \d{1,2}, \d{4})", text)
    order_date = date_match.group(1) if date_match else None
    if not order_date:
        fallback = re.search(r"Delivered on (\d{1,2} \w+ \d{4})", text)
        if fallback:
            order_date = fallback.group(1)
    order_date = order_date or "N/A"

    # Items
    lines = text.split("\n")
    item_lines = [line.strip() for line in lines if re.search(r"\d+ ?[xX] ", line) or "₹" in line]
    items = []
    for line in item_lines:
        item_match = re.search(r"(\d+ ?[xX])? ?(.+?) ?-? ?₹\s?([\d.]+)", line)
        if item_match:
            qty = item_match.group(1) or "1X"
            name = item_match.group(2).strip()
            price = item_match.group(3).strip()
            items.append(f"{qty} {name} - ₹{price}")
        else:
            loose_match = re.match(r"(.*Cake|.*Pizza|.*Roll|.*Bhature|.*Burger|.*Paratha|.*Biryani|.*Kebab)", line, re.IGNORECASE)
            if loose_match:
                items.append(loose_match.group(1).strip())
    items = items or ["N/A"]

    return {
        "name": customer_name,
        "restaurant": restaurant,
        "restaurant_address": restaurant_address,
        "order_date": order_date,
        "items": items,
        "amount": amount
    }
