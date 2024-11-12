import asyncio
from speech import SpeechHandler
from hardware import HardwareInterface

async def main():
    # Initialize the SpeechHandler
    speech_handler = SpeechHandler()

    # Initialize the HardwareInterface with the SpeechHandler
    hardware_interface = HardwareInterface(speech_handler)

    print("[MAIN] Application is running. Press the button to activate.")
    
    try:
        # Keep the main thread alive to listen for events
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n[MAIN] Exiting gracefully.")
    finally:
        hardware_interface.cleanup()

if __name__ == "__main__":
    asyncio.run(main())