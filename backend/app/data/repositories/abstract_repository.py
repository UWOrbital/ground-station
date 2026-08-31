from abc import ABC
from typing import Any, TypeVar
from uuid import UUID

from sqlmodel import select

from app.data.database.engine import get_db_session
from app.data.models.base_model import BaseSQLModel

T = TypeVar("T", bound=BaseSQLModel)
PK = TypeVar("PK", int, UUID)


class AbstractRepository[T, PK](ABC):
    """
    An Abstract Base Class for all data repositories.
    """

    model: type[T]
    uneditable_fields: set[str] = {"id"}

    async def get_all(self) -> list[T]:
        """
        Get all data wrapper for the unspecified model

        :return: a list of all model instances
        """
        async with get_db_session() as session:
            return list((await session.exec(select(self.model))).all())

    async def get_first_by(self, **kwargs: object) -> T | None:
        """
        Retrieve the first row matching the given field(s).

        :param kwargs: fields to search by
        :return: the first matching instance, or None
        """
        async with get_db_session() as session:
            return (await session.exec(select(self.model).filter_by(**kwargs))).first()

    async def get_all_by(self, **kwargs: object) -> list[T]:
        """
        Get all data wrapper for the unspecified model by fields

        :param kwargs: fields to search by
        :return: a list of all model instances matching the fields
        """
        async with get_db_session() as session:
            return list((await session.exec(select(self.model).filter_by(**kwargs))).all())

    async def get_by_id(self, obj_id: PK) -> T:
        """
        Retrieve data wrapper for the unspecified model

        :param obj_id: PK of the model instance to be retrieved
        :return: the retrieved instance
        """
        async with get_db_session() as session:
            obj = await session.get(self.model, obj_id)
            if not obj:
                raise ValueError(f"{self.model.__name__} with ID {obj_id} not found.")
            return obj

    async def create(self, data: dict[str, Any]) -> T:
        """
        Post data wrapper for the unspecified model

        :param data: the JSON object of the model instance to be created
        :return: the newly created instance
        """
        async with get_db_session() as session:
            obj = self.model(**data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj

    async def delete_by_id(self, obj_id: PK) -> T:
        """
        Delete data wrapper for the unspecified model

        :param obj_id: PK of the model instance to be deleted
        :return: the deleted instance
        """
        async with get_db_session() as session:
            obj = await session.get(self.model, obj_id)
            if not obj:
                raise ValueError(f"{self.model.__name__} with ID {obj_id} not found.")
            await session.delete(obj)
            await session.commit()
            return obj

    async def update(self, obj_id: PK, data: dict[str, Any]) -> T:
        """
        Update data wrapper for the unspecified model

        :param obj_id: PK of the model instance to be updated
        :param data: dictionary of field names and new values
        :return: the updated instance
        """
        async with get_db_session() as session:
            obj = await session.get(self.model, obj_id)
            if not obj:
                raise ValueError(f"{self.model.__name__} with ID {obj_id} not found.")

            for field, value in data.items():
                if not hasattr(obj, field):
                    raise ValueError(f"{self.model.__name__}, field {field} not found.")

                if field in self.uneditable_fields:
                    raise ValueError(f"{self.model.__name__}, field {field} is uneditable")

                current_value = getattr(obj, field)

                if current_value and value:
                    field_type = type(current_value)
                    if not isinstance(value, field_type):
                        raise TypeError(f"{self.model.__name__}, field {field} must be of type {field_type.__name__}")

                try:
                    setattr(obj, field, value)
                except Exception as e:
                    raise RuntimeError(f"Failed to update {self.model.__name__}: {e}") from e

            await session.commit()
            return obj
