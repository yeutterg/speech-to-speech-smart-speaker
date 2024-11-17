import asyncio
import signal
import logging
from hardware import HardwareController
from openai_realtime_client.handlers.input_handler import InputHandler

# Configure logging for main module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [Main] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

async def shutdown(sig, loop, hardware: HardwareController, input_handler: InputHandler):
    logging.info(f"Main: Received exit signal {sig.name}...")
    input_handler.stop()
    hardware.close()
    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    logging.info("Main: Shutdown complete.")

async def main():
    loop = asyncio.get_running_loop()

    external_queue = asyncio.Queue()

    hardware = HardwareController(external_queue=external_queue, loop=loop, use_mock=False)

    input_handler = InputHandler(external_queue=external_queue, loop=loop)
    input_handler.start()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(shutdown(s, loop, hardware, input_handler))
        )

    logging.info("Main: System is running. Press buttons to interact.")

    try:
        while True:
            await asyncio.sleep(3600)  # Keep the main coroutine alive
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Main: Application shutdown.")