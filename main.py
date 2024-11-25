import asyncio
import logging
import wave
import io
from config import OPENAI_API_KEY, CHUNK_SIZE, SAMPLE_FORMAT, CHANNELS, RATE
from openai_realtime_client import (
    RealtimeClient,
    AudioHandler,
    TurnDetectionMode,
)
from hardware import HardwareController
import pyaudio
from tools import ToolRegistry
from llama_index.core.tools import FunctionTool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

class SmartSpeaker:
    def __init__(self):
        self.audio_handler = AudioHandler()
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.recording = False
        self.mic_muted = True          # Start with microphone muted
        self.speaker_muted = False     # Start with speaker unmuted (to hear responses)
        self.tool_registry = ToolRegistry()     # Initialize tools

        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # Convert tools to LlamaIndex FunctionTools
        self.function_tools = []
        for tool in self.tool_registry.tools:
            function_tool = FunctionTool.from_defaults(
                fn=tool.execute,
                name=tool.name,
                description=tool.description
            )
            self.function_tools.append(function_tool)
        
        self.client = RealtimeClient(
            api_key=OPENAI_API_KEY,
            on_text_delta=lambda text: print(f"\nAssistant: {text}", end="", flush=True),
            on_audio_delta=self.play_audio,
            on_interrupt=self.stop_playback,
            turn_detection_mode=TurnDetectionMode.MANUAL,
            on_input_transcript=lambda transcript: print(
                f"\nYou said: {transcript}\nAssistant: ", end="", flush=True
            ),
            on_output_transcript=lambda transcript: print(
                f"{transcript}", end="", flush=True
            ),
            tools=self.function_tools,
        )

        # Initialize the command queue as an asyncio.Queue
        self.external_queue = asyncio.Queue()
        self.hardware_controller = None  # Will be initialized in async context

        # Ready flag to ignore initial spurious commands
        self.ready = False

        # Lock to prevent overlapping conversations
        self.conversation_lock = asyncio.Lock()

    def _encode_wav(self, frames):
        """Encapsulate raw audio frames into WAV format."""
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(SAMPLE_FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        wav_data = buffer.getvalue()
        logging.debug(f"Encoded WAV data size: {len(wav_data)} bytes.")
        return wav_data

    async def start_recording(self):
        """Start recording audio from the microphone."""
        if self.recording:
            logging.warning("Attempted to start recording, but already recording.")
            return
        try:
            self.stream = self.p.open(
                format=SAMPLE_FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
            )
            self.recording = True
            self.mic_muted = False  # Unmute when recording starts
            self.frames = []
            logging.info("Recording started.")
            # Stop any ongoing playback to prevent feedback
            self.audio_handler.stop_playback_immediately()
            # Start a background task to read audio frames
            self.recording_task = asyncio.create_task(self.record_audio())
            # Start AudioHandler streaming
            self.streaming_task = asyncio.create_task(
                self.audio_handler.start_streaming(self.client)
            )
        except Exception as e:
            logging.error(f"Failed to start recording: {e}")

    async def stop_recording(self):
        """Stop recording audio and send it to the API."""
        if not self.recording:
            logging.warning("Attempted to stop recording, but not currently recording.")
            return
        try:
            self.recording = False
            self.mic_muted = True  # Mute when recording stops
            self.recording_task.cancel()
            await self.recording_task
            logging.info("Recording stopped.")
            if not self.frames:
                logging.warning("No audio frames were recorded. Skipping send_audio.")
                return
            audio_data = self._encode_wav(self.frames)
            logging.info(f"Sending {len(audio_data)} bytes of audio data to the API.")
            await self.client.send_audio(audio_data)
            # Stop AudioHandler streaming
            self.audio_handler.stop_playback_immediately()
            if self.streaming_task:
                self.streaming_task.cancel()
                await self.streaming_task
            # Clear frames after sending
            self.frames = []
        except asyncio.CancelledError:
            logging.info("Recording task cancelled successfully.")
        except Exception as e:
            logging.error(f"Failed to stop recording: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

    async def record_audio(self):
        """Continuously read audio frames while recording."""
        try:
            while self.recording:
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                self.frames.append(data)
                await asyncio.sleep(0)  # Yield control to the event loop
        except asyncio.CancelledError:
            logging.info("Recording task cancelled.")
        except Exception as e:
            logging.error(f"Error during recording: {e}")

    async def unmute_mic_and_stop_playback(self):
        """Unmute the microphone and stop any ongoing playback."""
        logging.info("Unmuting microphone and stopping playback.")
        self.speaker_muted = True
        self.mic_muted = False
        await self.start_recording()
        self.audio_handler.stop_playback_immediately()
        logging.info("Microphone unmuted and playback stopped.")

    async def mute_mic_and_manage_output(self):
        """Mute the microphone and ensure only output is played on the speaker."""
        logging.info("Muting microphone and managing output.")
        self.speaker_muted = False
        self.mic_muted = True
        await self.stop_recording()
        # Additional logic to manage output can be added here if necessary
        logging.info("Microphone muted and output managed.")

    def stop_playback(self):
        """Callback to stop playback immediately."""
        logging.info("Interrupt received: Stopping playback.")
        self.audio_handler.stop_playback_immediately()

    async def handle_commands(self):
        """Handle incoming commands from the queue."""
        # Allow some time for the system to stabilize and ignore initial spurious commands
        await asyncio.sleep(2)  # Adjust the delay as needed

        # Set the system as ready to process commands
        self.ready = True
        logging.info("System is ready to process commands.")

        while True:
            command = await self.external_queue.get()
            if not self.ready:
                logging.warning(f"Ignored command before readiness: {command}")
                continue

            async with self.conversation_lock:
                if command == "r":
                    logging.info("'r' command received: Unmuting mic and stopping playback.")
                    await self.unmute_mic_and_stop_playback()
                elif command == "enter":
                    logging.info("'enter' command received: Muting mic and managing output.")
                    await self.mute_mic_and_manage_output()
                else:
                    logging.warning(f"Unknown command received: {command}")

    async def start(self):
        """Start the smart speaker."""
        self.loop = asyncio.get_running_loop()

        # Initialize HardwareController with the shared external_queue and event loop
        self.hardware_controller = HardwareController(
            external_queue=self.external_queue,
            loop=self.loop,
            use_mock=False,  # Set to True if you want to use mock hardware for testing
        )

        try:
            await self.client.connect()
            self.message_handler = asyncio.create_task(
                self.client.handle_messages()
            )
            logging.info("Connected to OpenAI Realtime API.")

            # Start handling button commands as a background task
            handle_commands_task = asyncio.create_task(self.handle_commands())

            # Keep the program running indefinitely
            await asyncio.Event().wait()

        except Exception as e:
            logging.error(f"Error during startup: {e}")
        finally:
            await self.cleanup()

    def play_audio(self, audio_data):
        """Play audio using the audio handler."""
        if self.speaker_muted:
            logging.info("Speaker muted. Skipping audio playback.")
            return

        if not audio_data:
            logging.warning("No audio data received to play.")
            return

        try:
            logging.info("Playing received audio.")
            self.audio_handler.play_audio(audio_data)
        except Exception as e:
            logging.error(f"Error playing audio: {e}")
        
    async def handle_tool_call(self, tool_call):
        """Handle tool calls from the API"""
        logging.info(f"Received tool call with ID: {tool_call.id}")
        try:
            tool_name = tool_call.name
            arguments = tool_call.arguments
            
            logging.info(f"Executing tool call: {tool_name}")
            logging.debug(f"Tool arguments: {arguments}")
            
            # Execute the tool
            logging.info(f"Calling tool_registry.execute_tool for '{tool_name}'")
            result = self.tool_registry.execute_tool(tool_name, **arguments)
            
            logging.info(f"Tool '{tool_name}' execution completed successfully")
            logging.debug(f"Tool result: {result}")
            
            # Send the result back to the API
            logging.info(f"Sending tool result back to API for call ID: {tool_call.id}")
            await self.client.send_tool_result(tool_call.id, result)
            logging.info(f"Tool result sent successfully for '{tool_name}'")
            
        except Exception as e:
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            logging.error(error_msg)
            logging.exception("Full exception details:")  # This will log the full traceback
            error_result = {"error": str(e)}
            logging.info(f"Sending error result back to API for call ID: {tool_call.id}")
            await self.client.send_tool_result(tool_call.id, error_result)

    async def cleanup(self):
        """Clean up resources."""
        logging.info("Starting cleanup process.")
        self.audio_handler.stop_streaming()
        self.audio_handler.cleanup()
        await self.client.close()
        if self.hardware_controller:
            self.hardware_controller.close()
        if self.recording:
            await self.stop_recording()
        self.p.terminate()
        logging.info("Cleanup complete.")

if __name__ == "__main__":
    try:
        speaker = SmartSpeaker()
        asyncio.run(speaker.start())
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully...")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")