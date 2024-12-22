import asyncio
import logging
import wave
import io
from config import (
    CHUNK_SIZE, 
    SAMPLE_FORMAT, 
    CHANNELS, 
    RATE,
    LIVEKIT_TOKEN,
    LIVEKIT_URL
)
from livekit import rtc
import pyaudio
from hardware import HardwareController

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

class SmartSpeaker:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.recording = False
        self.mic_muted = True          # Start with microphone muted
        self.speaker_muted = False     # Start with speaker unmuted
        
        # Initialize LiveKit room
        self.room = rtc.Room()
        self._setup_room_handlers()

        # Initialize the command queue as an asyncio.Queue
        self.external_queue = asyncio.Queue()
        self.hardware_controller = None
        self.ready = False
        self.conversation_lock = asyncio.Lock()

    def _setup_room_handlers(self):
        @self.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            logging.info(
                "participant connected: %s %s", participant.sid, participant.identity
            )

        @self.room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant,
        ):
            logging.info("track subscribed: %s", publication.sid)
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                # Handle incoming audio track
                audio_stream = rtc.AudioStream(track)
                asyncio.ensure_future(self.handle_audio_stream(audio_stream))

    async def handle_audio_stream(self, stream: rtc.AudioStream):
        async for frame in stream:
            if not self.speaker_muted:
                # Play the received audio frame
                self.play_audio(frame.data)

    def _encode_wav(self, frames):
        """Encapsulate raw audio frames into WAV format."""
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(SAMPLE_FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        return buffer.getvalue()

    async def start_recording(self):
        """Start recording audio and publishing to LiveKit."""
        if self.recording:
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
            self.mic_muted = False
            self.frames = []
            logging.info("Recording started.")
            
            # Create and publish local audio track
            local_track = await rtc.LocalAudioTrack.create()
            await self.room.local_participant.publish_track(local_track)
            
            # Start recording task
            self.recording_task = asyncio.create_task(self.record_audio(local_track))
            
        except Exception as e:
            logging.error(f"Failed to start recording: {e}")

    async def record_audio(self, local_track):
        """Continuously read and publish audio frames."""
        try:
            while self.recording and not self.mic_muted:
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                self.frames.append(data)
                # Convert data to proper format for LiveKit
                await local_track.write_sample(data, RATE, CHANNELS)
                await asyncio.sleep(0.01)
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

        # Initialize HardwareController
        self.hardware_controller = HardwareController(
            external_queue=self.external_queue,
            loop=self.loop,
            use_mock=False,
        )

        try:
            # Connect to LiveKit room
            await self.room.connect(LIVEKIT_URL, LIVEKIT_TOKEN)
            logging.info("Connected to LiveKit room: %s", self.room.name)

            # Start handling button commands
            handle_commands_task = asyncio.create_task(self.handle_commands())

            # Keep the program running
            await asyncio.Event().wait()

        except Exception as e:
            logging.error(f"Error during startup: {e}")
        finally:
            await self.cleanup()

    def play_audio(self, audio_data):
        """Play audio using PyAudio output stream."""
        if self.speaker_muted:
            logging.info("Speaker muted. Skipping audio playback.")
            return

        if not audio_data:
            logging.warning("No audio data received to play.")
            return

        try:
            # Create output stream if it doesn't exist
            if not hasattr(self, 'output_stream'):
                self.output_stream = self.p.open(
                    format=SAMPLE_FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True,
                    frames_per_buffer=CHUNK_SIZE
                )
            
            logging.info("Playing received audio.")
            self.output_stream.write(audio_data)
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
        if self.recording:
            await self.stop_recording()
        if hasattr(self, 'output_stream'):
            self.output_stream.stop_stream()
            self.output_stream.close()
        await self.room.disconnect()
        if self.hardware_controller:
            self.hardware_controller.close()
        self.p.terminate()
        logging.info("Cleanup complete.")

if __name__ == "__main__":
    try:
        if not LIVEKIT_TOKEN or not LIVEKIT_URL:
            raise ValueError("LIVEKIT_TOKEN and LIVEKIT_URL are required")
        speaker = SmartSpeaker()
        asyncio.run(speaker.start())
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully...")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")