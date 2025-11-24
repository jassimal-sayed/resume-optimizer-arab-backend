import asyncio
import logging

from shared import get_settings

settings = get_settings()
logger = logging.getLogger("worker")
logging.basicConfig(level=logging.INFO)


async def run_worker() -> None:
    logger.info("Worker starting (env=%s)", settings.env)
    # TODO: implement task polling and handling for embed/optimize tasks.
    while True:
        logger.info("Worker heartbeat: waiting for task implementation")
        await asyncio.sleep(10)


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
