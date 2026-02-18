# For production, you would set these as environment variables and read them like this:
import argparse
from email.message import EmailMessage
parser = argparse.ArgumentParser(description='Check credentials for PubMed Weekly Recommendation System')
parser.add_argument('--SMTP_USER', required=True, help='SMTP username for sending emails')
parser.add_argument('--SMTP_PASS', required=True, help='SMTP password for sending emails')
parser.add_argument('--SMTP_RECEIVER', required=True, help='Email address to receive the recommendations')
parser.add_argument('--PUBMED_API_KEY', required=True, help='API key for accessing PubMed data')
args = parser.parse_args()


# Send email
msg = EmailMessage()
msg["Subject"] = "Test"
msg["From"] = smtp_user
msg["To"] = receiver
msg.set_content("Hi")

# send first
with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(smtp_user, smtp_pass)
    server.send_message(msg)
    print(f"Email sent to {receiver} with {n_selected} papers recommended.")

# only if send succeeded, update seen items
seen_pmids.update(top_pmids)
with open('seen_pmids.json', 'w') as f:
    json.dump(sorted(seen_pmids), f)