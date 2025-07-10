import base64
import json
import pandas as pd
import streamlit as st
from tempfile import NamedTemporaryFile
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def authenticate_gmail():
    if "gmail_token" in st.session_state:
        creds = Credentials.from_authorized_user_info(st.session_state["gmail_token"], SCOPES)
        return build("gmail", "v1", credentials=creds)

    secrets_dict = dict(st.secrets["gmail"])
    with NamedTemporaryFile("w+", delete=False, suffix=".json") as temp:
        client_config = {
            "web": {
                "client_id": secrets_dict["client_id"],
                "client_secret": secrets_dict["client_secret"],
                "auth_uri": secrets_dict["auth_uri"],
                "token_uri": secrets_dict["token_uri"],
                "redirect_uris": [secrets_dict["redirect_uri"]]
            }
        }
        json.dump(client_config, temp)
        temp.flush()

        flow = Flow.from_client_secrets_file(
            temp.name,
            scopes=SCOPES,
            redirect_uri=secrets_dict["redirect_uri"]
        )

    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline", include_granted_scopes="true")
    st.session_state["gmail_flow"] = flow
    st.session_state["auth_url"] = auth_url
    return None


def complete_auth(code):
    flow = st.session_state.get("gmail_flow")
    if not flow:
        raise RuntimeError("OAuth flow not initialized. Please restart login.")

    flow.fetch_token(code=code)
    creds = flow.credentials
    st.session_state["gmail_token"] = json.loads(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def search_zomato_emails(service):
    results = []
    page_token = None
    while True:
        response = service.users().messages().list(
            userId="me",
            q="from:(noreply@zomato.com OR order@zomato.com)",
            maxResults=100,
            pageToken=page_token
        ).execute()
        results.extend([msg["id"] for msg in response.get("messages", [])])
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return results


def fetch_email_content(service, msg_id):
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    payload = msg.get("payload", {})
    headers = payload.get("headers", [])
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")

    body = ""
    parts = payload.get("parts", [])
    for part in parts:
        if part.get("mimeType") == "text/html":
            body = part["body"].get("data", "")
            break
    else:
        body = payload.get("body", {}).get("data", "")

    if body:
        missing_padding = len(body) % 4
        if missing_padding:
            body += "=" * (4 - missing_padding)
        body = base64.urlsafe_b64decode(body).decode("utf-8", errors="ignore")

    internal_date = msg.get("internalDate")
    received_date = pd.to_datetime(internal_date, unit="ms") if internal_date else None

    return subject, body, received_date
