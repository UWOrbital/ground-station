from data.data_wrappers.wrappers import MCCUsersWrapper
from fastapi import APIRouter, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse, Response
from keycloak.exceptions import KeycloakError
from mcc_keycloak.client import keycloak
from sqlalchemy.exc import IntegrityError

mcc_auth_router = APIRouter(tags=["MCC", "Authentication"])


@mcc_auth_router.get("/ping", dependencies=[keycloak.require_auth])
def ping() -> dict[str, str]:
    """
    Simple ping endpoint to verify that user is authenticated.
    """
    return {"status": "authenticated"}


@mcc_auth_router.get("/login")
def login() -> RedirectResponse:
    """
    Login endpoint for redirecting to keycloak's login/registration page
    """
    return RedirectResponse(url=keycloak.login_url, status_code=303)


@mcc_auth_router.get("/callback")
def auth_token_callback(code: str) -> Response:
    """
    Callback endpoint redirected to by keycloak for tokens
    """
    try:
        tokens = keycloak.get_tokens(code)
    except (KeycloakError, ValueError) as e:
        raise HTTPException(status_code=401, detail="Token exchange failed") from e
    user_info = keycloak.decode_token(tokens["id_token"])
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

    response = Response(
        status_code=302,
        headers={"location": keycloak.config.redirect_uri},
    )

    response.set_cookie(
        "id_token", tokens["id_token"], httponly=True, secure=keycloak.config.secure_cookies, samesite="lax", path="/"
    )
    response.set_cookie(
        "access_token",
        tokens["access_token"],
        httponly=True,
        secure=keycloak.config.secure_cookies,
        samesite="lax",
        path="/",
    )

    return response


@mcc_auth_router.get("/logout")
def logout(request: Request) -> RedirectResponse:
    """
    Log-out endpoint for removing tokens from users.
    """
    id_token = request.cookies.get("id_token")
    url = keycloak.logout_url(id_token) if id_token else keycloak.config.redirect_uri
    response = RedirectResponse(url=url)
    response.delete_cookie("id_token")
    response.delete_cookie("access_token")
    return response
