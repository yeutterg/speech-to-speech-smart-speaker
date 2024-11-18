import pyaudio
import wave
import logging
import io
import os
from config import CHUNK_SIZE, SAMPLE_FORMAT, CHANNELS, RATE
from openai_realtime_client.handlers.audio_handler import AudioHandler as RealtimeAudioHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class AudioIOHandler:
    def __init__(self):
        self.realtime_handler = RealtimeAudioHandler()
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.recording = False

    def start_recording(self):
        """Start recording audio from microphone"""
        if self.recording:
            logging.info("Recording is already in progress. Stopping playback before starting a new recording.")
            self.stop_playback()  # Stop any ongoing playback
        
        logging.info("Starting recording")
        self.recording = True
        self.frames = []
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )

    def record(self):
        """Record a chunk of audio"""
        if self.recording and self.stream:
            try:
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                logging.error(f"Error recording audio: {e}")

    def stop_recording(self):
        """Stop recording and return the audio data as WAV"""
        if not self.recording:
            return None
            
        logging.info("Stopping recording")
        self.recording = False
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        
        # Convert raw PCM to WAV format
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(16000)
            wf.writeframes(b''.join(self.frames))
        
        wav_data = wav_buffer.getvalue()
        self.frames = []
        return wav_data

    def play_audio(self, audio_data):
        """Play audio using the realtime client's audio handler"""
        if not audio_data:
            return
            
        try:
            logging.info("Playing audio response")  # Add logging
            self.realtime_handler.play_audio(audio_data)
        except Exception as e:
            logging.error(f"Error playing audio: {e}")

    def stop_playback(self):
        """Stop any ongoing audio playback"""
        try:
            self.realtime_handler.stop_playback_immediately()
            logging.info("Audio playback stopped")
        except Exception as e:
            logging.error(f"Error stopping audio playback: {e}")

    def cleanup(self):
        """Clean up resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        self.realtime_handler.cleanup()
        logging.info("Audio handler cleaned up")