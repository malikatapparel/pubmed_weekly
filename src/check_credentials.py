# Set-up environment
import argparse
from email.message import EmailMessage
import smtplib

# Get credentials from environment variables
smtp_server = "smtp.gmail.com"
smtp_port = 587
parser = argparse.ArgumentParser(description='PubMed Weekly Recommendation System')
parser.add_argument('--smtp_user', required=True, help='SMTP username for sending emails')
parser.add_argument('--smtp_pass', required=True, help='SMTP password for sending emails')
parser.add_argument('--receiver', required=True, help='Email address to receive the recommendations')
args = parser.parse_args()

smtp_user = args.smtp_user
smtp_pass = args.smtp_pass
receiver = args.receiver


# Send email
msg = EmailMessage()
msg["Subject"] = "Credentials check for PubMed Weekly Recommendation System"
msg["From"] = smtp_user
msg["To"] = receiver
msg.set_content("Congrats! Your credentials are working and you can send emails.")

# send first
with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(smtp_user, smtp_pass)
    server.send_message(msg)
    print(f"Email sent to {receiver}.")