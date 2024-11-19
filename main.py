import asyncio
from config import OPENAI_API_KEY, BUTTON_PIN, CHUNK_SIZE, SAMPLE_FORMAT, CHANNELS, RATE
from gpiozero import Button
import logging
from openai_realtime_client import RealtimeClient, AudioHandler, InputHandler, TurnDetectionMode
import pyaudio
from queue import Queue
import signal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class SmartSpeaker:
    def __init__(self):
        self.audio_handler = AudioHandler()
        self.button = Button(BUTTON_PIN)
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.recording = False

        self.stream = self.p.open(
            format=SAMPLE_FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
            
        self.client = RealtimeClient(
            api_key=OPENAI_API_KEY,
            on_text_delta=lambda text: print(f"\nAssistant: {text}", end="", flush=True),
            on_audio_delta=lambda audio: self.play_audio(audio),
            on_interrupt=lambda: self.audio_handler.stop_playback_immediately(),
            turn_detection_mode=TurnDetectionMode.SERVER_VAD,
            on_input_transcript=lambda transcript: print(f"\nYou said: {transcript}\nAssistant: ", end="", flush=True),
            on_output_transcript=lambda transcript: print(f"{transcript}", end="", flush=True)
        )

    async def start(self):
        """Start the smart speaker"""
        external_queue = Queue()
        self.loop = asyncio.get_running_loop()
        
        self.input_handler = InputHandler(external_queue, self.loop)
        
        try:
            await self.client.connect()
            self.message_handler = asyncio.create_task(self.client.handle_messages())
            print("Connected to OpenAI Realtime API")
            self.streaming_task = asyncio.create_task(self.audio_handler.start_streaming(self.client))

            while True:
                # Keep the connection alive
                command, _ = await self.input_handler.command_queue.get()

        except Exception as e:
            logging.error(f"Error: {e}")
        finally:
            await self.cleanup()

    def play_audio(self, audio_data):
        """Play audio using the audio handler"""
        if not audio_data:
            logging.warning("No audio data received")
            return

        try:
            logging.info("Playing audio")
            self.audio_handler.play_audio(audio_data)
        except Exception as e:
            logging.error(f"Error playing audio: {e}")

    async def cleanup(self):
        """Clean up resources"""
        self.audio_handler.stop_streaming()
        self.audio_handler.cleanup()
        await self.client.close()
        self.button.close()
        logging.info("Cleanup complete")

if __name__ == "__main__":
    try:
        speaker = SmartSpeaker()
        asyncio.run(speaker.start())
    except KeyboardInterrupt:
        logging.info("Shutting down...")