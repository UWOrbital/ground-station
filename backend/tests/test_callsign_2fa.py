from typing import Any

import pytest
from fastapi import HTTPException

from app.api.aro.auth.services.callsign_2fa import (
    score_callsign_match,
    verify_user_callsign,
)
from app.api.aro.schemas.auth.requests import CallsignRequest
from app.data.models.aro_user_models import AROUserCallsigns
from app.data.repositories.dal import DAL

# A solo ham: the registry leaves every club column NULL, which is the case for ~96% of records.
_REGISTRY_ROW: dict[str, Any] = {
    "call_sign": "VE3ABC",
    "first_name": "BILL",
    "last_name": "MCFADDEN",
    "personal_address": '"188 MILLWOOD DRIVE"',  # the seed CSV leaves literal quotes on addresses
    "personal_city": "MIDDLE SACKVILLE",
    "personal_province": "NS",
    "personal_postal_code": "B4E2X8",
    "qual_level_a": True,
    "qual_level_b": False,
    "qual_level_c": True,
    "qual_level_d": True,
    "qual_level_e": False,
}

_FORM: dict[str, Any] = {
    "call_sign": "ve3abc",
    "first_name": "Bill",
    "last_name": "McFadden",
    "personal_address": "188 Millwood Dr.",
    "personal_city": "Middle Sackville",
    "personal_province": "ns",
    "personal_postal_code": "b4e 2x8",
    "qual_levels": [True, False, True, True, False],
}

_CLUB_COLUMNS: dict[str, Any] = {
    "club_name": "YARMOUTH AMATEUR RADIO CLUB INC",
    "second_club_name": "ATTN DAVE GARBER",
    "club_address": '"610 SOUTH PACIFIC STREET"',
    "club_city": "WINDSOR",
    "club_province": "ON",
    "club_postal_code": "N8X2W8",
}

_CLUB_FORM: dict[str, Any] = {
    "club_name": "Yarmouth Amateur Radio Club Inc.",
    "club_address": "610 South Pacific St",
    "club_city": "Windsor",
    "club_province": "on",
    "club_postal_code": "n8x 2w8",
}


def _score(
    registry_overrides: dict[str, Any] | None = None, **form_overrides: Any
) -> float:
    """Score a submitted form against the registry row, overriding either side per test."""
    record = AROUserCallsigns(**{**_REGISTRY_ROW, **(registry_overrides or {})})
    return score_callsign_match(
        CallsignRequest.model_validate({**_FORM, **form_overrides}), record
    )


def test_empty_registry_columns_do_not_dilute_the_score() -> None:
    """A solo ham scores 1.0: NULL registry columns leave the scoreboard rather than counting as failures."""
    assert _score() == pytest.approx(1.0)


def test_populated_column_the_user_omits_scores_zero() -> None:
    """When the registry holds a value the user didn't supply, the field stays in the denominator at 0."""
    assert _score(personal_city=None) == pytest.approx(11 / 12)


def test_qual_levels_are_worth_one_point_each() -> None:
    """Qual levels carry a weight of 5, so three correct of five costs two points rather than one."""
    assert _score(qual_levels=[True] * 5) == pytest.approx(10 / 12)


def test_second_club_name_only_counts_when_the_club_name_misses() -> None:
    """A matching club name drops second_club_name from the denominator; a miss keeps it in, scoring 0."""
    assert _score(_CLUB_COLUMNS, **_CLUB_FORM) == pytest.approx(1.0)
    assert _score(
        _CLUB_COLUMNS, **{**_CLUB_FORM, "club_name": "Some Other Club"}
    ) == pytest.approx(16 / 18)


@pytest.mark.parametrize(
    ("registry_address", "form_address"),
    [
        (
            '"188 MILLWOOD DRIVE"',
            "188 Millwood Dr.",
        ),  # seed-CSV quotes, and DRIVE vs DR
        (
            '"476, RUE DE L\'ERABLIERE"',
            "476, rue de l'Érablière",
        ),  # French street type and accents
        ('"PO BOX 33"', "Box 33"),  # PO BOX vs BOX
    ],
)
def test_address_survives_registry_and_abbreviation_noise(
    registry_address: str, form_address: str
) -> None:
    """Addresses match once parsed, despite stored quotes, abbreviations, accents and French forms."""
    assert _score(
        {"personal_address": registry_address}, personal_address=form_address
    ) == pytest.approx(1.0)


def test_a_different_street_number_does_not_match() -> None:
    """Ignoring street type and directionals must not make every address match."""
    assert _score(personal_address="189 Millwood Dr") == pytest.approx(11 / 12)


async def test_certifies_the_user_when_the_score_clears_the_threshold() -> None:
    """A strong match flips is_callsign_verified and stores the callsign."""
    callsigns = DAL.aro_user_callsigns()
    users = DAL.aro_users()
    await callsigns.create(_REGISTRY_ROW)
    user = await users.create({"email": "solo@test.com", "first_name": "Bill"})

    updated_user = await verify_user_callsign(
        CallsignRequest.model_validate(_FORM), user, callsigns, users
    )

    assert updated_user.is_callsign_verified is True
    assert updated_user.call_sign == "VE3ABC"


async def test_certification_is_persisted_on_the_user_row() -> None:
    """The verified flag is written to the ARO user, not to the callsign registry row it was matched against."""
    callsigns = DAL.aro_user_callsigns()
    users = DAL.aro_users()
    await callsigns.create(_REGISTRY_ROW)
    user = await users.create({"email": "persisted@test.com", "first_name": "Bill"})

    await verify_user_callsign(
        CallsignRequest.model_validate(_FORM), user, callsigns, users
    )

    stored_user = await users.get_by_id(user.id)
    assert stored_user.is_callsign_verified is True
    assert stored_user.call_sign == "VE3ABC"


async def test_rejects_a_callsign_that_is_not_in_the_registry() -> None:
    """An unknown callsign fails the strict gate before any scoring happens."""
    callsigns = DAL.aro_user_callsigns()
    users = DAL.aro_users()
    user = await users.create({"email": "unknown@test.com", "first_name": "Bill"})

    with pytest.raises(HTTPException) as exc_info:
        await verify_user_callsign(
            CallsignRequest.model_validate({**_FORM, "call_sign": "VE3ZZZ"}),
            user,
            callsigns,
            users,
        )

    assert exc_info.value.status_code == 401
    assert user.is_callsign_verified is False


async def test_rejects_a_match_below_the_threshold() -> None:
    """The callsign alone clears the gate but not the threshold, so nothing is certified."""
    callsigns = DAL.aro_user_callsigns()
    users = DAL.aro_users()
    await callsigns.create(_REGISTRY_ROW)
    user = await users.create({"email": "weak@test.com", "first_name": "Bill"})
    weak_form = {
        **_FORM,
        "first_name": "Jane",
        "last_name": "Doe",
        "personal_address": "1 Other St",
        "personal_city": "Toronto",
        "personal_province": "on",
        "personal_postal_code": "m5v 1a1",
        "qual_levels": [False, True, False, False, True],
    }

    with pytest.raises(HTTPException) as exc_info:
        await verify_user_callsign(
            CallsignRequest.model_validate(weak_form), user, callsigns, users
        )

    assert exc_info.value.status_code == 401
    assert user.is_callsign_verified is False
