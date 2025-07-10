import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import pandas as pd
from gmail_service import search_zomato_emails, fetch_email_content
from zomato_parser import parse_email
from summary import generate_summary

st.set_page_config(page_title="Zomato Order Summary", layout="centered")
st.title("🍽️ Zomato Order Summary")
st.markdown("Get insights on your Zomato spending directly from your Gmail.")

# --- Secrets ---
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

# --- Session Reset ---
if st.button("🔁 Force Clear Session and Retry Login"):
    st.session_state.clear()
    st.rerun()

# --- Step 1: OAuth ---
if "credentials" not in st.session_state:
    flow = Flow.from_client_config(
        client_config=CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0]
    )
    # ✅ Correct boolean value here
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline",
        include_granted_scopes='true'
    )
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

# --- Step 2: Gmail Client ---
credentials = st.session_state["credentials"]
service = build("gmail", "v1", credentials=credentials)

# --- Step 3: Process Emails ---
st.info("📩 Fetching your Zomato orders...")

messages = search_zomato_emails(service)
orders = []

progress = st.progress(0)
for i, msg_id in enumerate(messages):
    subject, body, received_date = fetch_email_content(service, msg_id)
    parsed = parse_email(body, received_date)
    if parsed:
        orders.append(parsed)
    progress.progress((i + 1) / len(messages))

if not orders:
    st.warning("No valid Zomato orders found.")
    st.stop()

# --- Step 4: Display Orders + Summary ---
df = pd.DataFrame(orders)
st.success(f"✅ Found {len(df)} valid Zomato orders.")
st.dataframe(df)

# --- Step 5: Show Dashboard Summary ---
st.markdown("## 📊 Order Summary")
summary_text = generate_summary(df)
st.markdown(summary_text)
