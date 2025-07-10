import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
import google.auth.transport.requests
import base64
import re
from bs4 import BeautifulSoup
import os

st.set_page_config(page_title="Zomato Order Summary", layout="centered")
st.title("🍽️ Zomato Order Summary")
st.markdown("Get insights on your Zomato spending directly from your Gmail.")

# --- Safety check for required secrets ---
required_keys = ["client_id", "client_secret", "redirect_uri"]
if not all(k in st.secrets.get("gmail", {}) for k in required_keys):
    st.error("Missing Gmail OAuth credentials in secrets.toml.")
    st.stop()

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

# --- Force session reset ---
if st.button("🔁 Force Clear Session and Retry Login"):
    st.session_state.clear()
    st.rerun()

# --- Step 1: Authenticate ---
if "credentials" not in st.session_state:
    try:
        flow = Flow.from_client_config(
            client_config=CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0]
        )

        auth_url, _ = flow.authorization_url(
            prompt="consent",
            access_type="offline",
            include_granted_scopes="true"  # MUST be string, not boolean
        )

        st.markdown(f"[Click here to log in with Gmail]({auth_url})")

        code = st.query_params.get("code")
        if code:
            if isinstance(code, list):
                code = code[0]

            try:
                flow.fetch_token(code=code)
                credentials = flow.credentials
                st.session_state["credentials"] = credentials
                st.rerun()
            except Exception as e:
                st.error(f"OAuth Error: {e}")
                st.stop()

        st.stop()
    except Exception as e:
        st.error(f"Auth Initialization Error: {e}")
        st.stop()

# --- Step 2: Build Gmail Client ---
try:
    credentials = st.session_state["credentials"]
    service = build("gmail", "v1", credentials=credentials)
except RefreshError:
    st.error("Session expired. Please log in again.")
    del st.session_state["credentials"]
    st.rerun()
except Exception as e:
    st.error(f"Failed to connect to Gmail API: {e}")
    st.stop()

# --- Step 3: Fetch Zomato emails ---
def get_zomato_emails(service):
    try:
        result = service.users().messages().list(
            userId="me", q="from:order@zomato.com", maxResults=50
        ).execute()
        return result.get("messages", [])
    except Exception as e:
        st.error(f"Error fetching emails: {e}")
        return []

# --- Step 4: Parse email content ---
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

# --- Step 5: Display results ---
st.markdown("🔄 Fetching your Zomato emails...")

emails = get_zomato_emails(service)
orders = []

for msg in emails:
    try:
        raw = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        payload = raw.get("payload", {})
        parts = payload.get("parts", [])

        found_html = False
        for part in parts:
            if part.get("mimeType") == "text/html":
                data = part["body"].get("data")
                if data:
                    try:
                        decoded = base64.urlsafe_b64decode(data).decode("utf-8")
                        parsed = parse_email_content(decoded)
                        if parsed:
                            orders.append(parsed)
                    except Exception:
                        continue
                found_html = True
                break

        # Fallback if no parts
        if not parts and payload.get("body", {}).get("data"):
            try:
                decoded = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
                parsed = parse_email_content(decoded)
                if parsed:
                    orders.append(parsed)
            except Exception:
                continue

    except Exception:
        continue

# --- Step 6: Show results ---
if orders:
    st.success(f"✅ Found {len(orders)} Zomato orders.")
    st.dataframe(orders)
else:
    st.warning("No Zomato orders found or failed to parse them.")
