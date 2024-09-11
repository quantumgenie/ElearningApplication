import json
from channels.generic.websocket import AsyncWebsocketConsumer

# live chat comsumer handling multi-user chat communication


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'live_chat_%s' % self.room_name
        # joining coms channel
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    # handle input from WebSocket

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )
    # handle output to WebSocket

    async def chat_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))

# notification consumer handling notification broadcasting


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope["user"]
            self.group_name = f'notifications_{self.user.id}'

            # joining notification group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            print(f"WebSocket connected to group: {self.group_name}")
            await self.accept()
        except Exception as e:
            print(f"Error in connect method: {e}")

    async def disconnect(self, close_code):
        # leaving notification group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    # handle input from WebSocket

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))
    # handle output to WebSocket

    async def send_notification(self, event):
        try:
            message = event['message']
            unread_count = event.get('unread_count', 0)
            # debugging: print message to console
            print(f"Sending notification to ws: {message}")

            # sending message to WebSocket
            await self.send(text_data=json.dumps({
                'message': message,
                'unread_count': unread_count,
            }))
        except Exception as e:
            print(f"Error sending notification: {e}")
