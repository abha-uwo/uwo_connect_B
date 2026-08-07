import requests
import datetime
from ..models import Campaign, Contact
from ..repositories.campaign_repository import CampaignRepository
from ..repositories.contact_repository import ContactRepository

class CampaignService:
    @staticmethod
    def process_campaign(campaign_id):
        try:
            campaign = CampaignRepository.get_campaign(id=campaign_id)
            client = campaign.client
            template = campaign.template
            
            token = client.whatsapp_access_token
            
            # Determine audience
            if campaign.audience_filter == 'ALL':
                contacts = ContactRepository.filter_contacts(client=client)
            else:
                contacts = ContactRepository.filter_contacts(client=client, stage=campaign.audience_filter)

            contact_list = list(contacts)
            campaign.total_recipients = len(contact_list)
            campaign.total_queued = len(contact_list)
            campaign.failed_recipients = []
            campaign.save()

            for contact in contact_list:
                name = contact.name or f"Contact #{contact.id}"
                phone = contact.phone_number or ""

                if not phone:
                    campaign.total_failed += 1
                    campaign.failed_recipients.append({
                        "id": str(contact.id),
                        "name": name,
                        "phone": "N/A",
                        "platform": "WhatsApp",
                        "reason": "Missing Phone Number",
                        "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "retry_count": 0,
                        "status": "FAILED"
                    })
                    campaign.save()
                    continue

                # Prepare payload (Template or Text message)
                if template:
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": phone,
                        "type": "template",
                        "template": {
                            "name": template.name,
                            "language": {
                                "code": template.language
                            }
                        }
                    }
                else:
                    msg_text = campaign.message_body or "Hello from UWOConnect!"
                    cust_name = contact.name or "Customer"
                    first_name = cust_name.split()[0] if cust_name else "Customer"
                    msg_text = msg_text.replace("{{first_name}}", first_name)\
                                       .replace("{{name}}", cust_name)\
                                       .replace("{{phone}}", phone)\
                                       .replace("{{email}}", getattr(contact, 'email', '') or '')\
                                       .replace("{{company}}", getattr(client, 'business_name', '') or 'UWOConnect')

                    payload = {
                        "messaging_product": "whatsapp",
                        "to": phone,
                        "type": "text",
                        "text": {
                            "preview_url": True,
                            "body": msg_text
                        }
                    }

                try:
                    from ..integrations.meta_integration import MetaIntegration
                    if token and client.whatsapp_phone_number_id:
                        res = MetaIntegration.send_whatsapp_message(client.whatsapp_phone_number_id, token, payload)
                        if res.status_code in [200, 201]:
                            campaign.total_sent += 1
                            campaign.total_delivered += 1
                        else:
                            campaign.total_failed += 1
                            reason = "Platform Error"
                            try:
                                err_data = res.json()
                                reason = err_data.get("error", {}).get("message", f"HTTP {res.status_code}")
                            except Exception:
                                pass

                            campaign.failed_recipients.append({
                                "id": str(contact.id),
                                "name": name,
                                "phone": phone,
                                "platform": "WhatsApp",
                                "reason": reason,
                                "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                "retry_count": 0,
                                "status": "FAILED"
                            })
                    else:
                        campaign.total_failed += 1
                        campaign.failed_recipients.append({
                            "id": str(contact.id),
                            "name": name,
                            "phone": phone,
                            "platform": "WhatsApp",
                            "reason": "WhatsApp Credentials Missing",
                            "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "retry_count": 0,
                            "status": "FAILED"
                        })
                except Exception as e:
                    campaign.total_failed += 1
                    campaign.failed_recipients.append({
                        "id": str(contact.id),
                        "name": name,
                        "phone": phone,
                        "platform": "WhatsApp",
                        "reason": str(e),
                        "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "retry_count": 0,
                        "status": "FAILED"
                    })

                campaign.total_queued = max(0, campaign.total_queued - 1)
                campaign.save()

            campaign.status = 'COMPLETED'
            campaign.save()
        except Exception as e:
            print(f"Error processing campaign: {str(e)}")
            try:
                campaign = CampaignRepository.get_campaign(id=campaign_id)
                campaign.status = 'FAILED'
                campaign.save()
            except Campaign.DoesNotExist:
                pass

    @staticmethod
    def retry_failed_recipients(campaign_id, contact_ids=None):
        try:
            campaign = CampaignRepository.get_campaign(id=campaign_id)
            client = campaign.client
            token = client.whatsapp_access_token
            template = campaign.template

            failed_items = campaign.failed_recipients or []
            new_failed_items = []
            
            for item in failed_items:
                if contact_ids and item.get("id") not in contact_ids:
                    new_failed_items.append(item)
                    continue

                phone = item.get("phone")
                if not phone or phone == "N/A" or not token or not client.whatsapp_phone_number_id:
                    item["retry_count"] = item.get("retry_count", 0) + 1
                    new_failed_items.append(item)
                    continue

                if template:
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": phone,
                        "type": "template",
                        "template": {"name": template.name, "language": {"code": template.language}}
                    }
                else:
                    cust_name = item.get("name") or "Customer"
                    first_name = cust_name.split()[0] if cust_name else "Customer"
                    msg_text = (campaign.message_body or "Hello!").replace("{{first_name}}", first_name)\
                                                                .replace("{{name}}", cust_name)\
                                                                .replace("{{phone}}", phone)\
                                                                .replace("{{company}}", getattr(client, 'business_name', '') or 'UWOConnect')
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": phone,
                        "type": "text",
                        "text": {"body": msg_text}
                    }

                try:
                    from ..integrations.meta_integration import MetaIntegration
                    res = MetaIntegration.send_whatsapp_message(client.whatsapp_phone_number_id, token, payload)
                    if res.status_code in [200, 201]:
                        campaign.total_sent += 1
                        campaign.total_delivered += 1
                        if campaign.total_failed > 0:
                            campaign.total_failed -= 1
                    else:
                        item["retry_count"] = item.get("retry_count", 0) + 1
                        item["time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                        new_failed_items.append(item)
                except Exception:
                    item["retry_count"] = item.get("retry_count", 0) + 1
                    new_failed_items.append(item)

            campaign.failed_recipients = new_failed_items
            campaign.save()
            return True
        except Exception as e:
            print(f"Error retrying campaign failed recipients: {e}")
            return False
