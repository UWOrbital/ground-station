from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse, Response
from keycloak.exceptions import KeycloakError
from sqlalchemy.exc import IntegrityError

from app.data.repositories.dal import DAL
from app.data.repositories.repositories import MCCUsersRepository
from app.mcc_keycloak.client import keycloak

mcc_auth_router = APIRouter(tags=["MCC", "Authentication"])


@mcc_auth_router.get("/ping", dependencies=[keycloak.require_auth])
async def ping() -> dict[str, str]:
    """
    Simple ping endpoint to verify that user is authenticated.
    """
    return {"status": "authenticated"}


@mcc_auth_router.get("/login")
async def login() -> RedirectResponse:
    """
    Login endpoint for redirecting to keycloak's login/registration page
    """
    # keycloak.login_url internally makes a synchronous well-known HTTP call; offload it
    # so it doesn't block the event loop.
    login_url = await run_in_threadpool(lambda: keycloak.login_url)
    return RedirectResponse(url=login_url, status_code=303)


@mcc_auth_router.get("/callback")
async def auth_token_callback(
    code: str,
    mcc_users: Annotated[MCCUsersRepository, Depends(DAL.get_repo(DAL.mcc_users))],
) -> Response:
    """
    Callback endpoint redirected to by keycloak for tokens

    :param code: the authorization code returned by keycloak's login redirect.
    :param mcc_users: injected MCCUsers repository.
    :return: a response that sets the id/access token cookies.
    """
    try:
        tokens = await keycloak.get_tokens(code)
    except (KeycloakError, ValueError) as e:
        raise HTTPException(status_code=401, detail="Token exchange failed") from e
    user_info = await keycloak.decode_token(tokens["id_token"])
    try:
        await mcc_users.create(
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

    response = Response(
        status_code=302,
        headers={"location": keycloak.config.redirect_uri},
    )

    response.set_cookie(
        "id_token",
        tokens["id_token"],
        httponly=True,
        secure=keycloak.config.secure_cookies,
        samesite="none" if keycloak.config.secure_cookies else "lax",
        path="/",
    )
    response.set_cookie(
        "access_token",
        tokens["access_token"],
        httponly=True,
        secure=keycloak.config.secure_cookies,
        samesite="none" if keycloak.config.secure_cookies else "lax",
        path="/",
    )

    return response


@mcc_auth_router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """
    Log-out endpoint for removing tokens from users.
    """
    id_token = request.cookies.get("id_token")
    url = keycloak.logout_url(id_token) if id_token else keycloak.config.redirect_uri
    response = RedirectResponse(url=url)
    response.delete_cookie(
        "id_token",
        path="/",
        secure=keycloak.config.secure_cookies,
        samesite="none" if keycloak.config.secure_cookies else "lax",
    )
    response.delete_cookie(
        "access_token",
        path="/",
        secure=keycloak.config.secure_cookies,
        samesite="none" if keycloak.config.secure_cookies else "lax",
    )
    return response
