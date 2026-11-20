from dsm_db import Network
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class NetworkExists(Exception):
    pass


def get_network(engine: Engine, network_id: str) -> Network | None:
    with Session(engine, expire_on_commit=False) as session:
        return session.scalar(select(Network).where(Network.network_id == network_id))


def list_networks(engine: Engine, group_id: int) -> list[Network]:
    with Session(engine, expire_on_commit=False) as session:
        return list(
            session.scalars(
                select(Network)
                .where(Network.group_id == group_id)
                .order_by(Network.created_at.desc())
            )
        )


def create_network(
    engine: Engine,
    group_id: int,
    network_id: str,
    orchestrator_version: str,
    replication_factor: int | None,
) -> Network:
    existing = get_network(engine, network_id)
    if existing is not None:
        if (
            existing.group_id == group_id
            and existing.orchestrator_version == orchestrator_version
            and existing.replication_factor == replication_factor
        ):
            return existing
        raise NetworkExists(network_id)

    network = Network(
        group_id=group_id,
        network_id=network_id,
        orchestrator_version=orchestrator_version,
        replication_factor=replication_factor,
    )
    try:
        with Session(engine, expire_on_commit=False) as session, session.begin():
            session.add(network)
    except IntegrityError as exc:
        raise NetworkExists(network_id) from exc
    return network
