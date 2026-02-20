import imaplib
import email
from email.header import decode_header
import os

def receive_email():
    # Configuration
    username = os.getenv("EMAIL_USER", "your_email@gmail.com")
    password = os.getenv("EMAIL_PASS", "your_app_password")
    
    # IMAP Server Settings (Example for Gmail)
    imap_server = "imap.gmail.com"

    try:
        # Connect to the server
        print(f"Connecting to {imap_server}...")
        mail = imaplib.IMAP4_SSL(imap_server)
        
        # Login
        print("Logging in...")
        mail.login(username, password)
        
        # Select the mailbox (inbox)
        mail.select("inbox")
        
        # Search for emails (e.g., all emails)
        # You can search by criteria usually: 'ALL', 'UNSEEN', 'FROM "user@example.com"'
        status, messages = mail.search(None, "ALL")
        
        # Get the list of email IDs
        email_ids = messages[0].split()
        
        # Fetch the latest email (last ID)
        if email_ids:
            latest_email_id = email_ids[-1]
            print(f"Fetching email ID: {latest_email_id.decode()}")
            
            # Fetch the email body (RFC822)
            res, msg = mail.fetch(latest_email_id, "(RFC822)")
            
            for response in msg:
                if isinstance(response, tuple):
                    # Parse bytes to message object
                    msg = email.message_from_bytes(response[1])
                    
                    # Decode email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    # Decode sender
                    from_ = msg.get("From")
                    
                    print("Subject:", subject)
                    print("From:", from_)
                    
                    # Extract body
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            
                            try:
                                body = part.get_payload(decode=True).decode()
                            except:
                                pass
                                
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                print("Body:", body)
                    else:
                        content_type = msg.get_content_type()
                        body = msg.get_payload(decode=True).decode()
                        print("Body:", body)
                        
        else:
            print("No emails found in Inbox.")

        mail.logout()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    receive_email()
