from abc import ABC
from typing import Any, Generic, TypeVar
from uuid import UUID

from data.database.engine import get_db_session
from data.tables.base_model import BaseSQLModel
from sqlmodel import select

T = TypeVar("T", bound=BaseSQLModel)
PK = TypeVar("PK", int, UUID)


class AbstractWrapper(ABC, Generic[T, PK]):
    """
    An Abstract Base Class for all data wrappers.
    """

    model: type[T]

    def get_all(self) -> list[T]:
        """
        Get all data wrapper for the unspecified model

        :return: a list of all model instances
        """
        with get_db_session() as session:
            return list(session.exec(select(self.model)).all())

    def get_all_by(self, **kwargs: object) -> list[T]:
        """
        Get all data wrapper for the unspecified model by fields

        :param kwargs: fields to search by
        :return: a list of all model instances matching the fields
        """
        with get_db_session() as session:
            return list(session.exec(select(self.model).filter_by(**kwargs)).all())

    def get_by_id(self, obj_id: PK) -> T:
        """
        Retrieve data wrapper for the unspecified model

        :param obj_id: PK of the model instance to be retrieved
        :return: the retrieved instance
        """
        with get_db_session() as session:
            obj = session.get(self.model, obj_id)
            if not obj:
                raise ValueError(f"{self.model.__name__} with ID {obj_id} not found.")
            return obj

    def create(self, data: dict[str, Any]) -> T:
        """
        Post data wrapper for the unspecified model

        :param data: the JSON object of the model instance to be created
        :return: the newly created instance
        """
        with get_db_session() as session:
            obj = self.model(**data)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj

    def delete_by_id(self, obj_id: PK) -> T:
        """
        Delete data wrapper for the unspecified model

        :param obj_id: PK of the model instance to be deleted
        :return: the deleted instance
        """
        with get_db_session() as session:
            obj = session.get(self.model, obj_id)
            if not obj:
                raise ValueError(f"{self.model.__name__} with ID {obj_id} not found.")
            session.delete(obj)
            session.commit()
            return obj

    def update(self, obj: T) -> T:
        """
        Update data wrapper for the unspecified model

        :param obj: the model instance to be updated
        :return: the updated instance
        """
        with get_db_session() as session:
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj
