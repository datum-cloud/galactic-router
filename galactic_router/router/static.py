import ipaddress
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
                await self.bus.dispatch(StaticRouter.create_route("node1", "10.1.1.2/32", "2001:1::1234:1234:1234:ffff", ["2001:2::1234:1234:1234:ffff"], "ADD"))
                await self.bus.dispatch(StaticRouter.create_route("node2", "10.1.1.1/32", "2001:2::1234:1234:1234:ffff", ["2001:1::1234:1234:1234:ffff"], "ADD"))
            case 'node3':
                await self.bus.dispatch(StaticRouter.create_route("node3", "10.1.1.2/32", "2001:3::1234:1234:1234:ffff", ["2001:2::1234:1234:1234:ffff"], "ADD"))
                await self.bus.dispatch(StaticRouter.create_route("node3", "10.1.1.1/32", "2001:3::1234:1234:1234:ffff", ["2001:1::1234:1234:1234:ffff"], "ADD"))
                await self.bus.dispatch(StaticRouter.create_route("node1", "10.1.1.3/32", "2001:1::1234:1234:1234:ffff", ["2001:3::1234:1234:1234:ffff"], "ADD"))
                await self.bus.dispatch(StaticRouter.create_route("node2", "10.1.1.3/32", "2001:2::1234:1234:1234:ffff", ["2001:3::1234:1234:1234:ffff"], "ADD"))
        return True

    async def handle_deregister(self, event: DeregisterEvent) -> bool:
        match event.worker:
            case 'node1':
                await self.bus.dispatch(StaticRouter.create_route("node2", "10.1.1.1/32", "2001:2::1234:1234:1234:ffff", ["2001:1::1234:1234:1234:ffff"], "DELETE"))
            case 'node2':
                pass
            case 'node3':
                pass
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

    def extract_vpc_from_srv6_endpoint(endpoint: str) -> tuple[str, str]:
        addr = ipaddress.ip_address(endpoint)
        if not isinstance(addr, ipaddress.IPv6Address):
            raise ValueError(f"provided endpoint is not an IPv6 address: {endpoint}")
        endpoint_num = int(addr)
        vpc_num = (endpoint_num >> 16) & 0xFFFFFFFFFFFF      # 48 bits after dropping 16
        vpc_attachment_num = endpoint_num & 0xFFFF           # low 16 bits
        return f"{vpc_num:012x}", f"{vpc_attachment_num:04x}"
