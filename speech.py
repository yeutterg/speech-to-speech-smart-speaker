import openai
import os
import asyncio
import time
from functions import get_current_weather, control_lights, control_spotify
from realtime_client import RealtimeClient  # Import the RealtimeClient

system_prompt = "You are an intelligent assistant that helps control smart home devices."
model = "gpt-4o-realtime-preview-2024-10-01"

class SpeechHandler:
    def __init__(self):
        """
        Initializes the SpeechHandler with necessary configurations.
        """
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.realtime_client = RealtimeClient(api_key=openai.api_key)
        asyncio.create_task(self.initialize_realtime())

    async def initialize_realtime(self):
        """
        Initializes the RealtimeClient and sets up event handlers.
        """
        await self.realtime_client.connect()
        self.realtime_client.on('conversation.updated', self.on_conversation_updated)
        self.realtime_client.on('conversation.item.appended', self.on_item_appended)
        self.realtime_client.on('conversation.item.completed', self.on_item_completed)
        # Add more event handlers as needed

    def handle_speech(self):
        """
        Handles the speech processing tasks.
        This method is now synchronous and schedules the asynchronous processing.
        """
        asyncio.create_task(self.process_speech())

    async def process_speech(self):
        """
        Orchestrates the speech processing flow.
        """
        # Capture audio input
        audio_input = self.capture_audio()

        # Convert audio input to text using OpenAI Whisper
        user_message = await self.transcribe_audio(audio_input)

        # Send message via RealtimeClient
        await self.realtime_client.send_user_message(user_message)

        # Further processing is handled via event callbacks

    def capture_audio(self):
        """
        Captures audio input from the user.
        Implement this method based on your hardware specifications.
        """
        # Placeholder implementation
        print("[SPEECH] Capturing audio...")
        time.sleep(2)  # Simulate audio capture delay
        return "Simulated audio data"

    async def transcribe_audio(self, audio_data):
        """
        Transcribes audio data to text using OpenAI Whisper.
        Implement this method based on your requirements.
        """
        print("[SPEECH] Transcribing audio...")
        await asyncio.sleep(1)  # Simulate transcription delay
        return "Simulated transcribed text"

    async def on_conversation_updated(self, event):
        """
        Handles the 'conversation.updated' event from RealtimeClient.
        """
        item = event.get('item')
        delta = event.get('delta')
        print(f"[SPEECH] Conversation updated: {item}")
        if item['type'] == 'message':
            response = item.get('content', '')
            await self.process_response(response)

    async def on_item_appended(self, event):
        """
        Handles the 'conversation.item.appended' event.
        """
        item = event.get('item')
        print(f"[SPEECH] New item appended: {item}")
        # Implement any additional logic if necessary

    async def on_item_completed(self, event):
        """
        Handles the 'conversation.item.completed' event.
        """
        item = event.get('item')
        print(f"[SPEECH] Item completed: {item}")
        # Implement any additional logic if necessary

    async def process_response(self, response):
        """
        Processes the response from OpenAI and triggers appropriate functions.
        """
        print(f"[SPEECH] Processing response: {response}")
        response_lower = response.lower()
        if "weather" in response_lower:
            weather_info = await asyncio.to_thread(get_current_weather)
            self.play_audio(weather_info)
        elif "lights" in response_lower:
            await asyncio.to_thread(control_lights)
            self.play_audio("I have adjusted the lights for you.")
        elif "spotify" in response_lower:
            await asyncio.to_thread(control_spotify)
            self.play_audio("Playing your favorite Spotify playlist.")
        else:
            # If no known command is found, just repeat the response
            self.play_audio(response)

    def play_audio(self, message, complete_callback=None):
        """
        Plays audio feedback to the user.
        Implement this method based on your hardware specifications.
        """
        print(f"[SPEECH] Playing audio: {message}")
        # Simulate audio playback delay
        time.sleep(2)  # Simulate the time taken to play audio
        if complete_callback:
            complete_callback()  # Call the callback to indicate playback is complete