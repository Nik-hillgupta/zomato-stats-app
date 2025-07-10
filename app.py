import streamlit as st
from streamlit_oauth import OAuth2Component
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from gmail_service import search_zomato_emails, fetch_email_content
from zomato_parser import parse_email
from collections import Counter
import re

# App config
st.set_page_config(page_title="Zomato Order Summary", page_icon="🍽️", layout="centered")
st.title("🍽️ Zomato Order Summary")
st.markdown("Get insights on your Zomato spending directly from your Gmail.")

# ✅ OAuth2 Setup (from Streamlit secrets)
client_id = st.secrets["gmail"]["client_id"]
client_secret = st.secrets["gmail"]["client_secret"]
redirect_uri = st.secrets["gmail"]["redirect_uri"]

# 👉 Debug print
st.write("🔁 Redirect URI from secrets:", redirect_uri)

oauth2 = OAuth2Component(
    client_id=client_id,
    client_secret=client_secret,
    authorize_endpoint="https://accounts.google.com/o/oauth2/auth",
    token_endpoint="https://oauth2.googleapis.com/token",
    redirect_uri=redirect_uri,
    scopes=["https://www.googleapis.com/auth/gmail.readonly"]
)

# Step 1: Google Login
token = oauth2.authorize_button(
    name="google",
    icon="🔐",
    login_button_text="Login with Google",
    logout_button_text="Logout",
)

if not token:
    st.stop()

# Step 2: Authenticate Gmail API
try:
    creds = Credentials(
        token=token["access_token"],
        refresh_token=token.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"]
    )
    service = build('gmail', 'v1', credentials=creds)
except Exception as e:
    st.error(f"❌ Gmail Authentication failed: {e}")
    st.stop()

# Step 3: Search Zomato emails
st.info("✅ Logged in successfully! Looking for Zomato orders...")
messages = search_zomato_emails(service, "from:noreply@zomato.com OR from:order@zomato.com")

if not messages:
    st.warning("We couldn’t find any Zomato order emails in your Gmail. Try logging in with your Zomato-linked email.")
    st.button("🔁 Try again", on_click=lambda: st.session_state.clear())
    st.stop()

# Step 4: Ask for phone number
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

    st.subheader("📤 Share Your Summary")
    st.write("Feature coming soon: generate image or link to share with friends!")
