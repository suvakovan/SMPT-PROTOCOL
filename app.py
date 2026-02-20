from flask import Flask, render_template, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate, make_msgid
from email.header import decode_header
import imaplib
import os
import json
from datetime import datetime

app = Flask(__name__)

# ============================================================
# FIXED SENDER CONFIGURATION
# The sender email is fixed. Users only enter the recipient.
# Configure these via environment variables or .env file.
# ============================================================
FIXED_SENDER_EMAIL = os.getenv("SMTP_SENDER_EMAIL", "")
FIXED_SENDER_PASSWORD = os.getenv("SMTP_SENDER_PASSWORD", "")
FIXED_SENDER_NAME = os.getenv("SMTP_SENDER_NAME", "SMTP Protocol Mailer")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")

# Email history storage (in-memory for demo, use DB in production)
email_history = []


@app.route('/')
def home():
    return render_template('index.html')


# Repository configuration
REPO_URL = os.getenv("REPO_URL", "https://github.com/suvakovan/SMPT-PROTOCOL")

@app.route('/config', methods=['GET'])
def get_config():
    """Return the fixed sender email (masked) so UI can display it."""
    if FIXED_SENDER_EMAIL:
        parts = FIXED_SENDER_EMAIL.split('@')
        masked = parts[0][:3] + '***@' + parts[1] if len(parts) == 2 else '***'
    else:
        masked = 'Not Configured'
    return jsonify({
        'sender_display': masked,
        'sender_name': FIXED_SENDER_NAME,
        'is_configured': bool(FIXED_SENDER_EMAIL and FIXED_SENDER_PASSWORD),
        'repo_url': REPO_URL
    })


