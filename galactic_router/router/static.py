import logging
import uuid
import ipaddress

from bubus import EventBus

from sqlmodel import SQLModel, Field, Session, select
from sqlalchemy import Index
from sqlalchemy.engine import Engine

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
        self.session = Session(db_engine)
        super().__init__(bus)

    async def stop(self) -> None:
        if self.session is not None:
            self.session.close()

    async def handle_register(self, event: RegisterEvent) -> bool:
        vpc_identifier, _ = StaticRouter.extract_vpc_from_srv6_endpoint(
            event.envelope.srv6_endpoint
        )

        cur_reg = self.session.exec(select(Registration).where(
            Registration.vpc == vpc_identifier,
            Registration.network == event.envelope.network,
        )).one_or_none()
        new_reg = Registration(
            vpc=vpc_identifier,
            network=event.envelope.network,
            endpoint=event.envelope.srv6_endpoint,
            worker=event.worker,
        )

        if cur_reg is not None:
            await self.handle_deregister(DeregisterEvent(
                worker=cur_reg.worker,
                envelope=pb.Deregister(
                    network=cur_reg.network,
                    srv6_endpoint=cur_reg.endpoint,
                )
            ))

        logger.info(f"register {new_reg.model_dump_json()}")
        # new registration to new worker
        await self.bus.dispatch(
            StaticRouter.create_route(
                new_reg.worker,
                new_reg.network,
                new_reg.endpoint,
                [new_reg.endpoint],
                "ADD"
            )
        )
        for reg in self.session.exec(
            select(Registration)
                .where(
                    Registration.vpc == vpc_identifier,
                    Registration.network != new_reg.network,
                )
        ):
            # existing registration to new worker
            await self.bus.dispatch(
                StaticRouter.create_route(
                    new_reg.worker,
                    reg.network,
                    new_reg.endpoint,
                    [reg.endpoint],
                    "ADD"
                )
            )
            # new registration to existing worker
            await self.bus.dispatch(
                StaticRouter.create_route(
                    reg.worker,
                    new_reg.network,
                    reg.endpoint,
                    [new_reg.endpoint],
                    "ADD"
                )
            )

        self.session.add(new_reg)
        self.session.commit()
        return True

    async def handle_deregister(self, event: DeregisterEvent) -> bool:
        vpc_identifier, _ = StaticRouter.extract_vpc_from_srv6_endpoint(
            event.envelope.srv6_endpoint
        )
        current_reg = self.session.exec(select(Registration).where(
            Registration.vpc == vpc_identifier,
            Registration.network == event.envelope.network,
            Registration.endpoint == event.envelope.srv6_endpoint,
            Registration.worker == event.worker,
        )).one_or_none()
        if current_reg is None:
            logger.warning(
                f"could not find registration: "
                f"vpc={vpc_identifier}, "
                f"network={event.envelope.network}, "
                f"endpoint={event.envelope.srv6_endpoint}, "
                f"worker={event.worker}"
            )
            return False

        logger.info(f"deregister {current_reg.model_dump_json()}")
        for reg in self.session.exec(
            select(Registration)
                .where(Registration.vpc == vpc_identifier)
        ):
            await self.bus.dispatch(
                StaticRouter.create_route(
                    reg.worker,
                    current_reg.network,
                    reg.endpoint,
                    [current_reg.endpoint],
                    "DELETE"
                )
            )
        self.session.delete(current_reg)
        self.session.commit()
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
            raise ValueError(
                f"provided endpoint is not an IPv6 address: {endpoint}"
            )
        endpoint_num = int(addr)
        # 48 bits after dropping 16
        vpc_num = (endpoint_num >> 16) & 0xFFFFFFFFFFFF  # noqa: WPS432
        # low 16 bits
        vpc_attachment_num = endpoint_num & 0xFFFF  # noqa: WPS432
        return f"{vpc_num:012x}", f"{vpc_attachment_num:04x}"
