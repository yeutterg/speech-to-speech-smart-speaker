from gpiozero import Button, DigitalOutputDevice
import platform
import threading
import time
import pygame

class DotStarCustom:
	"""
	A custom DotStar LED strip controller using software SPI via gpiozero's DigitalOutputDevice.
	"""
	START_FRAME = [0x00] * 4  # 32 bits of zeros
	DEFAULT_FRAME = [0xFF, 0x00, 0x00, 0x00]  # Default LED frame (brightness full, red color)

	def __init__(self, data_gpio, clock_gpio, num_leds, brightness=0.2):
		"""
		Initializes the DotStar LED strip using software SPI.

		Args:
			data_gpio (int): GPIO pin number for Data (e.g., GPIO5).
			clock_gpio (int): GPIO pin number for Clock (e.g., GPIO6).
			num_leds (int): Number of LEDs in the strip.
			brightness (float): Brightness level (0.0 to 1.0).
			"""
		self.num_leds = num_leds
		self.brightness = max(0.0, min(brightness, 1.0))  # Clamp brightness between 0.0 and 1.0

		# Initialize GPIO pins for Data and Clock
		self.data_pin = DigitalOutputDevice(data_gpio, active_high=True, initial_value=False)
		self.clock_pin = DigitalOutputDevice(clock_gpio, active_high=True, initial_value=False)
		print(f"[INIT] Initialized Data pin GPIO{data_gpio} and Clock pin GPIO{clock_gpio}.")

		# Initialize LED data
		self.led_data = [self.DEFAULT_FRAME.copy() for _ in range(self.num_leds)]
		self.update()

	def _send_bit(self, bit: int):
		"""
		Sends a single bit over SPI.

		Args:
			bit (int): The bit to send (0 or 1).
			"""
		if bit:
			self.data_pin.on()
		else:
			self.data_pin.off()
		# Short delay to ensure the data pin is set before toggling the clock
		time.sleep(0.0001)  # 100 microseconds
		self.clock_pin.on()
		time.sleep(0.0001)  # 100 microseconds
		self.clock_pin.off()
		time.sleep(0.0001)  # 100 microseconds

	def _send_byte(self, byte: int):
		"""
		Sends a single byte over SPI, MSB first.

		Args:
			byte (int): The byte to send.
			"""
		for i in range(7, -1, -1):
			bit = (byte >> i) & 0x01
			self._send_bit(bit)

	def _send_frame(self, frame: list):
		"""
		Sends a frame (list of bytes) to the DotStar strip.

		Args:
			frame (list): List of integers representing bytes.
			"""
		for byte in frame:
			self._send_byte(byte)

	def set_pixel(self, index, color):
		"""
		Sets the color of a specific LED.

		Args:
			index (int): LED index.
			color (tuple): (R, G, B) tuple with values from 0 to 255.
			"""
		if 0 <= index < self.num_leds:
			brightness_byte = int(self.brightness * 31) & 0x1F  # 5-bit brightness (0-31)
			r, g, b = color
			self.led_data[index] = [0xE0 | brightness_byte, b, g, r]
			print(f"[DEBUG] LED {index} set to color {color} with brightness {self.brightness}.")
		else:
			print(f"[WARNING] LED index {index} is out of range.")

	def show(self):
		"""
		Sends the LED data to the DotStar strip using software SPI.
		"""
		# Start frame
		self._send_frame(self.START_FRAME)

		# LED frames
		for frame in self.led_data:
			self._send_frame(frame)

		# Optional end frame (not strictly necessary for short strips)
		# Uncomment the following line if needed for longer strips
		# self._send_frame([0x00] * 4)

		print("[DEBUG] Sent data to DotStar strip.")

	def update(self):
		"""
		Refreshes the LED strip with the current LED data.
		"""
		self.show()

	def deinit(self):
		"""
		Closes the GPIO connections.
		"""
		self.data_pin.close()
		self.clock_pin.close()
		print("[CLEANUP] Data and Clock pins closed.")

class HardwareInterface:
	BUTTON_PIN = 17       # GPIO pin number where the button is connected
	DOTSTAR_DATA_GPIO = 5  # GPIO5 for DotStar Data
	DOTSTAR_CLOCK_GPIO = 6  # GPIO6 for DotStar Clock
	NUM_LEDS = 3          # Number of LEDs in the strip
	BRIGHTNESS = 0.2      # Set brightness (0.0 to 1.0)

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

		# Initialize DotStar LED strip using custom software SPI
		self.dots = DotStarCustom(
			data_gpio=self.DOTSTAR_DATA_GPIO,
			clock_gpio=self.DOTSTAR_CLOCK_GPIO,
			num_leds=self.NUM_LEDS,
			brightness=self.BRIGHTNESS
		)
		print("[INIT] DotStar LED strip initialized with software SPI.")

	def handle_press_event(self):
		"""
		Handles button press events and invokes the SpeechHandler.
		"""
		print("[DEBUG] Button press event detected.")
		# Play a pleasant beep sound to tell the user the device is listening
		self.play_wake_sound()
		# Activate the DotStar LED
		self.dots.set_pixel(0, (0, 0, 255))  # Set the first LED to blue (RGB: 0, 0, 255)
		self.dots.update()
		# Invoke speech handling 
		asyncio.create_task(self.speech_handler.handle_speech())

	def play_wake_sound(self):
		"""
		Plays a pleasant beep sound using Pygame in a separate thread.
		"""
		threading.Thread(target=self._play_sound, daemon=True).start()  # Start the sound in a new thread

	def _play_sound(self):
		"""
		Helper method to play the sound.
		"""
		pygame.mixer.init()  # Initialize the mixer
		beep_sound = pygame.mixer.Sound("audio/wake_sound.wav")  # Load your beep sound file
		beep_sound.play()  # Play the sound
		pygame.time.delay(500)  # Wait for the sound to finish playing (adjust as needed)

	def handle_speech_complete(self):
		"""
		Handles the completion of speech handling and turns off the DotStar LED.
		"""
		print("[DEBUG] Speech handling complete.")
		# Turn off the DotStar LED
		self.dots.set_pixel(0, (0, 0, 0))  # Set the first LED to off (RGB: 0, 0, 0)
		self.dots.update()

	def cleanup(self):
		"""
		Cleans up the GPIO settings.
		"""
		self.button.close()
		self.dots.deinit()
		print("[CLEANUP] GPIO settings cleaned up.")