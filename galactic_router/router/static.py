from bubus import EventBus
from . import BaseRouter
from ..events import RegisterEvent, DeregisterEvent, RouteEvent
from ..proto import remote_pb2 as pb


class StaticRouter(BaseRouter):
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        super().__init__(bus)

    async def stop(self) -> None:
        pass

    async def handle_register(self, event: RegisterEvent) -> bool:
        match event.worker:
            case 'node1':
                pass
            case 'node2':
                await self.bus.dispatch(StaticRouter.create_route("node1", "10.1.1.2/32", "2001::1", ["2001::2"], "ADD"))
                await self.bus.dispatch(StaticRouter.create_route("node2", "10.1.1.1/32", "2001::2", ["2001::1"], "ADD"))
            case 'node3':
                await self.bus.dispatch(StaticRouter.create_route("node3", "10.1.1.2/32", "2001::3", ["2001::2"], "ADD"))
                await self.bus.dispatch(StaticRouter.create_route("node3", "10.1.1.1/32", "2001::3", ["2001::1"], "ADD"))
                await self.bus.dispatch(StaticRouter.create_route("node1", "10.1.1.3/32", "2001::1", ["2001::3"], "ADD"))
                await self.bus.dispatch(StaticRouter.create_route("node2", "10.1.1.3/32", "2001::2", ["2001::3"], "ADD"))
        return True

    async def handle_deregister(self, event: DeregisterEvent) -> bool:
        return True

    async def handle_route(self, event: RouteEvent) -> bool:
        return True

    def create_route(worker, network, srv6_endpoint, srv6_segments, status):
        return RouteEvent(
            worker=worker,
            envelope=pb.Route(
                network=network,
                srv6_endpoint=srv6_endpoint,
                srv6_segments=srv6_segments,
                status=pb.Route.Status.Value(status),
            ),
        )
