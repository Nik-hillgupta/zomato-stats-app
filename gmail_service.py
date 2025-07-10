import base64
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
    
    # Get subject
    headers = msg["payload"].get("headers", [])
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
    
    # Get received date
    internal_date = int(msg.get("internalDate", 0))
    received_date = pd.to_datetime(internal_date, unit="ms") if internal_date else None

    # Decode HTML body
    def extract_html(payload):
        if payload.get("mimeType") == "text/html":
            data = payload.get("body", {}).get("data", "")
            return base64.urlsafe_b64decode(data.encode()).decode("utf-8", errors="ignore")
        for part in payload.get("parts", []):
            html = extract_html(part)
            if html:
                return html
        return ""
    
    body = extract_html(msg["payload"])
    return subject, body, received_date
