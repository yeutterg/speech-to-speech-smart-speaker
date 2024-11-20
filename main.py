import asyncio
from config import OPENAI_API_KEY, BUTTON_PIN, CHUNK_SIZE, SAMPLE_FORMAT, CHANNELS, RATE
import logging
from openai_realtime_client import RealtimeClient, AudioHandler, InputHandler, TurnDetectionMode
from hardware import HardwareController 
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
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.recording = False
        self.external_queue = Queue()
        self.hardware_controller = None

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
            turn_detection_mode=TurnDetectionMode.MANUAL,
            on_input_transcript=lambda transcript: print(f"\nYou said: {transcript}\nAssistant: ", end="", flush=True),
            on_output_transcript=lambda transcript: print(f"{transcript}", end="", flush=True)
        )

    async def start_recording(self):
        """Start recording audio from the microphone."""
        if self.recording:
            logging.warning("Already recording")
            return
        self.recording = True
        self.frames = []
        logging.info("Started recording")
        # Start a background task to read audio frames
        self.recording_task = asyncio.create_task(self.record_audio())

    async def stop_recording(self):
        """Stop recording audio and send it to the API."""
        if not self.recording:
            logging.warning("Not currently recording")
            return
        self.recording = False
        self.recording_task.cancel()
        logging.info("Stopped recording")
        audio_data = b''.join(self.frames)
        await self.client.send_audio(audio_data)

    async def record_audio(self):
        """Continuously read audio frames while recording."""
        try:
            while self.recording:
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                self.frames.append(data)
                await asyncio.sleep(0)  # Yield control to the event loop
        except asyncio.CancelledError:
            logging.info("Recording task cancelled")
        except Exception as e:
            logging.error(f"Error during recording: {e}")

    async def handle_commands(self):
        """Handle incoming commands from the queue."""
        while True:
            command = await self.loop.run_in_executor(None, self.external_queue.get)
            if command == "toggle_recording":
                if not self.recording:
                    await self.start_recording()
                else:
                    await self.stop_recording()
            elif command in ["enter", "r"]:
                print("button pressed")  # Print message on button press

    async def start(self):
        """Start the smart speaker"""
        self.loop = asyncio.get_running_loop()
        
        # Initialize HardwareController with the shared external_queue and event loop
        self.hardware_controller = HardwareController(
            external_queue=self.external_queue,
            loop=self.loop,
            use_mock=False  # Set to True if you want to use mock hardware for testing
        )
        
        self.input_handler = InputHandler(self.external_queue, self.loop)
        
        try:
            await self.client.connect()
            self.message_handler = asyncio.create_task(self.client.handle_messages())
            print("Connected to OpenAI Realtime API")
            self.streaming_task = asyncio.create_task(self.audio_handler.start_streaming(self.client))

            # Start handling button commands
            await self.handle_commands()

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
        if self.hardware_controller:
            self.hardware_controller.close()
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        logging.info("Cleanup complete")

if __name__ == "__main__":
    try:
        speaker = SmartSpeaker()
        asyncio.run(speaker.start())
    except KeyboardInterrupt:
        logging.info("Shutting down...")