from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.data.enums.aro_requests import ARORequestStatus

# -----------------------------------------------------------------
# Operation links (HATEOAS-style, per the endpoint conventions)
# -----------------------------------------------------------------


class DeleteOperation(BaseModel):
    """
    The `delete` operation available on a deletable picture request.
    """

    url: str
    deletable_until: datetime


class DownloadOperation(BaseModel):
    """
    The `download` operation available when a request has an uplink packet.
    """

    url: str


class PageLink(BaseModel):
    """
    A pagination link (e.g. `next`/`previous`) in a list response.
    """

    url: str


# -----------------------------------------------------------------
# Picture Request Responses
# -----------------------------------------------------------------


class PictureRequestItem(BaseModel):
    """
    A single ARO picture request, plus the operations that can be performed on it.
    """

    model_config = {"from_attributes": True}

    id: UUID
    aro_id: UUID | None = None
    latitude: Decimal
    longitude: Decimal
    created_on: datetime
    request_sent_to_obc_on: datetime | None = None
    pic_taken_on: datetime | None = None
    pic_transmitted_on: datetime | None = None
    delete_deadline: datetime | None = None
    packet_id: UUID | None = None
    status: ARORequestStatus
    operations: dict[str, DeleteOperation | DownloadOperation] = Field(default_factory=dict)


class PictureRequestResponse(BaseModel):
    """
    Single picture request response model.
    """

    data: PictureRequestItem


class PictureRequestsResponse(BaseModel):
    """
    Paginated list of picture requests response model.
    """

    data: list[PictureRequestItem]
    operations: dict[str, PageLink] = Field(default_factory=dict)
