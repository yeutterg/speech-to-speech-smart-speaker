import asyncio
import json
import logging
import os

from openai_realtime_client import OpenAIRealtimeClient
from dotenv import load_dotenv
import pygame

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('RealtimeClient')

class RealtimeClient:
    def __init__(self, api_key=None, url='wss://api.openai.com/v1/realtime'):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.url = url
        self.client = OpenAIRealtimeClient(api_key=self.api_key, url=self.url)
        self.client.on('error', self.handle_error)
        self.client.on('response', self.handle_response)
        self.client.on('end', self.handle_end)
        pygame.mixer.init()

    async def connect(self):
        await self.client.connect()
        await self.client.update_session({
            "modalities": ["text", "audio"],
            "instructions": "You are a helpful assistant",
            "voice": "alloy",
            "temperature": 0.8,
        })

    async def send_audio(self, audio_data: bytes):
        await self.client.send_audio(audio_data)

    def handle_response(self, response):
        logger.info(f"Received response: {response}")
        # Assuming the response contains audio data in bytes
        audio_bytes = response.get('audio')  # Adjust based on actual response structure
        if audio_bytes:
            self.play_audio(audio_bytes)

    def play_audio(self, audio_bytes: bytes):
        """Play audio bytes using pygame."""
        with open("temp_response.wav", "wb") as f:
            f.write(audio_bytes)
        pygame.mixer.music.load("temp_response.wav")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        os.remove("temp_response.wav")

    def handle_error(self, error):
        logger.error(f"Error: {error}")

    def handle_end(self):
        logger.info("Connection closed")

    async def close(self):
        await self.client.close()