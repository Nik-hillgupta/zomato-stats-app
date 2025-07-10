from gmail_service import authenticate_gmail, search_zomato_emails, fetch_email_content
from zomato_parser import parse_email

def main():
    print("✅ Gmail API authenticated successfully!")
    print("🔄 Processing emails (this may take a few seconds)...\n")

    service = authenticate_gmail()
    
    # ✅ Combined query to include all Zomato order formats
    messages = search_zomato_emails(service, "from:noreply@zomato.com OR from:order@zomato.com")

    all_orders = []
    no_amount_emails = []

    for idx, msg_id in enumerate(messages, 1):
        subject, body = fetch_email_content(service, msg_id)
        parsed = parse_email(body)

        if parsed:
            if parsed["amount"] is None:
                no_amount_emails.append(f"Email #{idx}: {subject}")
            else:
                all_orders.append(parsed)

    # 📊 Summary
    print("\n📊 Summary")
    print(f"📬 Total Zomato emails: {len(messages)}")
    print(f"✅ Amount extracted from: {len(all_orders)} emails")
    print(f"❌ No amount found in: {len(no_amount_emails)} emails")
    total_spent = sum(order["amount"] for order in all_orders if order["amount"] is not None)
    print(f"💰 Total amount spent: ₹{total_spent:,.2f}")

    # 📌 Emails without amount
    if no_amount_emails:
        print("\n📌 Emails without amounts:")
        for line in no_amount_emails:
            print(f"– {line}")

    # 🧾 Print each order
    print("\n🧾 Detailed Orders:")
    for i, order in enumerate(all_orders, 1):
        print(f"\n#{i}")
        print(f"👤 Name: {order['name']}")
        print(f"🍽️ Restaurant: {order['restaurant']}")
        print(f"📍 Address: {order['restaurant_address']}")
        print(f"📅 Date: {order['order_date']}")
        print(f"🧾 Items: {', '.join(order['items'])}")
        print(f"💵 Amount: ₹{order['amount']:.2f}")

if __name__ == "__main__":
    main()