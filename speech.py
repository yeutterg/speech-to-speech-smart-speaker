import openai
import os
from functions import get_current_weather, control_lights, control_spotify

class SpeechHandler:
	def __init__(self, hardware):
		self.hardware = hardware
		openai.api_key = os.getenv("OPENAI_API_KEY")

	def handle_speech(self):
		# Capture audio input
		audio_input = self.hardware.capture_audio()
		
		# Send audio to OpenAI's Realtime API
		response = openai.Audio.transcribe(audio_input)
		
		# Process the response and call appropriate function
		if "weather" in response:
			get_current_weather()
		elif "lights" in response:
			control_lights()
		elif "spotify" in response:
			control_spotify()
		
		# Provide audio feedback
		self.hardware.play_audio(response)

	private _stream: Stream;