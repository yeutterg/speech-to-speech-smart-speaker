import asyncio
import logging
import signal
import requests
from hardware import HardwareController

# Configure logging for main module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [Main] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


async def handle_events(external_queue: asyncio.Queue, openai_client_url: str):
    """
    Coroutine to handle events from the external queue.
    Alternates between sending "r" and Enter commands on button presses.

    Args:
        external_queue (asyncio.Queue): Queue to receive events from HardwareController.
        openai_client_url (str): The URL of the OpenAI real-time client endpoint.
    """
    send_recording = True  # Flag to toggle between "r" and "Enter" commands

    while True:
        event = await external_queue.get()
        logging.info(f"Event received: {event}")

        if event == "space_pressed":
            if send_recording:
                command = "r"
                await send_command(command, openai_client_url)
                logging.info(f'Sent command: "{command}" to OpenAI real-time client.')
            else:
                command = "Enter"
                await send_command(command, openai_client_url)
                logging.info(f'Sent command: "{command}" to OpenAI real-time client.')
            send_recording = not send_recording  # Toggle the flag


async def send_command(command: str, openai_client_url: str):
    """
    Sends the specified command to the OpenAI real-time client.

    Args:
        command (str): The command to send ("r" or "Enter").
        openai_client_url (str): The URL of the OpenAI real-time client endpoint.
    """
    try:
        payload = {"command": command}
        headers = {"Content-Type": "application/json"}
        logging.info(f"Sending command '{command}' to OpenAI client at {openai_client_url}...")
        
        # Send the POST request asynchronously to avoid blocking the event loop
        response = await asyncio.to_thread(requests.post, openai_client_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            logging.info(f"Command '{command}' sent successfully.")
        else:
            logging.error(f"Failed to send command '{command}'. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"An error occurred while sending command '{command}': {e}")


async def shutdown(signal_name: str, loop: asyncio.AbstractEventLoop, controller: HardwareController):
    """
    Cleanup tasks tied to the service's shutdown.

    Args:
        signal_name (str): The received shutdown signal.
        loop (asyncio.AbstractEventLoop): The asyncio event loop.
        controller (HardwareController): The hardware controller instance.
    """
    logging.info(f"Received exit signal {signal_name}...")

    logging.info("Closing HardwareController...")
    controller.close()

    logging.info("Cancelling outstanding tasks...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()

    logging.info("Awaiting task cancellations...")
    await asyncio.gather(*tasks, return_exceptions=True)

    logging.info("Shutdown complete.")
    loop.stop()


async def main():
    """
    Main coroutine to set up hardware controller and event handling.
    """
    external_queue = asyncio.Queue()
    use_mock = False  # Set to False to use real hardware
    openai_client_url = "http://your-openai-client-endpoint.com/command"  # Replace with your OpenAI client endpoint

    controller = HardwareController(external_queue, use_mock=use_mock)

    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for s in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s.name, loop, controller))
        )

    logging.info("Application started. Press the button to interact.")

    # Start handling events
    await handle_events(external_queue, openai_client_url)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Application shutdown requested.")