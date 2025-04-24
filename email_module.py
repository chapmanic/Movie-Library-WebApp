import smtplib
import os
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email_templates import welcome_email_html

# Load dotenv
load_dotenv()

# port 465 (SSL) 0r 587 (TLSS)
email_server = os.getenv("EMAIL_SERVER_ADDRESS")
email_server_port = os.getenv("EMAIL_SERVER_PORT")
host_email_password = os.getenv("HOST_EMAIL_PASSWORD")
sender_email = os.getenv("ADMIN_EMAIL_ADDRESS")
class Email:
    def send_welcome_email(self, recipient):
        """" Used to send a welcome """
        try:
            # Create MSG container
            msg = MIMEMultipart('alternative')
            msg["Subject"] = "Welcome to AccessMyCare!"
            msg["From"] = sender_email
            msg["To"] = recipient
            
            # Create body content & Record MIME type alongside content
            html = welcome_email_html
            part = MIMEText(html, "html")
            # Attached MSG to container
            msg.attach(part)
            
            with smtplib.SMTP(email_server, email_server_port) as connection:
                connection.starttls()
                connection.login(user=sender_email, password=host_email_password)
                connection.sendmail(from_addr=sender_email, 
                                    to_addrs=recipient, 
                                    msg=msg.as_string())
        except smtplib.SMTPException as e:
            print(f"Email Failed due to: {e}")
 