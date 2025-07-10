import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from gmail_service import authenticate_gmail, search_zomato_emails, fetch_email_content
from zomato_parser import parse_email

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

# 🔁 Reset button
if st.button("🔁 Force Clear Session and Retry Login"):
    st.session_state.clear()
    st.rerun()

# 🔐 Auth flow
if "credentials" not in st.session_state:
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES, redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0])
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline", include_granted_scopes=True)
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
st.info("📩 Fetching your Zomato emails...")
messages = search_zomato_emails(service)
orders = []

for idx, msg_id in enumerate(messages, 1):
    subject, html = fetch_email_content(service, msg_id)
    parsed = parse_email(html)
    if parsed:
        orders.append(parsed)

# ✅ Display
if orders:
    st.success(f"✅ Found {len(orders)} Zomato orders.")
    st.dataframe(orders)
else:
    st.warning("No valid Zomato orders found.")
