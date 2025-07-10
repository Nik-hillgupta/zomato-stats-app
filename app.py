import streamlit as st
import pandas as pd
from gmail_service import authenticate_gmail, search_zomato_emails, fetch_email_content
from zomato_parser import parse_email

st.set_page_config(page_title="Zomato Order Summary", page_icon="🍽️")
st.title("🍽️ Zomato Order Summary")
st.write("This tool reads your Zomato order history from your Gmail account.")

if st.button("Login with Gmail"):
    try:
        service = authenticate_gmail()
        st.success("✅ Logged in via Gmail!")

        with st.spinner("Fetching Zomato emails..."):
            messages = search_zomato_emails(service, "from:noreply@zomato.com OR from:order@zomato.com")

        all_orders = []
        no_amount_emails = []

        for idx, msg_id in enumerate(messages, 1):
            subject, body = fetch_email_content(service, msg_id)
            parsed = parse_email(body)

            if parsed:
                if parsed["amount"] is None:
                    no_amount_emails.append(f"Email #{idx}: {subject}")
                else:
                    all_orders.append(parsed)

        # Show summary
        st.markdown("## 📊 Summary")
        st.write(f"📬 Total Zomato emails: **{len(messages)}**")
        st.write(f"✅ Amount extracted from: **{len(all_orders)}** emails")
        st.write(f"❌ No amount found in: **{len(no_amount_emails)}** emails")

        total_spent = sum(order["amount"] for order in all_orders if order["amount"] is not None)
        st.write(f"💰 Total amount spent: ₹**{total_spent:,.2f}**")

        if no_amount_emails:
            with st.expander("📌 Emails without amount"):
                for line in no_amount_emails:
                    st.markdown(f"- {line}")

        # Show full table
        if all_orders:
            df = pd.DataFrame(all_orders)
            st.markdown("## 🧾 Detailed Orders")
            st.dataframe(df)

    except Exception as e:
        st.error(f"❌ Failed: {e}")
