import os
import pickle
import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email import message_from_bytes

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)

def search_zomato_emails(service, query):
    results = service.users().messages().list(userId="me", q=query, maxResults=500).execute()
    return [msg["id"] for msg in results.get("messages", [])]

def fetch_email_content(service, msg_id):
    message = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    headers = message["payload"].get("headers", [])
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
    def extract_html(payload):
        if payload.get("mimeType") == "text/html":
            body_data = payload.get("body", {}).get("data")
            if body_data:
                return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")
        for part in payload.get("parts", []):
            html = extract_html(part)
            if html:
                return html
        return ""
    body = extract_html(message["payload"])
    return subject, body
