import streamlit as st
from gmail_service import authenticate_gmail, search_zomato_emails, fetch_email_content
from zomato_parser import parse_email

# Page config
st.set_page_config(page_title="Zomato Order Summary", page_icon="🍽️", layout="centered")

# Title
st.title("🍽️ Zomato Order Summary")
st.markdown("Get insights on your Zomato spending directly from your Gmail.")

# Step 1: Authenticate Gmail
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    if st.button("🔐 Login with Google"):
        try:
            service = authenticate_gmail()
            st.session_state.service = service
            st.session_state.authenticated = True
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")
    st.stop()

# Step 2: Search for Zomato Emails
st.info("✅ Logged in successfully! Looking for Zomato orders...")

service = st.session_state.service
messages = search_zomato_emails(service, "from:noreply@zomato.com OR from:order@zomato.com")

if not messages:
    st.warning("We couldn’t find any Zomato order emails in your Gmail. Try logging in with your Zomato-linked email.")
    st.session_state.authenticated = False
    st.button("🔁 Try logging in again", on_click=lambda: st.session_state.clear())
    st.stop()

# Step 3: Ask for phone number
phone = st.text_input("📞 Enter your phone number to personalize your dashboard")

if phone:
    st.success("Processing your Zomato orders... please wait.")
    all_orders = []
    total_spent = 0
    no_amount_emails = []

    for idx, msg_id in enumerate(messages, 1):
        subject, body = fetch_email_content(service, msg_id)
        parsed = parse_email(body)
        if parsed:
            if parsed["amount"] is None:
                no_amount_emails.append(subject)
            else:
                all_orders.append(parsed)
                total_spent += parsed["amount"]

    # Summary
    st.subheader("📊 Summary")
    st.metric("Total Orders", len(all_orders))
    st.metric("Total Amount Spent", f"₹{total_spent:,.2f}")

    # Year-wise breakdown
    st.subheader("📅 Orders by Year")
    from collections import Counter
    import re

    years = [re.search(r"\d{4}", o["order_date"]).group() for o in all_orders if re.search(r"\d{4}", o["order_date"])]
    counts = Counter(years)
    for year, count in sorted(counts.items()):
        st.write(f"{year}: {count} orders")

    # Order details
    with st.expander("🧾 View All Orders"):
        for i, order in enumerate(all_orders, 1):
            st.markdown(f"### #{i}. {order['restaurant']}")
            st.write(f"👤 Name: {order['name']}")
            st.write(f"📍 Address: {order['restaurant_address']}")
            st.write(f"📅 Date: {order['order_date']}")
            st.write(f"🧾 Items: {', '.join(order['items'])}")
            st.write(f"💵 Amount: ₹{order['amount']:.2f}")
            st.markdown("---")

    # Share
    st.subheader("📤 Share Your Summary")
    st.write("Feature coming soon: generate image or link to share with friends!")