@app.route('/send', methods=['POST'])
def send_email():
    data = request.json
    receiver_email = data.get('receiver_email', '').strip()
    subject = data.get('subject', '').strip()
    body = data.get('body', '').strip()
    priority = data.get('priority', 'normal')  # high, normal, low

    # Validate required fields
    if not all([receiver_email, subject, body]):
        return jsonify({
            'status': 'error',
            'message': 'Recipient email, subject, and message are all required.'
        }), 400

    # Check if sender is configured
    if not FIXED_SENDER_EMAIL or not FIXED_SENDER_PASSWORD:
        return jsonify({
            'status': 'error',
            'message': 'Sender email is not configured. Set SMTP_SENDER_EMAIL and SMTP_SENDER_PASSWORD environment variables.'
        }), 500

    # ============================================================
    # BUILD THE EMAIL WITH PROPER HEADERS FOR INBOX DELIVERY
    # These headers help ensure the email lands in the inbox
    # and not in spam.
    # ============================================================
    message = MIMEMultipart("alternative")
    message["From"] = formataddr((FIXED_SENDER_NAME, FIXED_SENDER_EMAIL))
    message["To"] = receiver_email
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain=FIXED_SENDER_EMAIL.split('@')[-1])
    message["X-Mailer"] = "SMTP-Protocol-Mailer/3.0"
    message["Reply-To"] = FIXED_SENDER_EMAIL
    message["Auto-Submitted"] = "auto-generated"
    message["X-Auto-Response-Suppress"] = "All"
    message["Precedence"] = "bulk"

    # Set priority headers
    if priority == 'high':
        message["X-Priority"] = "1"
        message["Importance"] = "High"
    elif priority == 'low':
        message["X-Priority"] = "5"
        message["Importance"] = "Low"
    else:
        message["X-Priority"] = "3"
        message["Importance"] = "Normal"

    # Attach both plain text and HTML versions for better inbox delivery
    text_part = MIMEText(body, "plain", "utf-8")
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="border-bottom: 3px solid #6366f1; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="color: #6366f1; margin: 0;">{subject}</h2>
            </div>
            <div style="white-space: pre-wrap;">{body}</div>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
            <p style="font-size: 12px; color: #9ca3af;">
                Sent via SMTP Protocol Mailer
            </p>
        </div>
    </body>
    </html>
    """
    html_part = MIMEText(html_body, "html", "utf-8")
    message.attach(text_part)
    message.attach(html_part)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(FIXED_SENDER_EMAIL, FIXED_SENDER_PASSWORD)
        server.sendmail(FIXED_SENDER_EMAIL, receiver_email, message.as_string())
        server.quit()

        # Save to history
        email_record = {
            'id': len(email_history) + 1,
            'to': receiver_email,
            'subject': subject,
            'body': body[:100] + ('...' if len(body) > 100 else ''),
            'priority': priority,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'sent'
        }
        email_history.insert(0, email_record)

        return jsonify({
            'status': 'success',
            'message': f'Email sent successfully to {receiver_email}!',
            'record': email_record
        })

    except smtplib.SMTPAuthenticationError:
        return jsonify({
            'status': 'error',
            'message': 'Authentication Failed. Ensure you are using a valid App Password for Gmail.'
        }), 401
    except smtplib.SMTPRecipientsRefused:
        return jsonify({
            'status': 'error',
            'message': f'Recipient address rejected: {receiver_email}'
        }), 400
    except smtplib.SMTPException as e:
        return jsonify({
            'status': 'error',
            'message': f'SMTP Error: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }), 500


@app.route('/history', methods=['GET'])
def get_history():
    """Return recent email history."""
    return jsonify({'history': email_history[:20]})


@app.route('/receive', methods=['GET'])
def fetch_emails():
    """Fetch recent emails from IMAP inbox."""
    if not FIXED_SENDER_EMAIL or not FIXED_SENDER_PASSWORD:
        return jsonify({'status': 'error', 'message': 'Sender credentials not configured.'}), 500

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(FIXED_SENDER_EMAIL, FIXED_SENDER_PASSWORD)
        mail.select("inbox")
        
        # Search for recent emails
        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        
        latest_emails = []
        # Get last 10 emails
        for i in range(min(10, len(email_ids))):
            latest_id = email_ids[-(i+1)]
            res, msg_data = mail.fetch(latest_id, "(RFC822)")
            
            for response in msg_data:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])
                    
                    # Decode subject
                    subj_header = msg["Subject"]
                    if subj_header:
                        subject, encoding = decode_header(subj_header)[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                    else:
                        subject = "(No Subject)"
                    
                    # Decode sender
                    from_ = msg.get("From", "Unknown")
                    date = msg.get("Date", "Unknown")
                    
                    # Get snippet
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode()
                                    break
                                except:
                                    continue
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode()
                        except:
                            body = "(Encrypted or Binary content)"
                    
                    latest_emails.append({
                        'id': latest_id.decode(),
                        'from': from_,
                        'subject': subject,
                        'date': date,
                        'snippet': body[:120] + ('...' if len(body) > 120 else '')
                    })
        
        mail.logout()
        return jsonify({'status': 'success', 'emails': latest_emails})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/send-multiple', methods=['POST'])
def send_multiple():
    """Send the same email to multiple recipients."""
    data = request.json
    recipients = data.get('recipients', [])
    subject = data.get('subject', '').strip()
    body = data.get('body', '').strip()

    if not all([recipients, subject, body]):
        return jsonify({
            'status': 'error',
            'message': 'Recipients, subject, and message are all required.'
        }), 400

    if not FIXED_SENDER_EMAIL or not FIXED_SENDER_PASSWORD:
        return jsonify({
            'status': 'error',
            'message': 'Sender email is not configured.'
        }), 500

    results = []
    for recipient in recipients:
        recipient = recipient.strip()
        if not recipient:
            continue

        message = MIMEMultipart("alternative")
        message["From"] = formataddr((FIXED_SENDER_NAME, FIXED_SENDER_EMAIL))
        message["To"] = recipient
        message["Subject"] = subject
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid(domain=FIXED_SENDER_EMAIL.split('@')[-1])

        text_part = MIMEText(body, "plain", "utf-8")
        message.attach(text_part)

        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(FIXED_SENDER_EMAIL, FIXED_SENDER_PASSWORD)
            server.sendmail(FIXED_SENDER_EMAIL, recipient, message.as_string())
            server.quit()
            results.append({'email': recipient, 'status': 'sent'})
        except Exception as e:
            results.append({'email': recipient, 'status': 'failed', 'error': str(e)})

    return jsonify({'status': 'success', 'results': results})


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  SMTP PROTOCOL MAILER v2.0")
    print("=" * 60)
    if FIXED_SENDER_EMAIL:
        print(f"  Sender: {FIXED_SENDER_EMAIL}")
    else:
        print("  ⚠ WARNING: No sender email configured!")
        print("  Set environment variables:")
        print("    SMTP_SENDER_EMAIL=your_email@gmail.com")
        print("    SMTP_SENDER_PASSWORD=your_app_password")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
