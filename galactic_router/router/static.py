import logging
import uuid
import ipaddress

from bubus import EventBus

from sqlmodel import SQLModel, Field, Session, select
from sqlalchemy import Index
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoResultFound

from . import BaseRouter
from ..events import RegisterEvent, DeregisterEvent, RouteEvent
from ..proto import remote_pb2 as pb


logger = logging.getLogger("StaticRouter")


class Registration(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    vpc: str = Field(index=True)
    network: str
    endpoint: str
    worker: str

    __table_args__ = (
        Index("ix_registration_vpc_network", "vpc", "network"),
    )


class StaticRouter(BaseRouter):
    def __init__(self, bus: EventBus, db_engine: Engine) -> None:
        self.bus = bus
        self.db_engine = db_engine
        super().__init__(bus)

    async def stop(self) -> None:
        pass

    async def handle_register(self, event: RegisterEvent) -> bool:
        with Session(self.db_engine) as session:
            vpc_identifier, _ = StaticRouter.extract_vpc_from_srv6_endpoint(event.envelope.srv6_endpoint)
            try:
                new_reg = session.exec(select(Registration).where(Registration.vpc == vpc_identifier, Registration.network == event.envelope.network)).one()
                new_reg.endpoint = event.envelope.srv6_endpoint
                new_reg.worker = event.worker
            except NoResultFound as e:
                new_reg = Registration(
                    vpc = vpc_identifier,
                    network = event.envelope.network,
                    endpoint = event.envelope.srv6_endpoint,
                    worker = event.worker,
                )
            logger.info(f"register {new_reg.model_dump_json()}")
            session.add(new_reg)
            for reg in session.exec(select(Registration).where(Registration.vpc == vpc_identifier)):
                await self.bus.dispatch(StaticRouter.create_route(new_reg.worker, reg.network, new_reg.endpoint, [reg.endpoint], "ADD"))
                if str(reg.network) != new_reg.network:
                    await self.bus.dispatch(StaticRouter.create_route(reg.worker, new_reg.network, reg.endpoint, [new_reg.endpoint], "ADD"))
            session.commit()
        return True

    async def handle_deregister(self, event: DeregisterEvent) -> bool:
        match event.worker:
            case 'node1':
                await self.bus.dispatch(StaticRouter.create_route("node1", "10.1.1.1/32", "2001:1::1234:1234:1234:ffff", ["2001:1::1234:1234:1234:ffff"], "DELETE"))
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
