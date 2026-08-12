import json
from channels.generic.websocket import AsyncWebsocketConsumer
from urllib.parse import parse_qs
import jwt
from django.conf import settings
from asgiref.sync import sync_to_async
from .models import User
from .repositories.user_repository import UserRepository

class InboxConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if not token:
            await self.close()
            return

        try:
            # Decode the JWT token
            decoded_data = jwt.decode(token, settings.SIMPLE_JWT['SIGNING_KEY'], algorithms=[settings.SIMPLE_JWT['ALGORITHM']])
            user_id = decoded_data.get(settings.SIMPLE_JWT['USER_ID_CLAIM'])
            
            user = await self.get_user(user_id)
            if not user or not user.client_id:
                await self.close()
                return
                
            self.user = user
            self.client_id = str(user.client_id)
            self.room_group_name = f'inbox_{self.client_id}'

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
            
            # Send initial connection success message
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to inbox successfully',
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'role': user.role,
                    'department': user.department
                }
            }))

        except Exception as e:
            await self.close()

    @sync_to_async
    def get_user(self, user_id):
        try:
            return UserRepository.get_user(id=user_id)
        except User.DoesNotExist:
            return None

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Receive message from WebSocket and broadcast to group
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action_type = data.get('type')

            if action_type in ['typing_status', 'view_conversation', 'takeover_event', 'transfer_event', 'lock_event', 'status_change_event', 'note_event']:
                # Broadcast payload to group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'broadcast_event',
                        'event_data': data
                    }
                )
        except Exception as e:
            pass

    async def broadcast_event(self, event):
        await self.send(text_data=json.dumps(event['event_data']))

    # Receive message from room group
    async def new_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': message
        }))

class TeamChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if not token:
            await self.close()
            return

        try:
            decoded_data = jwt.decode(token, settings.SIMPLE_JWT['SIGNING_KEY'], algorithms=[settings.SIMPLE_JWT['ALGORITHM']])
            user_id = decoded_data.get(settings.SIMPLE_JWT['USER_ID_CLAIM'])
            
            user = await self.get_user(user_id)
            if not user or not user.client_id:
                await self.close()
                return
                
            self.client_id = str(user.client_id)
            self.room_group_name = f'teamchat_{self.client_id}'

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

        except Exception as e:
            await self.close()

    @sync_to_async
    def get_user(self, user_id):
        try:
            return UserRepository.get_user(id=user_id)
        except User.DoesNotExist:
            return None

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def new_team_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'new_team_message',
            'message': message
        }))

class WebRTCConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if not token:
            await self.close()
            return

        try:
            decoded_data = jwt.decode(token, settings.SIMPLE_JWT['SIGNING_KEY'], algorithms=[settings.SIMPLE_JWT['ALGORITHM']])
            user_id = decoded_data.get(settings.SIMPLE_JWT['USER_ID_CLAIM'])
            
            user = await self.get_user(user_id)
            if not user or not user.client_id:
                await self.close()
                return
                
            self.user = user
            self.client_id = str(user.client_id)
            
            self.workspace_group = f'webrtc_workspace_{self.client_id}'
            self.personal_group = f'webrtc_user_{user.email.lower()}' if user.email else f'webrtc_user_{user.username.lower()}'

            await self.channel_layer.group_add(self.workspace_group, self.channel_name)
            await self.channel_layer.group_add(self.personal_group, self.channel_name)

            await self.accept()

        except Exception as e:
            await self.close()

    @sync_to_async
    def get_user(self, user_id):
        try:
            return UserRepository.get_user(id=user_id)
        except User.DoesNotExist:
            return None

    async def disconnect(self, close_code):
        if hasattr(self, 'workspace_group'):
            await self.channel_layer.group_discard(self.workspace_group, self.channel_name)
        if hasattr(self, 'personal_group'):
            await self.channel_layer.group_discard(self.personal_group, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get('type')
            
            target_group = None
            if msg_type in ['offer', 'answer', 'ice_candidate', 'call_ended']:
                recipient = data.get('recipient', '').lower()
                target_group = f'webrtc_user_{recipient}'
            
            if target_group:
                await self.channel_layer.group_send(
                    target_group,
                    {
                        'type': 'webrtc_message',
                        'message': data
                    }
                )
        except Exception as e:
            pass

    async def webrtc_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))
