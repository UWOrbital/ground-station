"""
Callsign certification: score an ARO's claimed details against the government registry.

The callsign itself is a strict gate. Every other field contributes to a percentage score,
and the account is certified once that score clears settings.auth.callsign_match_pct.
"""

import usaddress
from fastapi import HTTPException, status
from loguru import logger
from collections.abc import Callable
from app.api.aro.schemas.auth.requests import CallsignRequest
from app.api.aro.schemas.types import normalize_postal_code, normalize_registry_text
from app.config.env_settings.backend_config import settings
from app.data.models.aro_user_models import AROUserCallsigns, AROUsers
from app.data.repositories.dal import DAL

Matcher = Callable[[str, str], bool]

# Abbreviations vary between the registry and what a user types ("DR"/"DRIVE", "BOX"/"PO BOX")
_IGNORED_ADDRESS_PARTS = frozenset({
    "StreetNamePreType",
    "StreetNamePostType",
    "StreetNamePreDirectional",
    "StreetNamePostDirectional",
    "USPSBoxType",
})
_TEXT_FIELDS = (
    "first_name",
    "last_name",
    "personal_city",
    "personal_province",
    "club_name",
    "second_club_name",
    "club_city",
    "club_province",
)
_POSTAL_FIELDS = ("personal_postal_code", "club_postal_code")
_ADDRESS_FIELDS = ("personal_address", "club_address")
_QUAL_LEVEL_COLUMNS = tuple(sorted(f for f in AROUserCallsigns.model_fields if f.startswith("qual_level_")))


def _text_matches(user_value: str, registry_value: str) -> bool:
    """
    Compare free text after normalizing both sides into registry shape.

    :param user_value: the value the user submitted.
    :param registry_value: the value stored in the registry.
    :return: True when the two agree.
    """
    return normalize_registry_text(user_value) == normalize_registry_text(registry_value)


def _postal_matches(user_value: str, registry_value: str) -> bool:
    """
    Compare postal codes after compacting both sides.

    :param user_value: the value the user submitted.
    :param registry_value: the value stored in the registry, which may carry stray spaces.
    :return: True when the two agree.
    """
    return normalize_postal_code(user_value) == normalize_postal_code(registry_value)


def _address_parts(value: str) -> dict[str, str]:
    """
    Tag an address into comparable components, dropping the ones that vary by abbreviation.

    :param value: an address from either side of the comparison.
    :return: the significant components, or an empty dict if the address could not be tagged.
    """
    try:
        tagged, _ = usaddress.tag(normalize_registry_text(value))
    except usaddress.RepeatedLabelError:
        return {}
    return {label: part for label, part in tagged.items() if label not in _IGNORED_ADDRESS_PARTS}


def _address_matches(user_value: str, registry_value: str) -> bool:
    """
    Compare two addresses by their parsed components.

    :param user_value: the address the user submitted.
    :param registry_value: the address stored in the registry.
    :return: True when the significant components agree.
    """
    user_parts = _address_parts(user_value)
    registry_parts = _address_parts(registry_value)
    if user_parts and registry_parts:
        return user_parts == registry_parts
    
    # Fall back to comparing the normalized text if too malformed
    return _text_matches(user_value, registry_value)


def score_callsign_match(request: CallsignRequest, record: AROUserCallsigns) -> float:
    """
    Score a request against the registry row its callsign matched.

    :param request: the user reg details
    :param record: the matched reg row
    :return: the matched fraction, between 0.0 and 1.0
    """
    field_matchers: tuple[tuple[tuple[str, ...], Matcher], ...] = (
        (_TEXT_FIELDS, _text_matches),
        (_POSTAL_FIELDS, _postal_matches),
        (_ADDRESS_FIELDS, _address_matches),
    )

    scoreboard: dict[str, int] = {"call_sign": 1}
    weights: dict[str, int] = {"call_sign": 1}

    for fields, matcher in field_matchers:
        for field in fields:
            registry_value = getattr(record, field)
            if registry_value is None:
                continue

            user_value = getattr(request, field)

            weights[field] = 1
            scoreboard[field] = 1 if user_value is not None and matcher(user_value, registry_value) else 0

    # A matching club name makes the second one redundant
    if scoreboard.get("club_name") == 1:
        scoreboard.pop("second_club_name", None)

    registry_levels = [getattr(record, column) for column in _QUAL_LEVEL_COLUMNS]
    scoreboard["qual_levels"] = sum(
        user_level == registry_level
        for user_level, registry_level in zip(
            request.qual_levels,
            registry_levels,
            strict=True
        )
    )
    weights["qual_levels"] = len(registry_levels)

    return sum(scoreboard.values()) / sum(weights[field] for field in scoreboard)


async def verify_user_callsign(request: CallsignRequest, user: AROUsers) -> AROUsers:
    """
    Certify a user's callsign and record the result when the match clears the threshold.

    :param request: the user's claimed registry details
    :param user: the ARO user being certified
    :return: the updated user
    """

    # If callsign does not match this query does not match
    record = await DAL.aro_user_callsigns().get_row_by_callsign(request.call_sign)
    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Callsign unable to be verified.")

    score = score_callsign_match(request, record)
    if score < settings.auth.callsign_match_pct:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Callsign unable to be verified.")

    return await DAL.aro_users().update(
        user.id,
        {
            "call_sign": request.call_sign, 
            "is_callsign_verified": True
        },
    )
