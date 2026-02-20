import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email():
    # Configuration
    # You can hardcode these or use environment variables
    sender_email = os.getenv("EMAIL_USER", "your_email@gmail.com")
    password = os.getenv("EMAIL_PASS", "your_app_password")
    receiver_email = "recipient_email@example.com"
    
    # SMTP Server Settings (Example for Gmail)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # Create the email content
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Test Email from Python"

    body = "This is a test email sent from a Python script using SMTP."
    message.attach(MIMEText(body, "plain"))

    try:
        # Connect to the server
        print(f"Connecting to {smtp_server}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        
        # Login
        print("Logging in...")
        server.login(sender_email, password)
        
        # Send email
        print("Sending email...")
        server.sendmail(sender_email, receiver_email, message.as_string())
        
        print("Email sent successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.quit()

if __name__ == "__main__":
    send_email()
