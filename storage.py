import os
from datetime import datetime

def save_user_summary(name, phone, summary):
    os.makedirs("summaries", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"summaries/{name}_{phone}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Name: {name}\n")
        f.write(f"Phone: {phone}\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        f.write(summary)
