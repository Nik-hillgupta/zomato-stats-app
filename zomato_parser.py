from bs4 import BeautifulSoup
import re

def parse_email(body):
    soup = BeautifulSoup(body, "html.parser")
    text = soup.get_text(separator="\n")

    restaurant = None
    if "from" in text.lower():
        match = re.search(r'from\s+(.*?)\n', text, re.IGNORECASE)
        if match:
            restaurant = match.group(1).strip()

    address_match = re.search(r"(?:delivery|delivered) to[:\s\n]+(.+?)\n", text, re.IGNORECASE)
    address = address_match.group(1).strip() if address_match else None

    item_match = re.search(r"(\d+)\s?x\s?(.*?)(?:\n|Total|₹)", text, re.IGNORECASE)
    items = item_match.group(0).strip() if item_match else "N/A"

    amount = None
    amount_patterns = [
        r"Total paid.*?₹\s?(\d+[\d,.]*)",
        r"Amount paid.*?₹\s?(\d+[\d,.]*)",
        r"Paid:.*?₹\s?(\d+[\d,.]*)",
        r"Total:.*?₹\s?(\d+[\d,.]*)",
        r"₹\s?(\d+[\d,.]*)\s?\(paid\)",
    ]
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                amount = float(match.group(1).replace(",", ""))
                break
            except ValueError:
                continue

    name_match = re.search(r"Hi (.*?),", text)
    name = name_match.group(1).strip() if name_match else "N/A"

    return {
        "name": name,
        "restaurant": restaurant or "N/A",
        "restaurant_address": address or "N/A",
        "items": items,
        "amount": amount,
    }
