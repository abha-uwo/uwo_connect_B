from ..models import Message, SupportMessage, TeamMessage

class MessageRepository:
    @staticmethod
    def filter_messages(**kwargs):
        return Message.objects.filter(**kwargs)

    @staticmethod
    def get_message(id):
        return Message.objects.filter(id=id).first()
        
    @staticmethod
    def create_message(**kwargs):
        msg = Message.objects.create(**kwargs)
        from ..models import Contact
        from django.utils import timezone
        
        # Touch the contact's updated_at so it rises to the top of the inbox list
        client = kwargs.get('client')
        platform_id = msg.from_address if msg.message_type == 'INCOMING' else msg.to_address
        if client and platform_id:
            Contact.objects.filter(client=client, platform_id=platform_id).update(updated_at=timezone.now())
            
        return msg

class SupportMessageRepository:
    @staticmethod
    def filter_messages(**kwargs):
        return SupportMessage.objects.filter(**kwargs)
        
    @staticmethod
    def create_message(**kwargs):
        return SupportMessage.objects.create(**kwargs)

class TeamMessageRepository:
    @staticmethod
    def filter_messages(**kwargs):
        return TeamMessage.objects.filter(**kwargs)
        
    @staticmethod
    def create_message(**kwargs):
        return TeamMessage.objects.create(**kwargs)

    @staticmethod
    def get_all_messages():
        return Message.objects.all()

    @staticmethod
    def get_all():
        return Message.objects.all()
