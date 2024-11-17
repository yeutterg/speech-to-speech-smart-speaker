import asyncio
from openai_realtime_client.handlers.input_handler import InputHandler
from hardware import HardwareController

async def main():
    # Create a shared asyncio.Queue for external button presses
    external_queue = asyncio.Queue()

    # Initialize InputHandler with the external queue
    input_handler = InputHandler(external_queue)
    input_handler.start()

    # Initialize HardwareController with the same external queue
    hardware_controller = HardwareController(external_queue)
    hardware_controller.start()

    try:
        # Keep the main coroutine alive while other tasks are running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        # Gracefully stop the handlers
        input_handler.stop()
        hardware_controller.stop()

# Run the main coroutine
if __name__ == "__main__":
    asyncio.run(main())