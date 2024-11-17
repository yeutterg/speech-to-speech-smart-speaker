# audio_handler.py

import pyaudio
import wave
import asyncio
import logging

# Configure logging for AudioHandler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [AudioHandler] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class AudioHandler:
    def __init__(self, output_audio_file='output.wav', chunk=1024, sample_format=pyaudio.paInt16, channels=1, rate=44100):
        self.p = pyaudio.PyAudio()
        self.chunk = chunk
        self.format = sample_format
        self.channels = channels
        self.rate = rate
        self.stream = None
        self.frames = []
        self.recording = False
        self.output_audio_file = output_audio_file
        logging.info("AudioHandler: Initialized.")

    def start_recording(self):
        if self.recording:
            logging.warning("AudioHandler: Already recording.")
            return
        logging.info("AudioHandler: Starting recording.")
        self.frames = []
        self.stream = self.p.open(format=self.format,
                                  channels=self.channels,
                                  rate=self.rate,
                                  frames_per_buffer=self.chunk,
                                  input=True)
        self.recording = True
        asyncio.create_task(self.record())

    async def record(self):
        logging.info("AudioHandler: Recording started.")
        while self.recording:
            data = self.stream.read(self.chunk, exception_on_overflow=False)
            self.frames.append(data)
            await asyncio.sleep(0)  # Yield control to the event loop
        logging.info("AudioHandler: Recording stopped.")

    def stop_recording(self):
        if not self.recording:
            logging.warning("AudioHandler: Not currently recording.")
            return None
        logging.info("AudioHandler: Stopping recording.")
        self.recording = False
        self.stream.stop_stream()
        self.stream.close()
        # Save the recorded data as a WAV file
        wf = wave.open(self.output_audio_file, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        logging.info(f"AudioHandler: Audio saved to {self.output_audio_file}.")
        # Read the audio data and return
        with open(self.output_audio_file, 'rb') as f:
            audio_data = f.read()
        return audio_data

    def play_audio(self, audio_data):
        """
        Play audio from binary data.
        """
        logging.info("AudioHandler: Playing audio.")
        wf = wave.open('temp_playback.wav', 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(audio_data)
        wf.close()

        # Play the audio
        stream = self.p.open(format=self.format,
                             channels=self.channels,
                             rate=self.rate,
                             output=True)
        wf = wave.open('temp_playback.wav', 'rb')
        data = wf.readframes(self.chunk)
        while data:
            stream.write(data)
            data = wf.readframes(self.chunk)
        stream.stop_stream()
        stream.close()
        wf.close()
        logging.info("AudioHandler: Audio playback finished.")

    def cleanup(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        logging.info("AudioHandler: Cleaned up.")