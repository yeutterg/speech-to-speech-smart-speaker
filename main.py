import asyncio
import logging
import signal
from hardware import HardwareController

# Configure logging for main module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [Main] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

async def handle_events(external_queue: asyncio.Queue):
    """
    Coroutine to handle events from the external queue.
    """
    while True:
        event = await external_queue.get()
        logging.info(f"Event received: {event}")
        # Add your event handling logic here
        # For example:
        if event == "space_pressed":
            logging.info("Space button was pressed!")
            # Perform actions in response to the button press

async def shutdown(signal, loop):
    """
    Cleanup tasks tied to the service's shutdown.
    """
    logging.info(f"Received exit signal {signal.name}...")
    logging.info("Closing HardwareController...")
    controller.close()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    list(map(lambda t: t.cancel(), tasks))
    logging.info("Cancelling outstanding tasks...")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

async def main():
    """
    Main coroutine to set up hardware controller and event handling.
    """
    global controller
    external_queue = asyncio.Queue()
    use_mock = False  # Set to True for testing without actual hardware

    controller = HardwareController(external_queue, use_mock=use_mock)

    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for s in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s, loop))
        )

    # Start handling events
    await handle_events(external_queue)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Application shutdown requested.")
