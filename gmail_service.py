import base64
import pandas as pd
from googleapiclient.discovery import build

def search_zomato_emails(service):
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
    return [msg["id"] for msg in messages]

def fetch_email_content(service, msg_id):
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    payload = msg.get("payload", {})
    headers = payload.get("headers", [])
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")

    parts = payload.get("parts", [])
    body = ""
    if parts:
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
