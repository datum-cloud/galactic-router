import logging
import asyncio
import aiorun

import click
from bubus import EventBus

from .router.static import StaticRouter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("galactic-router")

@click.command()
def run():
    logger.info("Starting")
    bus = EventBus()
    router = StaticRouter(bus)
    aiorun.run(spawn(bus, router))
    logger.info("Stopped")

async def spawn(*services):
    try:
        while True:
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        for service in services:
            stop = getattr(service, "stop", None)
            if callable(stop):
                await stop()
