import base64
import json
import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.exceptions import HTTPException
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from starlette.status import HTTP_401_UNAUTHORIZED
from web3login.auth import MoonstreamRegistration, to_checksum_address, verify
from web3login.exceptions import MoonstreamVerificationError

from . import actions, data
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

    async def __call__(self, request: Request) -> Optional[str]:
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
                return None
        return param


# Login implementation follows:
# https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
oauth2_scheme = OAuth2BearerOrSignature(tokenUrl="token")
oauth2_scheme_manual = OAuth2BearerOrSignature(tokenUrl="token", auto_error=False)


async def get_current_user(
    request: Request,
    token: UUID = Depends(oauth2_scheme),
    db_session=Depends(yield_db_read_only_session),
) -> data.UserResponse:
    """
    Middleware returns user if its token or web3 signature verified.
    """
    authorization: str = request.headers.get("Authorization")
    scheme_raw, _ = get_authorization_scheme_param(authorization)
    scheme = scheme_raw.lower()
    if token is None or token == "":
        raise HTTPException(status_code=404, detail="Access token not found")

    try:
        if scheme == "moonstream":
            payload_json = base64.decodebytes(str(token).encode()).decode("utf-8")
            payload = json.loads(payload_json)
            moonstream_schema: Any = MoonstreamRegistration # mypy hell
            verified = verify(
                authorization_payload=payload, schema=moonstream_schema
            )
            if not verified:
                logger.info("Moonstream verification error")
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

    return data.UserResponse(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        normalized_email=user.normalized_email,
        verified=user.verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
        autogenerated=user.autogenerated,
        application_id=user.application_id,
    )


async def get_current_user_with_groups(
    request: Request,
    token: UUID = Depends(oauth2_scheme),
    db_session=Depends(yield_db_read_only_session),
) -> data.UserWithGroupsResponse:
    """
    Middleware returns user with groups it belongs if its token or web3 signature verified.
    """
    authorization: str = request.headers.get("Authorization")
    scheme_raw, _ = get_authorization_scheme_param(authorization)
    scheme = scheme_raw.lower()
    if token is None or token == "":
        raise HTTPException(status_code=404, detail="Access token not found")

    try:
        if scheme == "moonstream":
            payload_json = base64.decodebytes(str(token).encode()).decode("utf-8")
            payload = json.loads(payload_json)
            moonstream_schema: Any = MoonstreamRegistration # mypy hell
            verified = verify(
                authorization_payload=payload, schema=moonstream_schema
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
    if BOT_INSTALLATION_TOKEN is None or BOT_INSTALLATION_TOKEN == "":
        logger.error("BOT_INSTALLATION_TOKEN environment variable must be set")
        raise HTTPException(status_code=500)

    is_autogenerated_user = False
    installation_token_header: Optional[str] = request.headers.get(
        BOT_INSTALLATION_TOKEN_HEADER, None
    )
    if (
        installation_token_header is not None
        and BOT_INSTALLATION_TOKEN == installation_token_header
    ):
        is_autogenerated_user = True
    elif (
        installation_token_header is not None
        and BOT_INSTALLATION_TOKEN != installation_token_header
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {BOT_INSTALLATION_TOKEN_HEADER} provided",
        )
    return is_autogenerated_user


async def is_token_restricted_or_installation(
    request: Request,
    token: UUID = Depends(oauth2_scheme_manual),
    db_session=Depends(yield_db_read_only_session),
) -> bool:
    """
    Allow access if Bugout installation header provided.

    Because of oauth2_scheme_manual we could accept None
    for follow up Bugout header check.
    """
    authorization: str = request.headers.get("Authorization")
    scheme_raw, _ = get_authorization_scheme_param(authorization)
    scheme = scheme_raw.lower()

    if scheme != "bearer" and scheme is not None and scheme != "":
        raise HTTPException(status_code=400, detail="Unaccepted scheme")

    is_autogenerated_user = autogenerated_user_token_check(request)
    if is_autogenerated_user:
        return False  # Return token.restricted = False
    else:
        token_restricted = await is_token_restricted(request, token, db_session)
        return token_restricted


async def is_token_restricted(
    request: Request,
    token: UUID = Depends(oauth2_scheme),
    db_session=Depends(yield_db_read_only_session),
) -> bool:
    """
    Check if user's token is restricted or not.
    """
    authorization: str = request.headers.get("Authorization")
    scheme_raw, _ = get_authorization_scheme_param(authorization)
    scheme = scheme_raw.lower()

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
