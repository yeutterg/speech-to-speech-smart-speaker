from adafruit_dotstar import DotStar
from gpiozero import Button
from signal import pause
import platform
import threading
import time

class HardwareInterface:
	BUTTON_PIN = 17  # GPIO pin number where the button is connected

	def __init__(self, speech_handler):
		"""
		Initializes the GPIO settings, configures the button pin, and sets up event detection.

		Args:
			speech_handler (SpeechHandler): An instance of SpeechHandler to handle speech processing.
		"""
		self.speech_handler = speech_handler

		# Check if the script is running on a Raspberry Pi
		platform_info = platform.uname()
		print("[INIT] Platform Info:", platform_info)
		if platform_info.system != "Linux" or not platform_info.node.lower().startswith("ras"):
			raise EnvironmentError("This script is intended to run on a Raspberry Pi.")

		# Initialize Button using gpiozero
		self.button = Button(self.BUTTON_PIN, pull_up=True, bounce_time=0.1)
		self.button.when_pressed = self.handle_press_event
		print(f"[INIT] Button initialized on GPIO pin {self.BUTTON_PIN} with pull-up resistor and bounce_time=0.1s.")

		# Initialize DotStar LED strip
		# self.DOTSTAR_DATA = 5
		# self.DOTSTAR_CLOCK = 6
		# self.dots = DotStar(self.DOTSTAR_CLOCK, self.DOTSTAR_DATA, 3, brightness=0.2)
		# print("[INIT] DotStar LED initialized.")

	def handle_press_event(self):
		"""
		Handles button press events and invokes the SpeechHandler.
		"""
		print("[DEBUG] Button press event detected.")
		# Invoke speech handling in a separate thread to prevent blocking
		threading.Thread(target=self.speech_handler.handle_speech, daemon=True).start()
		# Activate the DotStar LED
		# self.dots[0] = (0, 0, 255)  # Set the first LED to blue (RGB: 0, 0, 255)
		# self.dots.show()

	def cleanup(self):
		"""
		Cleans up the GPIO settings.
		"""
		# self.button.close()
		# self.dots.deinit()
		print("[CLEANUP] GPIO settings cleaned up.")