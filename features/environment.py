import asyncio
from typing import List

from bubus import EventBus

from galactic_router.router import BaseRouter
from galactic_router.router.static import StaticRouter
from galactic_router.events import RegisterEvent, DeregisterEvent, RouteEvent


class Collector(BaseRouter):
    def __init__(self, bus: EventBus) -> None:
        self.register: List[RegisterEvent] = []
        self.deregister: List[DeregisterEvent] = []
        self.route: List[RouteEvent] = []
        super().__init__(bus)

    async def stop(self) -> None:
        pass

    async def handle_register(self, event: RegisterEvent) -> bool:
        self.register.append(event)
        return True

    async def handle_deregister(self, event: DeregisterEvent) -> bool:
        self.deregister.append(event)
        return True

    async def handle_route(self, event: RouteEvent) -> bool:
        self.route.append(event)
        return True


def before_scenario(context, scenario):
    context.bus = EventBus()
    context.router = StaticRouter(context.bus)
    context.collector = Collector(context.bus)


def after_scenario(context, scenario):
    asyncio.run(context.bus.stop())
    asyncio.run(context.router.stop())
    asyncio.run(context.collector.stop())
