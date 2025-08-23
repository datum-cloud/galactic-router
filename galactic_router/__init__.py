import logging
import asyncio
import aiorun

import click
from bubus import EventBus
from sqlmodel import SQLModel, create_engine

from .router.static import StaticRouter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")

@click.command()
@click.option('--db_url', envvar="DB_URL", default="sqlite:///galactic-router.db", help='Database connection URL')
@click.option('--db_create', envvar="DB_CREATE", default=True, help='Create database schema')
def run(db_url, db_create):
    logger.info("Starting")

    bus = EventBus()

    db_engine = create_engine(db_url)
    if db_create:
        SQLModel.metadata.create_all(db_engine)
    router = StaticRouter(bus, db_engine)

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
