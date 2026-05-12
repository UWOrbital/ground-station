import httpx
from data.data_wrappers.wrappers import MCCUsersWrapper
from fastapi import APIRouter, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from keycloak.client import keycloak
from sqlalchemy.exc import IntegrityError

mcc_auth_router = APIRouter(tags=["MCC", "Authentication"])


@mcc_auth_router.get("/login")
def login() -> None:
    """
    Login endpoint for redirecting to keycloak's login/registration page
    """
    return RedirectResponse(url=keycloak.login_url)  # type: ignore[return-value]


@mcc_auth_router.get("/callback")
def auth_token_callback(code: str) -> RedirectResponse:
    """
    Callback endpoint redirected to by keycloak for tokens
    """
    try:
        tokens = keycloak.get_tokens(code)
    except (httpx.HTTPStatusError, ValueError) as e:
        raise HTTPException(status_code=401, detail="Token exchange failed") from e
    user_info = keycloak.decode_id_token(tokens["id_token"])
    try:
        MCCUsersWrapper().create(
            {
                "id": user_info["sub"],
                "email": user_info["email"],
                "phone_number": "",
            }
        )
    except IntegrityError:
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail="User provisioning failed") from e

    response = RedirectResponse(
        url="localhost:8000/docs"
    )  # TODO: Change redirect URI to frontend page, or set dynamically

    response.set_cookie("id_token", tokens["id_token"], httponly=True, secure=True, samesite="lax")
    response.set_cookie("access_token", tokens["access_token"], httponly=True, secure=True, samesite="lax")

    return response


@mcc_auth_router.get("/logout")
def logout(request: Request) -> None:
    """
    Logout endpoint for redirecting to keycloak's logout handler
    """
    id_token = request.cookies.get("id_token")
    if not id_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return RedirectResponse(url=keycloak.logout_url(id_token))  # type: ignore[return-value]
