import os
from mimetypes import guess_type
import smtplib
from email.message import EmailMessage

def send_email(recipient, attachments):
    SMTP_HOST = "smtp.gmail.com"  # e.g. Gmail
    SMTP_PORT = 587  # STARTTLS port
    SMTP_USER = "selectionsupplier@gmail.com"  # your email/login
    SMTP_PASS = "nyap xjff pkyu ntpa"  # your SMTP/app password

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = recipient
    msg["Subject"] = "Report of supplier ranking"
    msg.set_content("Plain text body here.")
    # Optional HTML version:
    msg.add_alternative("""\
        <!doctype html>
        <html>
          <body>
            <p>Dear Recipient,</p>
            <p>
              Please find attached the <b>supplier ranking analysis results</b>, 
              including outcomes <b>before and after perturbation</b>. 
              These results were generated using advanced <i>Gen AI</i> techniques.
            </p>
            <p>Kind regards,<br>
               <b>Selection Supplier Team</b></p>
          </body>
        </html>
        """, subtype="html")
    for filepath in attachments:
        if not os.path.isfile(filepath):
            print(f"Warning: file not found - {filepath}")
            continue

        mime_type, _ = guess_type(filepath)
        maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)

        with open(filepath, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(filepath)
            msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


