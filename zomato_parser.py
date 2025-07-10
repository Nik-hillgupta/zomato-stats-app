import re
from bs4 import BeautifulSoup

blacklist = ["Login Alert", "Zomato Gold", "Congratulations", "bill payment", "cancelled as requested"]

def should_ignore(text):
    return any(bad.lower() in text.lower() for bad in blacklist)

def parse_email(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    text = re.sub(r"[ \t]+", " ", text)

    if should_ignore(text):
        return None

    # Amount
    amount = None
    m = re.search(r"₹\s?([\d,]+)", text)
    if m:
        amount = f"₹{m.group(1)}"

    # Customer
    name_match = re.search(r"Hi\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text)
    name = name_match.group(1) if name_match else "N/A"

    # Restaurant
    rest_match = re.search(r"Thank you for ordering (?:from|at)\s+([A-Za-z &']+)", text)
    restaurant = rest_match.group(1).strip() if rest_match else "N/A"

    # Address
    addr_match = re.search(r"Issued on behalf of [^\n]+\s+(.+?\n(?:Bangalore|Mumbai|Delhi|Chennai|Pune).*)", text)
    address = addr_match.group(1).strip() if addr_match else "N/A"

    # Date
    date = re.search(r"(\w{3}, \w{3} \d{1,2}, \d{4})", text) or re.search(r"Delivered on (\d{1,2} \w+ \d{4})", text)
    order_date = date.group(1) if date else "N/A"

    return {
        "restaurant": restaurant,
        "amount": amount or "N/A",
        "date": order_date,
        "address": address,
        "customer": name
    }
