import asyncio
import websockets
import json
import os

class RealtimeClient:
    def __init__(self, api_key, url='wss://api.openai.com/v1/realtime'):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.url = url
        self.session = {}
        self.websocket = None
        self.event_handlers = {}

    async def connect(self):
        """
        Establishes a WebSocket connection to the OpenAI Realtime API.
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        print(f"Attempting to connect to WebSocket URL: {self.url}")
        try:
            self.websocket = await websockets.connect(self.url, extra_headers=headers)
            print("[RealtimeClient] Connected to OpenAI Realtime API.")
            asyncio.create_task(self.listen())
        except Exception as e:
            print(f"Failed to connect to WebSocket: {e}")
            raise

    async def listen(self):
        """
        Listens for incoming messages from the WebSocket and dispatches events.
        """
        try:
            async for message in self.websocket:
                event = json.loads(message)
                await self.handle_event(event)
        except websockets.exceptions.ConnectionClosed:
            print("[RealtimeClient] Connection closed.")
            # Implement reconnection logic if necessary

    async def handle_event(self, event):
        """
        Handles incoming events by invoking the appropriate event handler.
        """
        event_type = event.get('type')
        handler = self.event_handlers.get(event_type)
        if handler:
            await handler(event)
        else:
            print(f"[RealtimeClient] Unhandled event type: {event_type}")

    async def send_user_message(self, text):
        """
        Sends a user message to the Realtime API.
        """
        message = {
            'type': 'user_message',
            'content': text
        }
        await self.websocket.send(json.dumps(message))
        print(f"[RealtimeClient] Sent user message: {text}")

    def on(self, event_type, handler):
        """
        Registers an event handler for a specific event type.
        """
        self.event_handlers[event_type] = handler

    async def update_session(self, **kwargs):
        """
        Updates the session parameters.
        """
        self.session.update(kwargs)
        update_message = {
            'type': 'update_session',
            'session': self.session
        }
        await self.websocket.send(json.dumps(update_message))
        print(f"[RealtimeClient] Updated session with: {kwargs}")

    async def disconnect(self):
        """
        Closes the WebSocket connection.
        """
        await self.websocket.close()
        print("[RealtimeClient] Disconnected from OpenAI Realtime API.") 