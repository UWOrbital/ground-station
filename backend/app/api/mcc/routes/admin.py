from typing import Annotated, Final
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from app.api.mcc.schemas.requests import UpdateAdminRequestStatusRequest
from app.api.mcc.schemas.responses import AdminApplicantsResponse, UserInformationResponse
from app.data.enums.mcc_users import MCCAdminRequestStatus
from app.data.models.mcc_user_models import MCCUsers
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import MCCUsersRepository
from app.mcc_keycloak.client import keycloak

admin_router = APIRouter(tags=["MCC", "Admin"])

MCCUsersRepo = Annotated[MCCUsersRepository, Depends(DAL.get_repo(DAL.mcc_users))]

REQUEST_ACCESS_CONFLICT_DETAILS: Final[dict[MCCAdminRequestStatus, str]] = {
    MCCAdminRequestStatus.PENDING: "Admin access request already pending",
    MCCAdminRequestStatus.APPROVED: "User is already an MCC admin",
    MCCAdminRequestStatus.REJECTED: "Admin access request was already rejected",
}


@admin_router.post("/request-access")
async def request_admin_access(
    mcc_users: MCCUsersRepo,
    user: MCCUsers = Depends(keycloak.get_current_user),
) -> UserInformationResponse:
    """
    Submits a request for MCC admin access on behalf of the calling user.

    :param mcc_users: injected MCCUsers repository.
    :param user: the authenticated MCC user submitting the request.
    :return: the user's updated information, including the new request status.
    """
    if user.admin_request_status != MCCAdminRequestStatus.NOT_REQUESTED:
        raise HTTPException(status_code=409, detail=REQUEST_ACCESS_CONFLICT_DETAILS[user.admin_request_status])

    updated_user = await mcc_users.update(user.id, {"admin_request_status": MCCAdminRequestStatus.PENDING})
    return UserInformationResponse.model_validate(updated_user, from_attributes=True)


@admin_router.get("/applicants", dependencies=[keycloak.require_admin])
async def get_admin_applicants(mcc_users: MCCUsersRepo) -> AdminApplicantsResponse:
    """
    Lists MCC users with a pending admin access request.

    :param mcc_users: injected MCCUsers repository.
    :return: users awaiting an admin decision.
    """
    pending_users = await mcc_users.get_all_by(admin_request_status=MCCAdminRequestStatus.PENDING)
    return AdminApplicantsResponse(
        data=[UserInformationResponse.model_validate(u, from_attributes=True) for u in pending_users]
    )


@admin_router.patch("/applicants/{user_id}", dependencies=[keycloak.require_admin])
async def decide_admin_applicant(
    user_id: UUID,
    request: UpdateAdminRequestStatusRequest,
    mcc_users: MCCUsersRepo,
) -> UserInformationResponse:
    """
    Approves or rejects a pending MCC admin access request.

    :param user_id: the MCC user whose request is being decided.
    :param request: the admin's decision.
    :param mcc_users: injected MCCUsers repository.
    :return: the user's updated information.
    """
    try:
        target_user = await mcc_users.get_by_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="User not found") from e

    if target_user.admin_request_status != MCCAdminRequestStatus.PENDING:
        raise HTTPException(status_code=409, detail="User does not have a pending admin access request")

    if request.status == MCCAdminRequestStatus.APPROVED:
        await keycloak.grant_mcc_admin(user_id)  # Grant before DB write: Keycloak failure must leave request PENDING.

    updated_user = await mcc_users.update(user_id, {"admin_request_status": request.status})
    return UserInformationResponse.model_validate(updated_user, from_attributes=True)
