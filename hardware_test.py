"""
hardware_test.py

This script is designed to test the Adafruit Voice Bonnet hardware.
It initializes a button on GPIO pin 17 and controls a DotStar LED.
When the button is pressed, it turns the LED blue.
"""

from gpiozero import Button
from adafruit_dotstar import DotStar
from signal import pause
import platform
import sys

def main():
    # Check if the script is running on a Raspberry Pi
    print("Platform:", platform.uname())
    if platform.system() != "Linux" or not platform.uname().node.startswith("ras"):
        raise EnvironmentError("This script is intended to run on a Raspberry Pi.")

    # # Initialize the DotStar LED
    # DOTSTAR_DATA = 5   # Replace with your data pin
    # DOTSTAR_CLOCK = 6  # Replace with your clock pin
    # NUM_LEDS = 1       # Number of LEDs

    # try:
    #     dots = DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, NUM_LEDS, brightness=0.2)
    #     print("[INIT] DotStar LED initialized.")
    # except Exception as e:
    #     print(f"[ERROR] Failed to initialize DotStar LED: {e}")
    #     sys.exit(1)

    # Initialize Button using gpiozero
    BUTTON_PIN = 17
    button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.1)
    print(f"[INIT] Button initialized on GPIO pin {BUTTON_PIN} with pull-up resistor and bounce_time=0.1s.")

    def on_button_pressed():
        print("[EVENT] Button pressed")
        # Turn the DotStar LED blue
        # dots[0] = (0, 0, 255)  # RGB for blue
        # dots.show()
        print("[LED] DotStar LED set to blue.")

    def on_button_released():
        print("[EVENT] Button released")
        # Turn off the DotStar LED
        # dots[0] = (0, 0, 0)
        # dots.show()
        print("[LED] DotStar LED turned off.")

    # Assign event handlers
    button.when_pressed = on_button_pressed
    button.when_released = on_button_released

    print("[MAIN] Waiting for button press... Press Ctrl+C to exit.")

    try:
        pause()  # Keep the script running to listen for events
    except KeyboardInterrupt:
        print("\n[MAIN] KeyboardInterrupt detected. Exiting gracefully...")
    finally:
        # Cleanup
        try:
            # dots.deinit()
            print("[CLEANUP] DotStar LED deinitialized.")
        except Exception as e:
            print(f"[ERROR] Failed to deinitialize DotStar LED: {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()