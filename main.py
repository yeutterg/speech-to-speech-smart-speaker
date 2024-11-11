from speech import SpeechHandler
from hardware import HardwareInterface
# from web_interface import start_web_interface  # Uncomment if using web interface

import time

def main():
    """
    Initializes the HardwareInterface and SpeechHandler, and starts the main application loop.
    """
    # Initialize SpeechHandler without hardware reference for now
    speech_handler = SpeechHandler()

    # Initialize HardwareInterface with the SpeechHandler
    hardware_interface = HardwareInterface(speech_handler)

    # Optionally start web interface in a separate thread
    # web_thread = threading.Thread(target=start_web_interface, daemon=True)
    # web_thread.start()

    print("[MAIN] Application is running. Press Ctrl+C to exit.")

    try:
        # Keep the main thread alive to listen for events
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MAIN] Exiting gracefully.")
    finally:
        hardware_interface.cleanup()
        # If you started the web interface thread, ensure it's properly terminated
        # web_thread.join()

if __name__ == "__main__":
    main()