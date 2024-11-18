import asyncio
import logging
import signal
from gpiozero import Button
from openai_realtime_client import RealtimeClient
from audio import AudioIOHandler
from config import OPENAI_API_KEY, BUTTON_PIN

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class SmartSpeaker:
    def __init__(self):
        self.recording = False
        self.audio_io_handler = AudioIOHandler()
        self.button = Button(BUTTON_PIN)
        self.loop = None
        
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
            
        self.client = RealtimeClient(
            api_key=OPENAI_API_KEY,
            on_text_delta=lambda text: print(f"\nAssistant: {text}", end="", flush=True),
            on_audio_delta=self.audio_io_handler.play_audio,
            on_input_transcript=lambda transcript: print(f"\nYou said: {transcript}\nAssistant: ", end="", flush=True),
            on_output_transcript=lambda transcript: print(f"{transcript}", end="", flush=True)
        )
        
        # Set up button handler
        self.button.when_pressed = self._button_pressed
        
    def _button_pressed(self):
        """Non-async button handler that safely schedules the async toggle_recording"""
        if self.loop is None:
            logging.error("Event loop not set")
            return
        
        # Schedule the toggle recording
        asyncio.run_coroutine_threadsafe(self._toggle_recording(), self.loop)
        
    async def _toggle_recording(self):
        """Async method to handle recording toggle and audio sending"""
        # Stop playback immediately in the synchronous context
        self.audio_io_handler.stop_playback()
        
        if not self.recording:
            # Start recording
            self.recording = True
            self.audio_io_handler.start_recording()
            logging.info("Recording started")
        else:
            # Stop recording and immediately send audio
            self.recording = False
            audio_data = self.audio_io_handler.stop_recording()
            if audio_data:
                try:
                    logging.info("Sending audio to Realtime API...")
                    await self.client.send_audio(audio_data)
                    logging.info("Audio sent successfully")
                except Exception as e:
                    logging.error(f"Error sending audio: {e}")
    
    async def start(self):
        """Start the smart speaker"""
        try:
            # Store the event loop
            self.loop = asyncio.get_running_loop()
            
            # Connect to Realtime API
            await self.client.connect()
            logging.info("Connected to Realtime API")
            
            # Start message handler
            message_handler = asyncio.create_task(self.client.handle_messages())
            logging.info("Message handler started")
            
            print("\nSmart Speaker is ready!")
            print("Press the button to start/stop recording")
            print("Press Ctrl+C to exit\n")
            
            # Main loop - just keep recording while active
            while True:
                if self.recording:
                    self.audio_io_handler.record()
                await asyncio.sleep(0.005)
                
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        self.recording = False
        await self.client.close()
        self.audio_io_handler.cleanup()
        self.button.close()
        logging.info("Cleanup complete")

async def main():
    # Handle shutdown signals
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(cleanup()))
    
    speaker = SmartSpeaker()
    await speaker.start()

async def cleanup():
    """Handle shutdown gracefully"""
    logging.info("Shutting down...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    asyncio.get_event_loop().stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down...")