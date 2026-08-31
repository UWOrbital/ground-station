from typing import Any
from uuid import UUID

from fastapi_users.db import BaseUserDatabase

from app.data.models.aro_user_models import AROUserLogin, AROUsers
from app.data.repositories.dal import DAL


class AROUserRecord:
    """
    Merge 1 AROUsers row and 1 AROUserLogin row into a single object shaped like fastapi_users.models.UserProtocol.
    """

    def __init__(self, user: AROUsers, login: AROUserLogin) -> None:
        self._user = user
        self._login = login

        # these 6 define the entire contract
        self.id: UUID = user.id
        self.email: str = login.email
        self.hashed_password: str = login.password
        self.is_active: bool = user.is_active

        self.is_superuser: bool = user.is_superuser
        self.is_verified: bool = False
        self.is_callsign_verified: bool = user.is_callsign_verified


class AROUserDatabaseAdapter(BaseUserDatabase[AROUserRecord, UUID]):
    """
    fastapi_users database adapter.
    """

    def __init__(self) -> None:
        self.login_repo = DAL.aro_user_logins()
        self.user_repo = DAL.aro_users()

    async def _load(self, user: AROUsers) -> AROUserRecord | None:
        """
        Given an AROUsers row, find its corresponding AROUserLogin row and merge.

        :param user: AROUsers
        :return: composite AROUserRecord | None
        """
        login = await self.login_repo.get_first_by(user_id=user.id)
        if login is None:
            # The two tables have drifted apart
            return None
        return AROUserRecord(user, login)

    async def get(self, id: UUID) -> AROUserRecord | None:  # noqa: A002 (matches BaseUserDatabase.get's own param name)
        """
        :param id: UUID: AROUsers PK
        :return: composite AROUserRecord | None
        """
        user = await self.user_repo.get_first_by(id=id)
        if user is None:
            return None
        return await self._load(user)

    async def get_by_email(self, email: str) -> AROUserRecord | None:
        """
        :param email: str
        :return: composite AROUserRecord | None
        """
        user = await self.user_repo.get_first_by(email=email)
        if user is None:
            return None
        return await self._load(user)

    async def create(self, create_dict: dict[str, Any]) -> AROUserRecord:
        """
        Create a new user across both tables.

        :param create_dict: built by UserManager.create, see API
        :return: created composite AROUserRecord
        """
        hashed_password = create_dict.pop("hashed_password")
        email = create_dict.get("email")

        user = await self.user_repo.create(create_dict)

        login_data = {
            "user_id": user.id,
            "email": email,
            "password": hashed_password,
        }
        login = await self.login_repo.create(login_data)

        return AROUserRecord(user, login)

    async def update(self, user: AROUserRecord, update_dict: dict[str, Any]) -> AROUserRecord:
        """
        Apply changed fields to whichever table actually owns each one.

        :param user: AROUserRecord
        :param update_dict: only the fields that changed
        :return: the composite record built from the rows actually written
        """
        login_update = {}
        if "hashed_password" in update_dict:
            new_hashed_password = update_dict.pop("hashed_password")
            login_update["password"] = new_hashed_password
        if "email" in update_dict:
            login_update["email"] = update_dict["email"]

        # Using _load returns AROUserRecord | None, update needs to return certainty
        updated_login = user._login
        if login_update:
            updated_login = await self.login_repo.update(user._login.id, login_update)

        updated_user = user._user
        if update_dict:
            updated_user = await self.user_repo.update(user.id, update_dict)

        return AROUserRecord(updated_user, updated_login)

    async def delete(self, user: AROUserRecord) -> AROUserRecord:  # type: ignore[override]
        """
        Delete both source rows for an AROUserRecord, returning what was deleted.

        :param user: AROUserRecord to delete.
        :return: the same record that was just deleted.
        """
        # No CASCADE on FK
        await self.login_repo.delete_by_id(user._login.id)
        await self.user_repo.delete_by_id(user.id)
        return user
