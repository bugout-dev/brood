import base64
import json
import logging
from typing import Dict, Optional, Tuple, Union
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.exceptions import HTTPException
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from starlette.status import HTTP_401_UNAUTHORIZED
from web3login.auth import MoonstreamRegistration, to_checksum_address, verify
from web3login.exceptions import MoonstreamVerificationError

from . import actions, data, models
from .db import yield_db_read_only_session
from .settings import BOT_INSTALLATION_TOKEN, BOT_INSTALLATION_TOKEN_HEADER

logger = logging.getLogger(__name__)


class OAuth2BearerOrSignature(OAuth2):
    """
    Extended FastAPI OAuth2 middleware to support Bearer token
    and Moonstream Web3 base64 signature in one request.
    """

    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> Tuple[Optional[str], Optional[str]]:
        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or (
            scheme.lower() != "moonstream" and scheme.lower() != "bearer"
        ):
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "moonstream/bearer"},
                )
            else:
                return None, None
        return param, scheme.lower()


# Login implementation follows:
# https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
oauth2_scheme = OAuth2BearerOrSignature(tokenUrl="token")
oauth2_scheme_manual = OAuth2BearerOrSignature(tokenUrl="token", auto_error=False)


async def get_current_user(
    oauth2: Tuple[UUID, str] = Depends(oauth2_scheme),
    db_session=Depends(yield_db_read_only_session),
) -> data.UserResponse:
    """
    Middleware returns user if its token or web3 signature verified.
    """
    token = oauth2[0]
    scheme = oauth2[1]
    if token is None or token == "":
        raise HTTPException(status_code=404, detail="Access token not found")

    try:
        if scheme == "moonstream":
            payload_json = base64.decodebytes(token.encode()).decode("utf-8")
            payload = json.loads(payload_json)
            verified = verify(
                authorization_payload=payload, schema=MoonstreamRegistration
            )
            if not verified:
                logger.info("Moonstream authorization verification error")
                raise MoonstreamVerificationError()
            web3_address = payload.get("address")
            if web3_address is None:
                logger.error("Web3 address in payload could not be None")
                raise Exception()
            web3_address = to_checksum_address(web3_address)
            user = actions.get_user(session=db_session, web3_address=web3_address)

        elif scheme == "bearer":
            is_token_active, user = actions.get_current_user_by_token(
                session=db_session, token=token
            )
            if not is_token_active:
                raise actions.TokenNotActive("Access token not active")
        else:
            logger.error(f"Unaccepted authorization scheme {scheme}")
            raise Exception()

    except actions.TokenNotFound as e:
        logger.info(e)
        raise HTTPException(status_code=404, detail="Access token not found")
    except actions.TokenNotActive as e:
        logger.info(e)
        raise HTTPException(status_code=404, detail="Access token not active")
    except actions.UserNotFound as e:
        logger.info(e)
        raise HTTPException(status_code=403, detail="User authorization not found")
    except actions.UserInvalidParameters as e:
        logger.info(e)
        raise HTTPException(status_code=500)
    except MoonstreamVerificationError:
        raise HTTPException(status_code=403, detail="Signature not verified")
    except Exception:
        logger.error("Unhandled exception at get_current_user")
        raise HTTPException(status_code=500)

    return user


