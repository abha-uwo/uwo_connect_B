from django.core.mail import send_mail as django_send_mail
from django.conf import settings
from .gmail_service import send_gmail_message
from .meta_webhook_service import MetaWebhookService
import logging

logger = logging.getLogger(__name__)

class SalesDocumentNotificationService:
    @staticmethod
    def send_document_email(document, recipient, subject, message_body):
        """
        Sends the sales document details or link via email.
        Uses connected Gmail API credentials if active, falling back to standard django SMTP.
        """
        client = document.client
        if client and client.gmail_enabled and client.gmail_config:
            try:
                send_gmail_message(
                    client=client,
                    to_address=recipient,
                    body=message_body,
                    subject=subject
                )
                logger.info(f"[Gmail Dispatch Success] Sent document {document.document_number} to {recipient}")
                return True
            except Exception as e:
                logger.error(f"[Gmail Dispatch Failed] Reverting to Django send_mail fallback: {e}")
        
        # Standard SMTP Fallback
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@uwo24.com')
        django_send_mail(
            subject=subject,
            message=message_body,
            from_email=from_email,
            recipient_list=[recipient],
            fail_silently=False
        )
        logger.info(f"[SMTP Fallback Success] Sent document {document.document_number} to {recipient}")
        return True

    @staticmethod
    def send_document_whatsapp(document, to_number, message_body):
        """
        Sends quotation link via Meta WhatsApp API Integration.
        """
        client = document.client
        if client and client.whatsapp_phone_number_id and client.whatsapp_access_token:
            try:
                MetaWebhookService.send_whatsapp_message(
                    client=client,
                    to_number=to_number,
                    text_body=message_body,
                    phone_number_id=client.whatsapp_phone_number_id
                )
                logger.info(f"[WhatsApp Dispatch Success] Sent message to {to_number}")
                return True
            except Exception as e:
                logger.error(f"[WhatsApp Dispatch Failed] {e}")
                raise Exception(f"WhatsApp API Error: {str(e)}")
        else:
            raise Exception("WhatsApp integration is not enabled or configured for this client.")
