import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import base64
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="Zomato Order Summary", layout="centered")
st.title("🍽️ Zomato Order Summary")
st.markdown("Get insights on your Zomato spending directly from your Gmail.")

# Load client secrets from Streamlit secrets
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

# 👉 Add session reset button
if st.button("🔁 Force Clear Session and Retry Login"):
    st.session_state.clear()
    st.experimental_rerun()

# Step 1: Authenticate user
if "credentials" not in st.session_state:
    flow = Flow.from_client_config(
        client_config=CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0]
    )

    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline",
        include_granted_scopes=True
    )

    st.markdown(f"[Click here to log in with Gmail]({auth_url})")
    code = st.query_params.get("code")

    if code:
        try:
            flow.fetch_token(code=code[0])
            credentials = flow.credentials
            st.session_state["credentials"] = credentials
            st.experimental_rerun()
        except Exception as e:
            st.error(f"OAuth Error: {e}")
            st.stop()
    st.stop()

# Step 2: Gmail API client
credentials = st.session_state["credentials"]
service = build("gmail", "v1", credentials=credentials)

# Step 3: Fetch Zomato emails
def get_zomato_emails(service):
    result = service.users().messages().list(
        userId="me", q="from:order@zomato.com", maxResults=50
    ).execute()
    return result.get("messages", [])

# Step 4: Parse email content
def parse_email_content(content):
    try:
        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text()

        restaurant = re.search(r"(?i)from\s+(.+?)\s+on", text)
        amount = re.search(r"₹\s?(\d+[\d,]*)", text)
        date_match = re.search(r"(?i)(?:delivered|placed|ordered).+?on\s+(\d{1,2} \w+ \d{4})", text)

        return {
            "restaurant": restaurant.group(1).strip() if restaurant else "N/A",
            "amount": f"₹{amount.group(1)}" if amount else "N/A",
            "date": date_match.group(1) if date_match else "N/A"
        }
    except Exception:
        return None

# Step 5: Display orders
st.markdown("🔄 Fetching your Zomato emails...")
emails = get_zomato_emails(service)

orders = []
for msg in emails:
    raw = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
    parts = raw["payload"].get("parts", [])
    for part in parts:
        if part["mimeType"] == "text/html":
            data = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
            parsed = parse_email_content(data)
            if parsed:
                orders.append(parsed)
            break

if orders:
    st.success(f"✅ Found {len(orders)} Zomato orders.")
    st.dataframe(orders)
else:
    st.warning("No Zomato orders found.")
