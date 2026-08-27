from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.v1.aro.auth.aro_session import get_user_by_token
from app.api.v1.aro.schemas.picture_requests.requests import CreatePictureRequest
from app.api.v1.aro.schemas.picture_requests.responses import (
    DeleteOperation,
    DownloadOperation,
    PageLink,
    PictureRequestItem,
    PictureRequestResponse,
    PictureRequestsResponse,
)
from app.config.data_values import PICTURE_REQUEST_DELETE_WINDOW
from app.data.data_wrappers.wrappers import ARORequestWrapper, PacketWrapper
from app.data.enums.aro_requests import ARORequestStatus
from app.data.models.aro_user_models import AROUsers
from app.data.models.transactional_models import ARORequest
from app.exceptions.exceptions import InvalidStateError, NotFoundError

picture_requests_router = APIRouter(tags=["ARO", "Picture Requests"])


def _is_deletable(req: ARORequest) -> bool:
    """
    Decide whether a picture request may still be deleted by its owner.

    :param req: the picture request to check.
    :return: True if the request is PENDING and still within its delete window.
    """
    return (
        req.status == ARORequestStatus.PENDING
        and req.delete_deadline is not None
        and datetime.now(UTC) < req.delete_deadline
    )


def _build_operations(request: Request, req: ARORequest) -> dict[str, DeleteOperation | DownloadOperation]:
    """
    Build the operations object exposing the actions available on a request.

    Only includes an operation when it is actually available, so the frontend
    can rely on presence alone and never has to construct URLs itself.

    :param request: the incoming request, used to resolve route URLs.
    :param req: the picture request the operations apply to.
    :return: a mapping of operation name to its link (and any constraints).
    """
    operations: dict[str, DeleteOperation | DownloadOperation] = {}

    # _is_deletable already covers this, but the local binding lets mypy narrow the deadline.
    if _is_deletable(req) and req.delete_deadline is not None:
        operations["delete"] = DeleteOperation(
            url=str(request.url_for("aro_delete_picture_request", request_id=req.id)),
            deletable_until=req.delete_deadline,
        )

    if req.packet_id is not None:
        operations["download"] = DownloadOperation(
            url=str(request.url_for("aro_download_packet", request_id=req.id)),
        )

    return operations


def _to_item(request: Request, req: ARORequest) -> PictureRequestItem:
    """
    Serialize a picture request into its response item, with operations attached.

    :param request: the incoming request, used to resolve route URLs.
    :param req: the picture request to serialize.
    :return: the response item for the request.
    """
    item = PictureRequestItem.model_validate(req)
    item.operations = _build_operations(request, req)
    return item


async def _get_owned_request(request_id: UUID, user: AROUsers) -> ARORequest:
    """
    Fetch a picture request owned by the given user, or raise 404.

    Ownership mismatches are reported as 404 (not 403) so the endpoint never
    leaks the existence of another ARO's requests.

    :param request_id: id of the picture request to fetch.
    :param user: the authenticated ARO user that must own the request.
    :return: the owned picture request.
    :raises NotFoundError: if no such request exists for this user.
    """
    try:
        req = await ARORequestWrapper().get_by_id(request_id)
    except ValueError:
        raise NotFoundError("Picture request not found.") from None

    if req.aro_id != user.id:
        raise NotFoundError("Picture request not found.")

    return req


@picture_requests_router.get("/", name="aro_list_picture_requests")
async def list_picture_requests(
    request: Request,
    count: int = Query(default=100, ge=1),
    offset: int = Query(default=0, ge=0),
    user: AROUsers = Depends(get_user_by_token),
) -> PictureRequestsResponse:
    """
    List the current ARO user's most recent picture requests.

    :param request: the incoming request, used to resolve route URLs.
    :param count: maximum number of most recent requests to return.
    :param offset: number of most recent requests to skip, for paging.
    :param user: the authenticated ARO user (injected).
    :return: a page of the user's requests plus pagination operations.
    """
    requests = await ARORequestWrapper().get_recent_by_aro(user.id, count, offset)
    items = [_to_item(request, req) for req in requests]

    operations: dict[str, PageLink] = {}
    list_url = request.url_for("aro_list_picture_requests")
    if len(requests) == count:
        operations["next"] = PageLink(url=str(list_url.include_query_params(count=count, offset=offset + count)))
    if offset > 0:
        operations["previous"] = PageLink(
            url=str(list_url.include_query_params(count=count, offset=max(offset - count, 0)))
        )

    return PictureRequestsResponse(data=items, operations=operations)


@picture_requests_router.post("/", name="aro_create_picture_request")
async def create_picture_request(
    request: Request,
    payload: CreatePictureRequest,
    user: AROUsers = Depends(get_user_by_token),
) -> PictureRequestResponse:
    """
    Create a new picture request for the current ARO user.

    :param request: the incoming request, used to resolve route URLs.
    :param payload: the coordinates for the requested picture.
    :param user: the authenticated ARO user (injected).
    :return: the created request with its id and operations.
    """
    created = await ARORequestWrapper().create(
        {
            "aro_id": user.id,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "delete_deadline": datetime.now(UTC) + PICTURE_REQUEST_DELETE_WINDOW,
        }
    )
    return PictureRequestResponse(data=_to_item(request, created))


@picture_requests_router.get("/{request_id}/packet", name="aro_download_packet")
async def download_packet(
    request_id: UUID,
    user: AROUsers = Depends(get_user_by_token),
) -> Response:
    """
    Download the uplink packet the ARO transmits to confirm a picture request.

    :param request_id: id of the picture request whose packet to download.
    :param user: the authenticated ARO user (injected).
    :return: the raw packet bytes as an octet-stream attachment.
    :raises NotFoundError: if the request (or its packet) does not exist.
    """
    req = await _get_owned_request(request_id, user)

    if req.packet_id is None:
        raise NotFoundError("No packet is available for this request.")

    packet = await PacketWrapper().get_by_id(req.packet_id)
    return Response(
        content=packet.raw_data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="request-{request_id}.bin"'},
    )


@picture_requests_router.delete("/{request_id}", name="aro_delete_picture_request")
async def delete_picture_request(
    request: Request,
    request_id: UUID,
    user: AROUsers = Depends(get_user_by_token),
) -> PictureRequestResponse:
    """
    Delete one of the current ARO user's picture requests, if it is deletable.

    :param request: the incoming request, used to resolve route URLs.
    :param request_id: id of the picture request to delete.
    :param user: the authenticated ARO user (injected).
    :return: the deleted request.
    :raises NotFoundError: if the request does not exist for this user.
    :raises InvalidStateError: if the request is no longer in a deletable state.
    """
    req = await _get_owned_request(request_id, user)

    if not _is_deletable(req):
        raise InvalidStateError("This picture request can no longer be deleted.")

    deleted = await ARORequestWrapper().delete_by_id(request_id)
    return PictureRequestResponse(data=_to_item(request, deleted))
