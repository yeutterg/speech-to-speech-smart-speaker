import asyncio
import websockets
import json
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('RealtimeClient')

class RealtimeClient:
    def __init__(self, api_key=None, url='wss://api.openai.com/v1/realtime'):
        self.api_key = api_key
        print("API KEY:", self.api_key)
        self.url = url
        self.session = {}
        self.websocket = None
        self.event_handlers = {}
        # Register event handlers
        self.on('error', self.handle_error)
        self.on('message', self.handle_messages)  # Ensure you have a message handler as well

    def on(self, event_type, handler):
        """
        Registers an event handler for a specific event type.
        """
        self.event_handlers[event_type] = handler

    async def connect(self):
        """Establish WebSocket connection with the Realtime API."""
        url = f"{self.url}?model=gpt-4o-realtime-preview-2024-10-01"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        self.websocket = await websockets.connect(url, extra_headers=headers)
        await self.update_session()

    async def update_session(self):
        """Update session configuration."""
        config = {
            "modalities": ["text", "audio"],
            "instructions": "You are a helpful assistant",
            "voice": "alloy",
            "temperature": 0.8,
            # Add any other necessary parameters here
        }
        event = {
            "type": "session.update",
            "session": config
        }
        await self.websocket.send(json.dumps(event))

    async def handle_messages(self):
        """Handle incoming messages from the WebSocket."""
        try:
            async for message in self.websocket:
                event = json.loads(message)
                event_type = event.get("type")

                if event_type == "error":
                    print(f"Error: {event['error']}")
                elif event_type == "response.created":
                    # Handle response creation
                    pass
                # Add more event handling as needed
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
        except Exception as e:
            print(f"Error in message handling: {str(e)}")

    async def handle_error(self, error):
        """Handle errors from the WebSocket."""
        print(f"Error: {error}")

    async def close(self):
        """Close the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()

# Usage
async def main():
    client = RealtimeClient(api_key=os.getenv("OPENAI_API_KEY"))
    await client.connect()
    await client.handle_messages()

# Run the client
asyncio.run(main())