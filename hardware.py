import logging
from gpiozero import Button, Device
from gpiozero.pins.mock import MockFactory
import asyncio
import time

# Configure logging for HardwareController
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [HardwareController] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class HardwareController:
    """
    Controls the hardware components, such as the space button.

    Attributes:
        external_queue (asyncio.Queue): Queue to communicate events.
        use_mock (bool): Flag to determine whether to use MockFactory.
        loop (asyncio.AbstractEventLoop): Reference to the asyncio event loop.
    """
    def __init__(self, external_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop, use_mock: bool = False):
        self.external_queue = external_queue
        self.use_mock = use_mock
        self.loop = loop
        self.factory = None
        self.last_button_press = "enter"

        # Debounce settings
        self.debounce_interval = 0.5  # 500 ms
        self.last_press_time = 0

        if self.use_mock:
            self.factory = MockFactory()
            Device.pin_factory = self.factory
            logging.info("HardwareController: Using MockFactory for pin operations.")
        else:
            self.factory = None  # Use default factory
            logging.info("HardwareController: Using default GPIO pin factory.")

        try:
            self.space_button = Button(17, pin_factory=self.factory)  # GPIO17
            logging.info("HardwareController: Initialized Button on GPIO17.")
            self.space_button.when_pressed = self.on_button_pressed
        except Exception as e:
            logging.error(f"HardwareController: Failed to initialize Button on GPIO17: {e}")
            raise

    def on_button_pressed(self):
        """
        Callback for space button press event. Adds an event to the external queue in a thread-safe manner.
        """
        current_time = time.time()
        if current_time - self.last_press_time < self.debounce_interval:
            logging.warning("HardwareController: Button press ignored due to debounce.")
            return
        self.last_press_time = current_time

        logging.info("HardwareController: Button pressed. Scheduling event to external queue.")
        try:
            # Determine the next command based on the last button press
            if self.last_button_press == "enter":
                command = "r"
                self.last_button_press = "r"
                logging.info("HardwareController: Scheduling 'r' to external queue.")
            else:
                command = "enter"
                self.last_button_press = "enter"
                logging.info("HardwareController: Scheduling 'enter' to external queue.")

            # Schedule the command to be put in the asyncio.Queue
            future = asyncio.run_coroutine_threadsafe(
                self.external_queue.put(command), self.loop
            )

            # Optionally, check if the future was successful
            result = future.result(timeout=1)
            logging.info(f"HardwareController: Successfully enqueued command '{command}'. Queue size: {self.external_queue.qsize()}")
        except Exception as e:
            logging.error(f"HardwareController: Failed to schedule event to external queue: {e}")

    def close(self):
        """
        Cleans up the hardware components.
        """
        logging.info("HardwareController: Closing HardwareController...")
        self.space_button.close()
        logging.info("HardwareController: Button on GPIO17 closed.")