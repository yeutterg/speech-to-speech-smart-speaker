import asyncio
from gpiozero import Button
from threading import Thread

class HardwareController:
    """
    Handles hardware button presses and communicates with InputHandler.
    """
    def __init__(self, external_queue: asyncio.Queue):
        """
        Initializes the HardwareController.

        Args:
            external_queue (asyncio.Queue): Queue to send button press events to InputHandler.
        """
        self.external_queue = external_queue
        self.running = False

        # Initialize buttons (replace GPIO pins as per your setup)
        self.space_button = Button(17)
        self.enter_button = Button(27)
        self.r_button = Button(22)
        self.q_button = Button(23)

    def button_pressed(self, button_name):
        """
        Callback when a button is pressed.

        Args:
            button_name (str): The name of the button pressed.
        """
        print(f"Button pressed: {button_name}")
        asyncio.run_coroutine_threadsafe(
            self.external_queue.put(button_name), asyncio.get_event_loop()
        )

    def start(self):
        """
        Starts monitoring hardware buttons.
        """
        self.running = True

        # Assign callbacks to button press events
        self.space_button.when_pressed = lambda: self.button_pressed('space')
        self.enter_button.when_pressed = lambda: self.button_pressed('enter')
        self.r_button.when_pressed = lambda: self.button_pressed('r')
        self.q_button.when_pressed = lambda: self.button_pressed('q')

    def stop(self):
        """
        Stops monitoring hardware buttons.
        """
        self.running = False
        self.space_button.close()
        self.enter_button.close()
        self.r_button.close()
        self.q_button.close()