import streamlit as st
from streamlit_oauth import OAuth2Component
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
import re
from bs4 import BeautifulSoup

# ----------------------------------
# Setup OAuth
# ----------------------------------

client_id = st.secrets["gmail"]["client_id"]
client_secret = st.secrets["gmail"]["client_secret"]
redirect_uri = st.secrets["gmail"]["redirect_uri"]

oauth2 = OAuth2Component(
    client_id=client_id,
    client_secret=client_secret,
    authorize_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
    token_endpoint="https://oauth2.googleapis.com/token",
    redirect_uri=redirect_uri,
    scopes=["https://www.googleapis.com/auth/gmail.readonly"]
)

st.title("🍽️ Zomato Order Summary")
st.markdown("Get insights on your Zomato spending directly from your Gmail.")

token = oauth2.authorize_button(
    name="google",
    icon="🌐",
    login_button_text="Login with Google",
    logout_button_text="Logout",
)

if not token:
    st.stop()

# ----------------------------------
# Setup Gmail API
# ----------------------------------

creds = Credentials(
    token=token["access_token"],
    refresh_token=token.get("refresh_token"),
    token_uri="https://oauth2.googleapis.com/token",
    client_id=client_id,
    client_secret=client_secret,
    scopes=["https://www.googleapis.com/auth/gmail.readonly"]
)

service = build("gmail", "v1", credentials=creds)

# ----------------------------------
# Fetch Emails from Zomato
# ----------------------------------

def search_zomato_emails(service):
    response = service.users().messages().list(userId='me', q='from:order@zomato.com').execute()
    return response.get('messages', [])

def fetch_email_content(service, msg_id):
    message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    headers = message['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')

    parts = message['payload'].get('parts', [])
    data = ''
    for part in parts:
        if part['mimeType'] == 'text/html':
            data = part['body'].get('data')
            break

    if not data:
        data = message['payload']['body'].get('data', '')

    decoded_body = base64.urlsafe_b64decode(data.encode('UTF-8')).decode('utf-8')
    return subject, decoded_body

def parse_email(body):
    soup = BeautifulSoup(body, 'html.parser')
    text = soup.get_text()

    restaurant = re.search(r'Order from\s+(.+?)\s+has been placed', text)
    amount = re.search(r'₹\s?([\d,]+)', text)
    date = re.search(r'Placed on\s+(\w+\s\d+,\s\d+)', text)

    return {
        "restaurant": restaurant.group(1).strip() if restaurant else None,
        "amount": amount.group(1).strip() if amount else None,
        "date": date.group(1).strip() if date else None
    }

# ----------------------------------
# Run Parser
# ----------------------------------

with st.spinner("Fetching your Zomato orders..."):
    messages = search_zomato_emails(service)
    st.success(f"Found {len(messages)} emails")

    all_orders = []
    for msg in messages[:30]:  # Limit for speed
        subject, body = fetch_email_content(service, msg['id'])
        parsed = parse_email(body)
        if parsed and parsed["restaurant"]:
            all_orders.append(parsed)

if all_orders:
    st.subheader("📦 Order Summary")
    st.dataframe(all_orders, use_container_width=True)
else:
    st.warning("No valid Zomato order emails parsed.")
