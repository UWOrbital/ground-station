from fastapi import HTTPException, status

from app.api.aro.schemas.auth.requests import CallsignRequest
from app.data.models.aro_user_models import AROUsers
from app.data.repositories.dal import DAL


async def callsign_verified(user_call_sign: str) -> bool:
    """
    Check a call sign against AROUserCallsigns.

    Exact match only, per issue this becomes % matching later.

    :user_call_sign: str: a user's provided call sign
    """
    callsigns = DAL.aro_user_callsigns()
    record = await callsigns.get_row_by_callsign(user_call_sign)
    return record is not None


async def verify_user_callsign(request: CallsignRequest, user: AROUsers) -> AROUsers:
    """
    Verify a user's callsign and update their verification status if valid.

    :request CallsignRequest
    :user AROUsers
    :returns AROUsers
    """
    if not await callsign_verified(request.call_sign):
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
