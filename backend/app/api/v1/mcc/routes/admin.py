from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from app.api.v1.mcc.schemas.requests import UpdateAdminRequestStatusRequest
from app.api.v1.mcc.schemas.responses import PendingAdminRequestsResponse, UserInformationResponse
from app.data.data_wrappers.wrappers import MCCUsersWrapper
from app.data.enums.mcc_users import MCCAdminRequestStatus
from app.data.models.mcc_user_models import MCCUsers
from app.mcc_keycloak.client import keycloak

admin_router = APIRouter(tags=["MCC", "Admin"])


def _to_user_information_response(user: MCCUsers) -> UserInformationResponse:
    """
    Serializes an MCCUsers row into its API response representation.

    :param user: the MCC user to serialize.
    :return: the serialized user information.
    """
    return UserInformationResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        admin_request_status=user.admin_request_status,
    )


@admin_router.post("/request")
async def request_admin_access(user: MCCUsers = Depends(keycloak.get_current_user)) -> UserInformationResponse:
    """
    Submits a request for MCC admin access on behalf of the calling user.

    :param user: the authenticated MCC user submitting the request.
    :return: the user's updated information, including the new request status.
    """
    if user.admin_request_status == MCCAdminRequestStatus.PENDING:
        raise HTTPException(status_code=409, detail="Admin access request already pending")
    if user.admin_request_status == MCCAdminRequestStatus.APPROVED:
        raise HTTPException(status_code=409, detail="User is already an MCC admin")

    updated_user = await MCCUsersWrapper().update(user.id, {"admin_request_status": MCCAdminRequestStatus.PENDING})
    return _to_user_information_response(updated_user)


@admin_router.get("/requests", dependencies=[keycloak.require_admin])
async def get_pending_admin_requests() -> PendingAdminRequestsResponse:
    """
    Lists MCC users with a pending admin access request.

    :return: users awaiting an admin decision.
    """
    pending_users = await MCCUsersWrapper().get_all_by(admin_request_status=MCCAdminRequestStatus.PENDING)
    return PendingAdminRequestsResponse(data=[_to_user_information_response(u) for u in pending_users])


@admin_router.patch("/requests/{user_id}", dependencies=[keycloak.require_admin])
async def update_admin_request(user_id: UUID, request: UpdateAdminRequestStatusRequest) -> UserInformationResponse:
    """
    Approves or rejects a pending MCC admin access request.

    :param user_id: the MCC user whose request is being decided.
    :param request: the admin's decision.
    :return: the user's updated information.
    """
    try:
        target_user = await MCCUsersWrapper().get_by_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="User not found") from e

    if target_user.admin_request_status != MCCAdminRequestStatus.PENDING:
        raise HTTPException(status_code=409, detail="User does not have a pending admin access request")

    if request.status == MCCAdminRequestStatus.APPROVED:
        await keycloak.grant_mcc_admin(user_id)  # Grant before DB write: Keycloak failure must leave request PENDING.

    updated_user = await MCCUsersWrapper().update(user_id, {"admin_request_status": request.status})
    return _to_user_information_response(updated_user)