async def get_current_user_with_groups(
    oauth2: Tuple[UUID, str] = Depends(oauth2_scheme),
    db_session=Depends(yield_db_read_only_session),
) -> data.UserWithGroupsResponse:
    """
    Middleware returns user with groups it belongs if its token or web3 signature verified.
    """
    token = oauth2[0]
    scheme = oauth2[1]
    if token is None or token == "":
        raise HTTPException(status_code=404, detail="Access token not found")

    try:
        if scheme == "moonstream":
            payload_json = base64.decodebytes(token.encode()).decode("utf-8")
            payload = json.loads(payload_json)
            verified = verify(
                authorization_payload=payload, schema=MoonstreamRegistration
            )
            if not verified:
                logger.info("Moonstream authorization verification error")
                raise MoonstreamVerificationError()
            web3_address = payload.get("address")
            if web3_address is None:
                logger.error("Web3 address in payload could not be None")
                raise Exception()
            web3_address = to_checksum_address(web3_address)
            user_extended = actions.get_user_with_groups(
                session=db_session, web3_address=web3_address
            )

        elif scheme == "bearer":
            (
                is_token_active,
                user_extended,
            ) = actions.get_current_user_with_groups_by_token(
                session=db_session, token=token
            )
            if not is_token_active:
                raise actions.TokenNotActive("Access token not active")
        else:
            logger.error(f"Unaccepted authorization scheme {scheme}")
            raise Exception()

    except actions.TokenNotFound as e:
        logger.info(e)
        raise HTTPException(status_code=404, detail="Access token not found")
    except actions.TokenNotActive as e:
        logger.info(e)
        raise HTTPException(status_code=404, detail="Access token not active")
    except actions.UserNotFound as e:
        logger.info(e)
        raise HTTPException(status_code=403, detail="User authorization not found")
    except actions.UserInvalidParameters as e:
        logger.info(e)
        raise HTTPException(status_code=500)
    except MoonstreamVerificationError:
        raise HTTPException(status_code=403, detail="Signature not verified")
    except Exception:
        logger.error("Unhandled exception at get_current_user_with_groups")
        raise HTTPException(status_code=500)

    return user_extended


def autogenerated_user_token_check(request: Request) -> bool:
    """
    Checks installation token header for autogenerated user access.
    """
    if BOT_INSTALLATION_TOKEN is None:
        raise ValueError("BOT_INSTALLATION_TOKEN environment variable must be set")

    autogenerated_user_token = False
    installation_token_header: Optional[str] = request.headers.get(
        BOT_INSTALLATION_TOKEN_HEADER, None
    )
    if (
        installation_token_header is not None
        and BOT_INSTALLATION_TOKEN == installation_token_header
    ):
        autogenerated_user_token = True
    elif (
        installation_token_header is not None
        and BOT_INSTALLATION_TOKEN != installation_token_header
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {BOT_INSTALLATION_TOKEN_HEADER} provided",
        )
    return autogenerated_user_token


async def get_current_user_or_installation(
    request: Request,
    oauth2: Tuple[UUID, str] = Depends(oauth2_scheme_manual),
    db_session=Depends(yield_db_read_only_session),
) -> Union[models.User, bool]:
    """
    Allow access if Bugout installation token provided, if not
    check user by default.

    Because of oauth2_scheme_manual we could accept None bearer token.
    """
    scheme = oauth2[1]
    if scheme != "bearer" and scheme is not None:
        raise HTTPException(status_code=400, detail="Unaccepted scheme")

    autogenerated_user = autogenerated_user_token_check(request)
    if autogenerated_user is True:
        return True
    elif autogenerated_user is False:
        user = await get_current_user(oauth2, db_session)
        return user

    raise HTTPException(status_code=400, detail="Access denied")


async def is_token_restricted_or_installation(
    request: Request,
    oauth2: Tuple[UUID, str] = Depends(oauth2_scheme_manual),
    db_session=Depends(yield_db_read_only_session),
) -> bool:
    """
    Allow access if Bugout installation provided.

    Because of oauth2_scheme_manual we could accept None bearer token.
    """
    scheme = oauth2[1]
    if scheme != "bearer" and scheme is not None:
        raise HTTPException(status_code=400, detail="Unaccepted scheme")

    autogenerated_user = autogenerated_user_token_check(request)
    if autogenerated_user is True:
        return False  # Return token.restricted = False
    elif autogenerated_user is False:
        token_restricted = await is_token_restricted(oauth2, db_session)
        return token_restricted

    raise HTTPException(status_code=400, detail="Access denied")


async def is_token_restricted(
    oauth2: Tuple[UUID, str] = Depends(oauth2_scheme),
    db_session=Depends(yield_db_read_only_session),
) -> bool:
    token = oauth2[0]
    scheme = oauth2[1]
    if scheme != "bearer":
        raise HTTPException(status_code=400, detail="Unaccepted scheme")

    try:
        token_object = actions.get_token(session=db_session, token=token)
    except actions.TokenNotFound:
        raise HTTPException(status_code=404, detail="Access token not found")
    except Exception:
        logger.error("Unhandled exception at is_token_restricted")
        raise HTTPException(status_code=500)
    return token_object.restricted
