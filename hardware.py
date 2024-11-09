import adafruit_voice_bonnet

class HardwareInterface:
	def __init__(self):
		self.voice_bonnet = adafruit_voice_bonnet.VoiceBonnet()

	def capture_audio(self):
		return self.voice_bonnet.record_audio()

	def play_audio(self, audio_data):
		self.voice_bonnet.play_audio(audio_data)

	def button_pressed(self):
		return self.voice_bonnet.button_pressed()

	def set_led_status(self, status):
		self.voice_bonnet.set_led_status(status)