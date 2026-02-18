import os
import reprlib


smtp_user = os.getenv("SMTP_USER", "NOT SET")
smtp_pass = os.getenv("SMTP_PASS", "NOT SET")

print(f"SMTP_USER repr: {reprlib.repr(smtp_user)}")
print(f"SMTP_PASS repr: {reprlib.repr(smtp_pass)}")
print(f"SMTP_USER length: {len(smtp_user)}")
print(f"SMTP_PASS length: {len(smtp_pass)}")
print(f"SMTP_USER bytes: {smtp_user.encode('utf-8')}")
print(f"SMTP_PASS bytes: {smtp_pass.encode('utf-8')}")