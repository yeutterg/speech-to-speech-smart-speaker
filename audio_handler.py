import pyaudio
import wave
import logging
import io
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
        """Play audio from bytes data"""
        if not audio_data:
            return
            
        try:
            # Create output stream with larger buffer and lower latency
            stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                output=True,
                frames_per_buffer=4096,  # Increased buffer size
                stream_callback=None,
                output_device_index=None,
                start=False  # Don't start yet
            )
            
            # Start stream
            stream.start_stream()
            
            # Calculate buffer size for smoother playback
            buffer_size = len(audio_data)
            chunk_size = 4096  # Larger chunks for smoother playback
            
            # Play audio in larger chunks
            for i in range(0, buffer_size, chunk_size):
                if not stream.is_active():
                    break
                chunk = audio_data[i:i + chunk_size]
                stream.write(chunk, exception_on_underflow=False)
            
            # Properly close stream
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