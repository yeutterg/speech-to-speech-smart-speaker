import pyaudio
import wave
import logging
import os
from config import CHUNK_SIZE, SAMPLE_FORMAT, CHANNELS, RATE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class AudioHandler:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.recording = False

    def start_recording(self):
        """Start recording audio from microphone"""
        if self.recording:
            return
        
        logging.info("Starting recording")
        self.recording = True
        self.frames = []
        self.stream = self.p.open(
            format=self.p.get_format_from_width(SAMPLE_FORMAT // 8),
            channels=CHANNELS,
            rate=RATE,
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
        """Stop recording and return the audio data"""
        if not self.recording:
            return None
            
        logging.info("Stopping recording")
        self.recording = False
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        
        # Convert audio data to bytes
        audio_data = b''.join(self.frames)
        self.frames = []
        return audio_data

    def play_audio(self, audio_data):
        """Play audio from bytes data"""
        if not audio_data:
            return
            
        try:
            # Create output stream
            stream = self.p.open(
                format=self.p.get_format_from_width(SAMPLE_FORMAT // 8),
                channels=CHANNELS,
                rate=RATE,
                output=True
            )
            
            # Play audio in chunks
            for i in range(0, len(audio_data), CHUNK_SIZE):
                chunk = audio_data[i:i + CHUNK_SIZE]
                stream.write(chunk)
                
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            logging.error(f"Error playing audio: {e}")

    def cleanup(self):
        """Clean up resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        logging.info("Audio handler cleaned up") 