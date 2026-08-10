import base64
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
from api.models import Message, Contact, EmailMessage, EmailAccount

def send_gmail_message(client, to_address, body, subject="New Message"):
    """
    Sends an email using the Gmail API on behalf of the client.
    """
    if not client.gmail_enabled or not client.gmail_config:
        raise Exception("Gmail is not enabled or configured for this client.")
        
    config = client.gmail_config
    
    # Reconstruct credentials object
    creds = Credentials(
        token=config.get('token'),
        refresh_token=config.get('refresh_token'),
        token_uri=config.get('token_uri'),
        client_id=config.get('client_id'),
        client_secret=config.get('client_secret'),
        scopes=config.get('scopes')
    )
    
    # Check if we have credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            # Update the stored token if it was refreshed
            client.gmail_config['token'] = creds.token
            client.save()
        else:
            raise Exception("Invalid Gmail credentials. Please reconnect Gmail.")

    try:
        service = build('gmail', 'v1', credentials=creds)
        
        message = EmailMessage()
        message.set_content(body)
        
        message['To'] = to_address
        message['From'] = config.get('email_address', '')
        message['Subject'] = subject

        # Encode the message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        create_message = {
            'raw': encoded_message
        }
        
        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        
        return {
            "success": True,
            "message_id": send_message.get('id')
        }
    except Exception as e:
        print(f"Failed to send Gmail message: {str(e)}")
        raise Exception(f"Gmail API Error: {str(e)}")

def sync_incoming_gmails(client):
    """
    Fetches unread emails from the connected Gmail account,
    saves them as Messages, and removes the UNREAD label.
    """
    if not client.gmail_enabled or not client.gmail_config:
        return 0

    config = client.gmail_config
    creds = Credentials(
        token=config.get('token'),
        refresh_token=config.get('refresh_token'),
        token_uri=config.get('token_uri'),
        client_id=config.get('client_id'),
        client_secret=config.get('client_secret'),
        scopes=config.get('scopes')
    )
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            client.gmail_config['token'] = creds.token
            client.save()
        else:
            return 0

    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # Get unread messages in inbox
        results = service.users().messages().list(userId='me', q="is:unread label:inbox").execute()
        messages = results.get('messages', [])
        
        if not messages:
            return 0
            
        new_messages_count = 0
            
        for msg in messages:
            msg_id = msg['id']
            full_msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            
            headers = full_msg['payload'].get('headers', [])
            subject = "No Subject"
            sender = "Unknown"
            
            for header in headers:
                if header['name'].lower() == 'subject':
                    subject = header['value']
                elif header['name'].lower() == 'from':
                    sender = header['value']
                    
            # Extract plain text body
            body = ""
            if 'parts' in full_msg['payload']:
                for part in full_msg['payload']['parts']:
                    if part.get('mimeType') == 'text/plain':
                        data = part.get('body', {}).get('data')
                        if data:
                            body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif 'body' in full_msg['payload'] and 'data' in full_msg['payload']['body']:
                data = full_msg['payload']['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                
            if not body:
                body = "[No readable text content]"

            # Clean sender email from "Name <email>" format
            import re
            email_match = re.search(r'<([^>]+)>', sender)
            if email_match:
                sender_email = email_match.group(1)
            else:
                sender_email = sender
                
            # Create Contact if doesn't exist
            contact, _ = Contact.objects.get_or_create(
                client=client,
                platform_id=sender_email,
                defaults={
                    'name': sender.split('<')[0].strip(),
                    'email': sender_email,
                    'stage': 'NEW'
                }
            )

            # Ensure EmailAccount exists
            account, _ = EmailAccount.objects.get_or_create(
                client=client,
                provider='gmail',
                email_address=config.get('email_address', ''),
                defaults={'display_name': config.get('email_address', '')}
            )

            # Check if this message was already synced
            if not Message.objects.filter(client=client, channel='GMAIL', metadata__gmail_id=msg_id).exists():
                Message.objects.create(
                    client=client,
                    channel='GMAIL',
                    from_address=sender_email,
                    to_address=config.get('email_address', ''),
                    body=f"Subject: {subject}\n\n{body}",
                    message_type='INCOMING',
                    status='DELIVERED',
                    metadata={'gmail_id': msg_id}
                )
                
            # Check if already synced in EmailMessage
            if not EmailMessage.objects.filter(client=client, account=account, metadata__gmail_id=msg_id).exists():
                EmailMessage.objects.create(
                    client=client,
                    account=account,
                    folder='inbox',
                    sender_email=sender_email,
                    sender_name=contact.name,
                    to_recipients=[config.get('email_address', '')],
                    subject=subject,
                    body_text=body,
                    body_html=body,
                    is_read=False,
                    status='delivered',
                    priority='normal',
                    metadata={'gmail_id': msg_id}
                )
                new_messages_count += 1
                
                # Remove UNREAD label
                service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()

        return new_messages_count
    except Exception as e:
        print(f"Gmail Sync Error: {str(e)}")
        return 0
