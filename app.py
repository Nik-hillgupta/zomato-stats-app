import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import base64
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="Zomato Order Summary", layout="centered")
st.title("🍽️ Zomato Order Summary")
st.markdown("Get insights on your Zomato spending directly from your Gmail.")

# Load secrets
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

# 🔁 Clear session
if st.button("🔁 Force Clear Session and Retry Login"):
    st.session_state.clear()
    st.rerun()

# 🔐 Step 1: Auth
if "credentials" not in st.session_state:
    flow = Flow.from_client_config(
        client_config=CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0]
    )
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

# 📩 Gmail API client
credentials = st.session_state["credentials"]
service = build("gmail", "v1", credentials=credentials)

# ⚙️ Step 2: Fetch and parse
def get_messages(service):
    messages = []
    page_token = None
    while True:
        response = service.users().messages().list(
            userId="me",
            q="from:(noreply@zomato.com OR order@zomato.com)",
            maxResults=100,
            pageToken=page_token
        ).execute()
        messages.extend(response.get("messages", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return messages

def decode_parts(payload):
    parts = payload.get("parts", [])
    for part in parts:
        if part.get("mimeType") == "text/html":
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
        elif part.get("parts"):
            return decode_parts(part)
    return ""

def should_ignore(text):
    blacklist = ["Login Alert", "Zomato Gold", "Congratulations", "bill payment", "cancelled as requested"]
    return any(x.lower() in text.lower() for x in blacklist)

def parse_email(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    if should_ignore(text):
        return None

    restaurant = re.search(r"Thank you for ordering (?:from|at)\s+([A-Za-z &']+)", text)
    amount = re.search(r"₹\s?(\d+[\d,]*)", text) or re.search(r"Total\s+paid\s+₹\s?(\d+[\d,]*)", text)
    date = re.search(r"(\w{3}, \w{3} \d{1,2}, \d{4})", text) or re.search(r"Delivered on (\d{1,2} \w+ \d{4})", text)
    address = re.search(r"Issued on behalf of [A-Za-z &']+\s+(.+?\n(?:Bangalore|Mumbai|Delhi|Chennai|Pune).*)", text)
    customer = re.search(r"Hi\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text)

    return {
        "restaurant": restaurant.group(1).strip() if restaurant else "N/A",
        "amount": f"₹{amount.group(1)}" if amount else "N/A",
        "date": date.group(1) if date else "N/A",
        "address": address.group(1).strip() if address else "N/A",
        "customer": customer.group(1) if customer else "N/A"
    }

# 🔍 Process emails
st.info("📩 Fetching your Zomato emails...")
messages = get_messages(service)
orders = []

for msg in messages:
    raw = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
    html = decode_parts(raw["payload"])
    parsed = parse_email(html)
    if parsed:
        orders.append(parsed)

# 🧾 Results
if orders:
    st.success(f"✅ Found {len(orders)} Zomato orders.")
    st.dataframe(orders)
else:
    st.warning("No valid Zomato orders found.")
