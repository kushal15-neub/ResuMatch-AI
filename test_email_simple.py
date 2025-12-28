#!/usr/bin/env python
"""
Simple email test script
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_smtp():
    """Test Gmail SMTP connection"""
    # Email configuration
    sender_email = "kushalpantha@gmail.com"
    app_password = "uwox bxni dcnx bjil"
    recipient_email = "kushalpanthadas44@gmail.com"
    
    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "Test Email from ResuMatch AI"
    
    body = "This is a test email to verify Gmail SMTP is working."
    message.attach(MIMEText(body, "plain"))
    
    try:
        # Create SMTP session
        print("Connecting to Gmail SMTP...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        
        print("Authenticating...")
        server.login(sender_email, app_password)
        
        print("Sending email...")
        text = message.as_string()
        server.sendmail(sender_email, recipient_email, text)
        
        print("✅ Email sent successfully!")
        server.quit()
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed. Your Gmail app password might be expired or incorrect.")
        print("Please generate a new app password from your Google Account settings.")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_gmail_smtp()
