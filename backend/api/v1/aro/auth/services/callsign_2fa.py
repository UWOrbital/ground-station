from api.v1.aro.models.auth_requests import CallsignRequest
from data.data_wrappers.wrappers import AROUserCallsignWrapper, AROUsersWrapper
from data.tables.aro_user_tables import AROUsers
from fastapi import HTTPException, status


def callsign_verified(qual_levels: tuple[bool, ...], user_call_sign: str) -> bool:
    """
    Checks call_sign against the government CSV file.

    TODO: Inquire about any further specifications before return
    TODO: Use % matching on callsigns instead of hardcoded methods
    """
    callsigns = AROUserCallsignWrapper()
    record = callsigns.get_callsign(user_call_sign)

    if not record:
        return False

    expected_levels = [
        record.qual_level_a,
        record.qual_level_b,
        record.qual_level_c,
        record.qual_level_d,
        record.qual_level_e,
    ]

    for i, expected in enumerate(expected_levels):
        if qual_levels[i] != expected:
            print("\033[1;31mWARNING!\033[0m")
            print(f"Mismatch at qual_level_{chr(ord('a') + i)} for callsign {record.call_sign}.")

    return True


def verify_user_callsign(request: CallsignRequest, user: AROUsers) -> AROUsers:
    """
    Verify a user's callsign and update their verification status if valid.

    :request CallsignRequest
    :user AROUsers
    :returns AROUsers
    """

    qual_levels = (
        request.qual_level_a,
        request.qual_level_b,
        request.qual_level_c,
        request.qual_level_d,
        request.qual_level_e,
    )

    if not callsign_verified(qual_levels=qual_levels, user_call_sign=request.call_sign):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Callsign unable to be verified.")

    users = AROUsersWrapper()
    updated_user = users.update(
        user.id,
        {
            "callsign": request.call_sign,
            "is_callsign_verified": True,
        },
    )

    return updated_user
