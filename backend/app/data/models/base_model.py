from typing import Any

from sqlmodel import SQLModel
from sqlmodel._compat import SQLModelConfig


class BaseSQLModel(SQLModel):
    """
    Base SQL Model class. It performs validation on the model unlike the default SQLModel class with table=True.
    """

    model_config = SQLModelConfig(validate_assignment=True)

    def __init__(self, **data: dict[str, Any]) -> None:
        is_table = self.model_config.get("table", False)
        self.model_config["table"] = False
        super().__init__(**data)
        self.model_config["table"] = is_table
