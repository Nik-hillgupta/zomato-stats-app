import base64
import pandas as pd
from googleapiclient.discovery import build

def authenticate_gmail():
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    import os

    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

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

    parts = payload.get("parts", [])
    body = ""
    for part in parts:
        if part.get("mimeType") == "text/html":
            body = part["body"].get("data", "")
            break
    else:
        body = payload.get("body", {}).get("data", "")

    if body:
        body = base64.urlsafe_b64decode(body + "==").decode("utf-8", errors="ignore")

    internal_date = msg.get("internalDate")
    received_date = pd.to_datetime(internal_date, unit="ms") if internal_date else None

    return subject, body, received_date
