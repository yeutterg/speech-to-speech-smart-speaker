import RPi.GPIO as GPIO
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

		# Initialize GPIO
		GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
		GPIO.setup(self.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		print(f"[INIT] GPIO pin {self.BUTTON_PIN} initialized as input with pull-up resistor.")

		# Set up event detection for button press (falling edge)
		GPIO.add_event_detect(self.BUTTON_PIN, GPIO.FALLING, callback=self.handle_press_event, bouncetime=100)
		print("[INIT] GPIO event detection set for button press with bouncetime=100ms.")

	def handle_press_event(self, channel):
		"""
		Handles GPIO pin press events and invokes the SpeechHandler.

		Args:
			channel (int): The GPIO channel where the event was detected.
		"""
		print("[DEBUG] Button press event detected.")
		# Invoke speech handling in a separate thread to prevent blocking
		threading.Thread(target=self.speech_handler.handle_speech, daemon=True).start()

	def cleanup(self):
		"""
		Cleans up the GPIO settings.
		"""
		GPIO.cleanup()
		print("[CLEANUP] GPIO settings cleaned up.")