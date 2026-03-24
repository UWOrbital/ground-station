from uuid import UUID

from data.data_wrappers.wrappers import ARORequestWrapper, PacketCommandsWrapper
from fastapi import APIRouter

from api.v1.aro.models.requests import PictureRequest
from api.v1.aro.models.responses import AllPictureResponse, PacketCommandResponse, PictureResponse

URL_PREFIX = "/api/v1/aro/requests"

picture_requests_router = APIRouter(tags=["ARO", "Picture Requests"])


@picture_requests_router.get("/", response_model=AllPictureResponse)
async def get(count: int = 100, offset: int = 0) -> AllPictureResponse:
    """
    Gets recent picture requests

    :return: picture requests
    """
    start_index = offset
    end_index = offset + count

    requests = ARORequestWrapper().get_all()[start_index:end_index]
    operations = []

    for request in requests:
        operation = {"delete": f"{URL_PREFIX}/{request.id}/delete", "download": f"{URL_PREFIX}/{request.id}/packet"}

        operations.append(operation)

    return AllPictureResponse(data=requests, operations=operations)


@picture_requests_router.post("/", response_model=PictureResponse)
async def create(payload: PictureRequest) -> PictureResponse:
    """
    Creates a picture request with the given payload
    :param payload: The data used to create a picture request
    :return: returns the picture request created
    """

    new_request = ARORequestWrapper().create(
        data={"aro_id": payload.aro_id, "latitude": payload.latitude, "longitude": payload.longitude}
    )

    operation = {"delete": f"{URL_PREFIX}/{new_request.id}/delete", "download": f"{URL_PREFIX}/{new_request.id}/packet"}

    return PictureResponse(data=new_request, operations=operation)


@picture_requests_router.get("/{request_id}/packet", response_model=PacketCommandResponse)
async def get_packet(request_id: UUID) -> PacketCommandResponse:
    """
    Gets the packet of a picture request

    :return: returns the picture request packet
    """

    request = ARORequestWrapper().get_by_id(request_id)
    packet = PacketCommandsWrapper().get_by_id(request.packet_id)

    return PacketCommandResponse(data=packet)


@picture_requests_router.delete("/{request_id}", response_model=PictureResponse)
async def delete(request_id: UUID) -> PictureResponse:
    """
    Deletes a picture request by id

    :return: returns the deleted picture request instance
    """

    deleted_request = ARORequestWrapper().delete_by_id(request_id)

    operation = {"download": f"{URL_PREFIX}/{deleted_request.id}/packet"}

    return PictureResponse(data=deleted_request, operations=operation)
