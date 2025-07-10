import base64
import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import streamlit as st
import json
from tempfile import NamedTemporaryFile

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def authenticate_gmail():
    creds = None

    # Convert secrets to dict and save to temp credentials.json
    secrets_dict = dict(st.secrets["gmail"])  # Ensure JSON-serializable
    with NamedTemporaryFile("w+", delete=False, suffix=".json") as temp:
        json.dump(secrets_dict, temp)
        temp.flush()
        flow = InstalledAppFlow.from_client_secrets_file(temp.name, SCOPES)
        creds = flow.run_local_server(port=0)

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
        # Add padding to base64 if missing
        missing_padding = len(body) % 4
        if missing_padding:
            body += "=" * (4 - missing_padding)
        body = base64.urlsafe_b64decode(body).decode("utf-8", errors="ignore")

    internal_date = msg.get("internalDate")
    received_date = pd.to_datetime(internal_date, unit="ms") if internal_date else None

    return subject, body, received_date
