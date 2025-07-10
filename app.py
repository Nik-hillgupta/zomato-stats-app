import streamlit as st
import pandas as pd
import json
from gmail_service import authenticate_gmail, search_zomato_emails, fetch_email_content
from zomato_parser import parse_email
from summary import generate_summary
from storage import save_user_summary

st.set_page_config(page_title="Zomato Order Summary", page_icon="🍽️", layout="centered")
st.title("🍽️ Zomato Order Summary")
st.write("Get insights on your Zomato spending directly from your Gmail.")
st.markdown("**Log in with the email linked to your Zomato account.**")

if st.button("Click here to log in with Gmail"):
    if "credentials" in st.session_state:
        del st.session_state["credentials"]
    st.experimental_rerun()

if "credentials" not in st.session_state:
    creds = authenticate_gmail()
    st.session_state["credentials"] = creds
    st.experimental_rerun()

service = st.session_state["credentials"]

st.markdown("### 👤 Enter your details")
name = st.text_input("Your Name")
phone = st.text_input("Phone Number")
submit = st.button("Enter")

if submit:
    if not name or not (phone.isdigit() and len(phone) >= 8):
        st.warning("Please enter a valid name and phone number.")
        st.stop()

    st.info("📩 Fetching your Zomato orders...")
    messages = search_zomato_emails(service)

    all_orders = []
    for idx, msg_id in enumerate(messages):
        subject, body, date = fetch_email_content(service, msg_id)
        parsed = parse_email(body)
        if parsed and parsed["amount"]:
            parsed["order_date"] = date
            parsed["name"] = name
            parsed["phone"] = phone
            all_orders.append(parsed)

    if not all_orders:
        st.warning("No valid Zomato orders found.")
        st.stop()

    df = pd.DataFrame(all_orders)
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    summary_html = generate_summary(df)
    save_user_summary(name, phone, summary_html)

    with open("log_summary.jsonl", "a") as f:
        f.write(json.dumps({
            "name": name,
            "phone": phone,
            "total_orders": len(df),
            "total_amount": df["amount"].sum()
        }) + "\n")

    st.success(f"✅ Found {len(df)} valid Zomato orders.")
    st.markdown("### 📊 Order Summary")
    st.markdown(summary_html, unsafe_allow_html=True)
    st.markdown("### 📦 Order Details")
    st.dataframe(df)
