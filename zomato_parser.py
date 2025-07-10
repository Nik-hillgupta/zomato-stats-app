import re
import pandas as pd

def parse_email(body, received_date):
    try:
        name_match = re.search(r"Hi\s+(\w+)", body)
        name = name_match.group(1) if name_match else "N/A"

        amount_match = re.search(r"Total paid[^₹]*₹([0-9.,]+)", body)
        amount = float(amount_match.group(1).replace(",", "")) if amount_match else None

        restaurant_match = re.search(r"from\s+([A-Za-z0-9\s,&-]+)<", body)
        restaurant = restaurant_match.group(1).strip() if restaurant_match else "N/A"

        address_match = re.search(r"Address:</b><br>(.*?)<", body, re.S)
        address = re.sub(r"<.*?>", "", address_match.group(1)).strip() if address_match else "N/A"

        items_match = re.search(r"Order Details:</b><br>(.*?)<", body, re.S)
        items = re.sub(r"<.*?>", "", items_match.group(1)).strip() if items_match else "N/A"

        return {
            "name": name,
            "restaurant": restaurant,
            "restaurant_address": address,
            "order_date": received_date.date() if received_date else "N/A",
            "items": items,
            "amount": amount
        }
    except:
        return None
