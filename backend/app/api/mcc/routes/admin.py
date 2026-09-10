from typing import Annotated
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
REQUEST_ACCESS_CONFLICT_DETAILS = {MCCAdminRequestStatus.PENDING: "Admin access request already pending", MCCAdminRequestStatus.APPROVED: "User is already an MCC admin", MCCAdminRequestStatus.REJECTED: "Admin access request was already rejected"}

@admin_router.post("/request-access")
async def request_admin_access(mcc_users: MCCUsersRepo, user: MCCUsers = Depends(keycloak.get_current_user)) -> UserInformationResponse:
    if user.admin_request_status != MCCAdminRequestStatus.NOT_REQUESTED: raise HTTPException(409, REQUEST_ACCESS_CONFLICT_DETAILS[user.admin_request_status])
    return UserInformationResponse.model_validate(await mcc_users.update(user.id, {"admin_request_status": MCCAdminRequestStatus.PENDING}), from_attributes=True)

@admin_router.get("/applicants", dependencies=[keycloak.require_admin])
async def get_admin_applicants(mcc_users: MCCUsersRepo) -> AdminApplicantsResponse:
    return AdminApplicantsResponse(data=[UserInformationResponse.model_validate(u, from_attributes=True) for u in await mcc_users.get_all_by(admin_request_status=MCCAdminRequestStatus.PENDING)])

@admin_router.patch("/applicants/{user_id}", dependencies=[keycloak.require_admin])
async def decide_admin_applicant(user_id: UUID, request: UpdateAdminRequestStatusRequest, mcc_users: MCCUsersRepo) -> UserInformationResponse:
    try: target_user = await mcc_users.get_by_id(user_id)
    except ValueError as e: raise HTTPException(404, "User not found") from e
    if target_user.admin_request_status != MCCAdminRequestStatus.PENDING: raise HTTPException(409, "User does not have a pending admin access request")
    if request.status == MCCAdminRequestStatus.APPROVED: await keycloak.grant_mcc_admin(user_id)  # before the DB write so a Keycloak failure leaves it PENDING
    return UserInformationResponse.model_validate(await mcc_users.update(user_id, {"admin_request_status": request.status}), from_attributes=True)
