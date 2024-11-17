import asyncio
import logging

# Configure logging for Dispatcher
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [Dispatcher] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

async def dispatcher(external_queue: asyncio.Queue, target_queues: list):
    """
    Distributes commands from external_queue to all target_queues.
    """
    logging.info("Dispatcher: Started.")
    while True:
        command = await external_queue.get()
        logging.info(f"Dispatcher: Received command: {command}")
        for q in target_queues:
            await q.put(command)
            logging.info(f"Dispatcher: Enqueued command '{command}' to {q}")
        external_queue.task_done()