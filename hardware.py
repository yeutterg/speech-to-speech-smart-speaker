import logging
from gpiozero import Button, Device
from gpiozero.pins.mock import MockFactory  # Corrected import
import asyncio

# Configure logging for hardware module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [HardwareController] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class HardwareController:
    """
    Controls the hardware components, such as buttons.
    
    Attributes:
        external_queue (asyncio.Queue): Queue to communicate events.
        use_mock (bool): Flag to determine whether to use MockFactory.
    """
    def __init__(self, external_queue: asyncio.Queue, use_mock: bool = False):
        self.external_queue = external_queue
        self.use_mock = use_mock
        self.factory = None

        if self.use_mock:
            self.factory = MockFactory()
            Device.pin_factory = self.factory
            logging.info("Using MockFactory for pin operations.")
        else:
            self.factory = None  # Use default factory
            logging.info("Using default GPIO pin factory.")

        try:
            self.space_button = Button(17, pin_factory=self.factory)  # GPIO17
            logging.info("Initialized Button on GPIO17.")
            self.space_button.when_pressed = self.on_space_button_pressed
        except Exception as e:
            logging.error(f"Failed to initialize Button on GPIO17: {e}")
            raise

    def on_space_button_pressed(self):
        """
        Callback for space button press event. Adds an event to the external queue.
        """
        logging.info("Space button pressed. Adding event to external queue.")
        self.external_queue.put_nowait("space_pressed")

    def close(self):
        """
        Cleans up the hardware components.
        """
        logging.info("Closing HardwareController...")
        self.space_button.close()
        logging.info("Button on GPIO17 closed.")