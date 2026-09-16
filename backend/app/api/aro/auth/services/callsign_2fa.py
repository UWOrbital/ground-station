from fastapi import HTTPException, status

from app.api.aro.schemas.auth.requests import CallsignRequest
from app.data.models.aro_user_models import AROUsers, AROUserCallsigns
from app.data.repositories.dal import DAL


async def callsign_verified(
    call_sign: str,
    first_name: str | None,
    last_name: str | None,
    personal_address: str | None,
    personal_city: str | None,
    qual_levels: list[bool],
    club_name: str | None,
    second_club_name: str | None,
    club_address: str | None,
    club_city: str | None,
    club_province: str | None,
    club_postal_code: str | None,
) -> tuple[bool, int]:
    """
    Check a call sign against AROUserCallsigns.

    Exact match only, per issue this becomes % matching later.

    :user_call_sign: str | None: a user's provided call sign
    """
    callsigns = DAL.aro_user_callsigns()

    callsign_record = await callsigns.get_row_by_callsign(call_sign)
    if callsign_record is None:
        return False, -1

    


async def verify_user_callsign(request: CallsignRequest, user: AROUsers) -> AROUsers:
    """
    Verify a user's callsign and update their verification status if valid.

    :request CallsignRequest
    :user AROUsers
    :returns AROUsers
    """
    callsign_request_package = {
        "call_sign": request.call_sign,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "personal_address": request.personal_address,
        "personal_city": request.personal_city,
        "qual_levels": [
            request.qual_level_a,
            request.qual_level_b,
            request.qual_level_c,
            request.qual_level_d,
            request.qual_level_e,
        ],
        "club_name": request.club_name,
        "second_club_name": request.club_name,
        "club_address": request.club_address,
        "club_city": request.club_city,
        "club_province": request.club_province,
        "club_postal_code": request.club_postal_code,
    }

    if not await callsign_verified(**callsign_request_package):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Callsign unable to be verified.")

    users = DAL.aro_users()
    updated_user = await users.update(
        user.id,
        {
            "call_sign": request.call_sign,
            "is_callsign_verified": True,
        },
    )

    return updated_user
