import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from gmail_service import authenticate_gmail, search_zomato_emails, fetch_email_content
from zomato_parser import parse_email
from collections import Counter
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Zomato Order Summary", layout="centered")
st.title("🍽️ Zomato Order Summary")
st.markdown("Get insights on your Zomato spending directly from your Gmail.")

# Load OAuth config
CLIENT_CONFIG = {
    "web": {
        "client_id": st.secrets["gmail"]["client_id"],
        "client_secret": st.secrets["gmail"]["client_secret"],
        "redirect_uris": [st.secrets["gmail"]["redirect_uri"]],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# 🔁 Reset session
if st.button("🔁 Force Clear Session and Retry Login"):
    st.session_state.clear()
    st.rerun()

# 🔐 OAuth flow
if "credentials" not in st.session_state:
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES, redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0])
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline", include_granted_scopes="true")
    st.markdown(f"[Click here to log in with Gmail]({auth_url})")
    code = st.query_params.get("code")
    if code:
        try:
            flow.fetch_token(code=code)
            st.session_state["credentials"] = flow.credentials
            st.rerun()
        except Exception as e:
            st.error(f"OAuth Error: {e}")
            st.stop()
    st.stop()

# 📨 Gmail API
credentials = st.session_state["credentials"]
service = build("gmail", "v1", credentials=credentials)

# 📦 Fetch
st.info("📬 Fetching your Zomato emails...")
messages = search_zomato_emails(service)
orders = []

for msg in messages:
    subject, html, received_at = fetch_email_content(service, msg)
    parsed = parse_email(html)
    if parsed:
        if parsed["order_date"] == "N/A":
            parsed["order_date"] = received_at
        orders.append(parsed)

# ✅ Display
if not orders:
    st.warning("No valid Zomato orders found.")
    st.stop()

st.success(f"✅ Found {len(orders)} Zomato orders.")

# 📊 Summary
df = pd.DataFrame(orders)
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

st.subheader("📊 Summary")

total_orders = len(df)
total_spent = df["amount"].sum()
highest_order = df.loc[df["amount"].idxmax()]
lowest_order = df.loc[df["amount"].idxmin()]

# Year-wise spend
# Convert order_date to datetime, invalid formats become NaT
df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

# Now extract year only from valid dates
df["year"] = df["order_date"].dt.year
yearly_spend = df.groupby("year")["amount"].sum().sort_index()

# Most ordered items
item_counts = Counter()
for items in df["items"]:
    for item in items:
        name = item.split(" -")[0].strip()
        item_counts[name] += 1

st.markdown(f"- **Total Orders Placed:** {total_orders}")
st.markdown(f"- **Total Amount Spent:** ₹{total_spent:,.2f}")
st.markdown(f"- **Highest Order:** ₹{highest_order['amount']} — *{', '.join(highest_order['items'])}*")
st.markdown(f"- **Lowest Order:** ₹{lowest_order['amount']} — *{', '.join(lowest_order['items'])}*")

if not yearly_spend.empty:
    st.markdown("**📆 Yearly Spend:**")
    for year, amt in yearly_spend.items():
        st.markdown(f"  - {int(year)}: ₹{amt:,.2f}")

if item_counts:
    st.markdown("**🍕 Most Ordered Items:**")
    for item, count in item_counts.most_common(5):
        st.markdown(f"  - {item}: {count} times")

# 🧾 Table
st.subheader("📋 Orders Table")
st.dataframe(df.drop(columns=["year"]), use_container_width=True)
