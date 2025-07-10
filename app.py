import streamlit as st
import pandas as pd
from gmail_service import authenticate_gmail, search_zomato_emails, fetch_email_content
from zomato_parser import parse_email
from summary import generate_summary
import json

st.set_page_config(page_title="Zomato Order Summary", page_icon="🍽️", layout="centered")
st.title("🍽️ Zomato Order Summary")
st.write("Get insights on your Zomato spending directly from your Gmail.")

# Force clear session
if st.button("Click here to log in with Gmail"):
    if "credentials" in st.session_state:
        del st.session_state["credentials"]
    st.experimental_rerun()

# Force login
if "credentials" not in st.session_state:
    st.markdown("**Log in with the email linked to your Zomato account.**")
    creds = authenticate_gmail()
    st.session_state["credentials"] = creds
    st.experimental_rerun()

service = st.session_state["credentials"]

# Ask for Name and Phone
st.markdown("### 👤 Enter your details")
name = st.text_input("Your Name")
phone = st.text_input("Phone Number")

if name and (phone.isdigit() and len(phone) >= 8):
    st.info("📩 Fetching your Zomato orders...")
    messages = search_zomato_emails(service)

    data = []
    for idx, msg_id in enumerate(messages):
        subject, body, received_date = fetch_email_content(service, msg_id)
        parsed = parse_email(body)
        if parsed and parsed["amount"]:
            parsed["order_date"] = received_date
            parsed["name"] = name
            parsed["phone"] = phone
            data.append(parsed)

        if idx % 50 == 0:
            st.write(f"Parsed {idx}/{len(messages)} emails...")

    if not data:
        st.warning("No valid Zomato orders found.")
        st.stop()

    df = pd.DataFrame(data)
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    # Save to logs
    summary_log = {
        "name": name,
        "phone": phone,
        "total_orders": len(df),
        "total_amount": df['amount'].sum(),
    }
    with open("log_summary.jsonl", "a") as f:
        f.write(json.dumps(summary_log) + "\n")

    st.success(f"✅ Found {len(df)} valid Zomato orders.")
    st.markdown("### 📊 Order Summary")
    summary_text = generate_summary(df)
    st.markdown(summary_text, unsafe_allow_html=True)

    st.markdown("### 📦 Order Details")
    st.dataframe(df)
else:
    st.warning("Please enter valid name and phone number.")
