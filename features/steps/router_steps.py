from typing import List

from behave import when, then
from behave.model import Table, Row

from deepdiff import DeepDiff

from galactic_router.events import RegisterEvent, DeregisterEvent, RouteEvent
import galactic_router.proto.remote_pb2 as pb


@when(u'a register event is received from "{worker}" for network "{network}" and endpoint "{endpoint}"')
async def step_when_register(context, worker, network, endpoint):
    await context.bus.dispatch(RegisterEvent(
        worker = worker,
        envelope = pb.Register(network=network, srv6_endpoint=endpoint),
    ))


@then('{n:d} route was published')
@then('{n:d} routes were published')
def step_then_count(context, n):
    routes = context.collector.route
    assert len(routes) == n, f"expected {n} routes, got {len(routes)}"


@then('the route is as follows:')
@then('the routes are as follows:')
def step_then_add_with_segments(context):
    compare_table_to_routes(context.table, context.collector.route)


def compare_table_to_routes(table: Table, routes: List[RouteEvent]) -> None:
    assert table is not None, "table is None"
    assert routes is not None, "routes is None"

    headings = [ "worker", "network", "endpoint", "segments", "status" ]
    assert headings == table.headings, f"headings do not match: {", ".join(headings)}"

    routes_table = Table(headings, [
        Row(
            headings,
            [
                route.worker,
                route.envelope.network,
                route.envelope.srv6_endpoint,
                ",".join(route.envelope.srv6_segments),
                pb.Route.Status.Name(route.envelope.status),
            ]
        )
        for route in routes
    ])

    diff_res = DeepDiff(
        table,
        routes_table,
        ignore_order=True,
    )
    if diff_res != {}:
        raise AssertionError(diff_res)
