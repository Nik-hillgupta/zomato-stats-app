import streamlit as st
import pandas as pd
from gmail_service import authenticate_gmail, search_zomato_emails, fetch_email_content
from zomato_parser import parse_email
from summary import compute_summary

st.set_page_config(page_title="Zomato Order Summary", layout="wide")
st.title("🍽️ Zomato Order Summary")
st.write("Get insights on your Zomato spending directly from your Gmail.")

if st.button("🔁 Force Clear Session and Retry Login"):
    st.cache_data.clear()
    st.rerun()

st.info("📩 Fetching your Zomato emails...")
service = authenticate_gmail()
messages = search_zomato_emails(service, "from:noreply@zomato.com OR from:order@zomato.com")

orders = []
for msg_id in messages:
    subject, body = fetch_email_content(service, msg_id)
    parsed = parse_email(body)
    if parsed:
        orders.append(parsed)

if not orders:
    st.warning("No valid Zomato orders found.")
    st.stop()

df = pd.DataFrame(orders)
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

st.success(f"✅ Found {len(df)} Zomato orders.")

# Display raw table
st.dataframe(df)

# Show summary
st.subheader("📊 Summary")
with st.spinner("Computing summary..."):
    try:
        summary_lines = compute_summary(df)
        for line in summary_lines:
            st.write(line)
    except Exception as e:
        st.error(f"Failed to compute summary: {e}")
