import logging
import asyncio
import aiorun

import click
from sqlmodel import SQLModel, create_engine

from .bus import EventBus
from .router.static import StaticRouter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


@click.command()
@click.option(
    '--db_url',
    envvar="DB_URL",
    default="sqlite:///galactic-router.db",
    help='Database connection URL'
)
@click.option(
    '--db_create',
    envvar="DB_CREATE",
    default=True,
    help='Create database schema'
)
def run(db_url, db_create):
    logger.info("Starting")

    bus = EventBus()

    db_engine = create_engine(db_url)
    if db_create:
        SQLModel.metadata.create_all(db_engine)
    router = StaticRouter(bus, db_engine)

    async def spawn(*services):  # noqa: WPS430
        await asyncio.gather(*services)
    aiorun.run(spawn(bus.run(), router.run()))

    logger.info("Stopped")
