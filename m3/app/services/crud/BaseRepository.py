### BaseRepository.py — example/app/services/crud/BaseRepository.py
from typing import Generic, TypeVar, Type
from sqlmodel import Session, select

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, session: Session, service: Type[T]):
        self.session = session
        self.service = service

    def create_entity(self, **kwargs) -> T:
        entity = self.service(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update_entity_status(self, entity: T, status: str):
        entity.status = status
        self.session.add(entity)

    def get_user_entities(self, user_id: int) -> list[T]:
        return self.session.exec(
            select(self.service).where(self.service.user_id == user_id)
        ).all()
