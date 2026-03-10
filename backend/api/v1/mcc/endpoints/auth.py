from data.data_wrappers.wrappers import MCCUsersWrapper
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from keycloak.client import keycloak

mcc_auth_router = APIRouter(tags=["MCC", "Authentication"])


@mcc_auth_router.get("/login")
def login() -> None:
    """
    Login endpoint
    """
    print(keycloak.login_url)
    RedirectResponse(url=keycloak.login_url)


@mcc_auth_router.get("/callback")
def callback(code: str) -> dict[str, str]:
    """
    Callback endpoint redirected to by keycloak for tokens
    """
    tokens = keycloak.get_tokens(code)
    user_info = keycloak.decode_id_token(tokens["id_token"])
    try:
        MCCUsersWrapper().get_by_id(user_info["sub"])
    except ValueError:
        MCCUsersWrapper().create({"id": user_info["sub"], "email": user_info["email"], "phone_number": ""})
    return {"id_token": tokens["id_token"], "access_token": tokens["access_token"]}
