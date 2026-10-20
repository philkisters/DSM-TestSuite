from dsm_db import Group
from sqlalchemy import select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class GroupExists(Exception):
    pass


def list_groups(engine: Engine) -> list[Group]:
    with Session(engine, expire_on_commit=False) as session:
        return list(session.scalars(select(Group).where(Group.archived == False).order_by(Group.name)))


def create_group(engine: Engine, name: str, vm_ip: str) -> Group:
    group = Group(name=name, vm_ip=vm_ip)
    try:
        with Session(engine, expire_on_commit=False) as session, session.begin():
            session.add(group)
    except IntegrityError:
        raise GroupExists(name)
    return group


def delete_group(engine: Engine, group_id: int) -> None:
    with Session(engine) as session, session.begin():
        session.execute(update(Group).where(Group.id == group_id).values(archived=True))
