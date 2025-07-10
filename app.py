import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import base64
from bs4 import BeautifulSoup
from zomato_parser import parse_email
import pandas as pd

# Streamlit config
st.set_page_config(page_title="Zomato Order Summary", layout="centered")
st.title("🍽️ Zomato Order Summary")
st.markdown("Get insights on your Zomato spending directly from your Gmail.")

# OAuth credentials from secrets
CLIENT_CONFIG = {
    "web": {
        "client_id": st.secrets["gmail"]["client_id"],
        "client_secret": st.secrets["gmail"]["client_secret"],
        "redirect_uris": [st.secrets["gmail"]["redirect_uri"]],
        "auth_uri": st.secrets["gmail"]["auth_uri"],
        "token_uri": st.secrets["gmail"]["token_uri"]
    }
}

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Step 1: Authenticate
if "credentials" not in st.session_state:
    flow = Flow.from_client_config(
        client_config=CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0]
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    st.markdown(f"[Click here to log in with Gmail]({auth_url})")
    st.info("Please log in with Gmail to continue.")
    code = st.experimental_get_query_params().get("code")
    if code:
        flow.fetch_token(code=code[0])
        credentials = flow.credentials
        st.session_state["credentials"] = credentials
        st.experimental_rerun()
    st.stop()

# Step 2: Gmail API client
credentials = st.session_state["credentials"]
service = build("gmail", "v1", credentials=credentials)

# Step 3: Fetch and parse emails
def get_zomato_emails(service):
    result = service.users().messages().list(userId="me", q="from:order@zomato.com", maxResults=100).execute()
    return result.get("messages", [])

def get_email_body(service, msg_id):
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    payload = msg.get("payload", {})
    parts = payload.get("parts", [])
    for part in parts:
        if part["mimeType"] == "text/html":
            data = part["body"]["data"]
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return ""

st.markdown("🔄 Fetching your Zomato emails...")
messages = get_zomato_emails(service)

orders = []
for msg in messages:
    body = get_email_body(service, msg["id"])
    parsed = parse_email(body)
    if parsed:
        orders.append(parsed)

if orders:
    st.success(f"✅ Found {len(orders)} Zomato orders.")
    df = pd.DataFrame(orders)
    st.dataframe(df)
else:
    st.warning("No Zomato orders found.")
