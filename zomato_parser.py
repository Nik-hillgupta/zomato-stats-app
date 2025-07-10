import re
from bs4 import BeautifulSoup

def parse_email(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    text = re.sub(r"[ \t]+", " ", text)  # Normalize spaces

    # Early filter: skip unrelated Zomato emails
    if any(x in text for x in ["Login Alert", "Zomato Gold", "Congratulations", "Your order has been cancelled", "Your bill payment"]):
        return None

    # Extract amount
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

    # Extract customer name
    name_match = re.search(r"Hi\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text)
    customer_name = name_match.group(1).strip() if name_match else None

    # Restaurant name
    restaurant = None
    m = re.search(r"Thank you for ordering (?:from|food online on Zomato,)\s+([^\n]+)", text)
    if m:
        restaurant = m.group(1).strip()

    # Restaurant address
    restaurant_address = None
    address_match = re.search(r"Issued on behalf of\s+" + re.escape(restaurant) + r"\s+(.+?Bangalore.*?)\n", text, re.IGNORECASE) if restaurant else None
    if address_match:
        restaurant_address = address_match.group(1).strip()

    # Order date
    date_match = re.search(r"(\w{3}, \w{3} \d{1,2}, \d{4})", text)
    order_date = date_match.group(1) if date_match else None

    # Fallback order date
    if not order_date:
        fallback = re.search(r"Delivered on (\d{1,2} \w+ \d{4})", text)
        if fallback:
            order_date = fallback.group(1)

    # Extract items
    lines = text.split("\n")
    item_lines = [line.strip() for line in lines if re.search(r"\d+ ?[xX] ", line) or re.search(r"₹", line)]

    items = []
    for line in item_lines:
        item_match = re.search(r"(\d+ ?[xX])? ?(.+?) ?-? ?₹\s?([\d.]+)", line)
        if item_match:
            qty = item_match.group(1) or "1X"
            name = item_match.group(2).strip()
            price = item_match.group(3).strip()
            items.append(f"{qty} {name} - ₹{price}")
        else:
            # Fallback for items without ₹ price format
            loose_match = re.match(r"(.*Cake|.*Puri|.*Pizza|.*Roll|.*Bhature|.*Burger|.*Paratha|.*Biryani|.*Kebab)", line, re.IGNORECASE)
            if loose_match:
                items.append(loose_match.group(1).strip())

    return {
        "name": customer_name or "N/A",
        "restaurant": restaurant or "N/A",
        "restaurant_address": restaurant_address or "N/A",
        "order_date": order_date or "N/A",
        "items": items or ["N/A"],
        "amount": amount
    }