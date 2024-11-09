from speech import SpeechHandler
from hardware import HardwareInterface
from web_interface import start_web_interface

def main():
	hardware = HardwareInterface()
	speech_handler = SpeechHandler(hardware)
	
	# Start the web interface in a separate thread
	start_web_interface()

	# Main loop
	while True:
		if hardware.button_pressed():
			speech_handler.handle_speech()

if __name__ == "__main__":
	main()