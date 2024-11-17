import asyncio
import signal
import logging
import os

from hardware import HardwareController
from audio_handler import AudioHandler
from dispatcher import dispatcher
from openai_realtime_client import RealtimeClient
from llama_index.core.tools import FunctionTool

# Add your own tools here!
def get_phone_number(name: str) -> str:
    """Get my phone number."""
    if name == "Jerry":
        return "1234567890"
    elif name == "Logan":
        return "0987654321"
    else:
        return "Unknown"

tools = [FunctionTool.from_defaults(fn=get_phone_number)]

# Configure logging for Main
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [Main] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

async def shutdown(sig, loop, hardware: HardwareController, client: RealtimeClient, audio_handler: AudioHandler):
    logging.info(f"Main: Received exit signal {sig.name}...")
    hardware.close()
    await client.close()
    audio_handler.cleanup()
    loop.stop()
    logging.info("Main: Shutdown complete.")

async def main():
    loop = asyncio.get_running_loop()

    # Initialize external command queue
    external_queue = asyncio.Queue()

    # Initialize AudioHandler
    audio_handler = AudioHandler()

    # Initialize HardwareController
    hardware = HardwareController(external_queue=external_queue, loop=loop, use_mock=False)

    # Initialize RealtimeClient
    client = RealtimeClient(
        api_key=os.environ.get("OPENAI_API_KEY"),
        on_text_delta=lambda text: print(f"\nAssistant: {text}", end="", flush=True),
        on_audio_delta=lambda audio: audio_handler.play_audio(audio),
        on_input_transcript=lambda transcript: print(f"\nYou said: {transcript}\nAssistant: ", end="", flush=True),
        on_output_transcript=lambda transcript: print(f"{transcript}", end="", flush=True),
        tools=tools,
    )

    # Start Dispatcher to distribute commands
    input_handler_queue = asyncio.Queue()
    audio_handler_queue = asyncio.Queue()
    dispatcher_task = asyncio.create_task(dispatcher(external_queue, [input_handler_queue, audio_handler_queue]))

    # Start RealtimeClient
    await client.connect()

    # Process Audio Commands
    async def process_audio_commands():
        while True:
            command = await audio_handler_queue.get()
            logging.info(f"AudioHandler: Received command: {command}")
            if command == 'r':
                audio_handler.start_recording()
            elif command == 'enter':
                audio_data = audio_handler.stop_recording()
                if audio_data:
                    await client.send_audio(audio_data)
                else:
                    logging.warning("AudioHandler: No audio data to send.")
            audio_handler_queue.task_done()

    audio_commands_task = asyncio.create_task(process_audio_commands())

    # Register shutdown signals
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(shutdown(s, loop, hardware, client, audio_handler))
        )

    logging.info("Main: System is running. Press the hardware button to interact.")

    try:
        # Keep the main coroutine alive
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Main: Error occurred - {e}")
    finally:
        # Clean up resources
        hardware.close()
        await client.close()
        audio_handler.cleanup()
        dispatcher_task.cancel()
        audio_commands_task.cancel()
        logging.info("Main: Cleanup complete.")

if __name__ == "__main__":
    # Ensure required packages are installed
    # pip install pyaudio gpiozero openai_realtime_client llama-index pynput

    logging.info("Starting Realtime API Integration...")
    asyncio.run(main())