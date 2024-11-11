"""
hardware_test.py

This script is designed to test the Adafruit Voice Bonnet hardware.
It initializes a button on GPIO pin 17 and continuously monitors its state.
When the button is pressed, it prints "Button pressed" to the console.
"""

import RPi.GPIO as GPIO
import time
import platform

# Check if the script is running on a Raspberry Pi
print("Platform:",platform.uname())
if platform.system() != "Linux" or platform.uname()[1][:3] != "ras":
    raise EnvironmentError("This script is intended to run on a Raspberry Pi.")

# Initialize the GPIO system
# If you get an error related to GPIO access, run all 3 of these commands:
# sudo apt remove python3-rpi.gpio
# pip3 uninstall rpi-lgpio
# pip3 install rpi-gpio
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
BUTTON_PIN = 17

# Set up GPIO pin 17 as input with a pull-up resistor
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    while True:
        button_state = GPIO.input(BUTTON_PIN)
        if not button_state:  # Button pressed (active LOW)
            print("Button pressed")
            # Debounce by waiting until the button is released
            while not GPIO.input(BUTTON_PIN):
                time.sleep(0.01)
        time.sleep(0.01)  # Polling interval
except KeyboardInterrupt:
    print("\nExiting gracefully")
finally:
    GPIO.cleanup()  # Cleans up the GPIO settings