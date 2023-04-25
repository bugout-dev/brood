import base64
import json
import logging
from typing import Optional, Tuple, cast
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.exceptions import HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from web3login.auth import to_checksum_address, verify
from web3login.exceptions import (
    Web3AuthorizationExpired,
    Web3AuthorizationWrongApplication,
    Web3VerificationError,
)
from web3login.middlewares.fastapi import OAuth2BearerOrWeb3

from . import actions, data
from .db import yield_db_read_only_session
from .settings import (
    BOT_INSTALLATION_TOKEN,
    BOT_INSTALLATION_TOKEN_HEADER,
    BUGOUT_APPLICATION_ID_HEADER,
)

logger = logging.getLogger(__name__)

# Login implementation follows:
# https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
oauth2_scheme = OAuth2BearerOrWeb3(tokenUrl="token")
oauth2_scheme_manual = OAuth2BearerOrWeb3(tokenUrl="token", auto_error=False)


async def request_user_authorization(
    request: Request,
    token: UUID = Depends(oauth2_scheme),
    db_session=Depends(yield_db_read_only_session),
) -> Tuple[bool, data.UserResponse]:
    """
    Middleware returns Tuple[is_restricted_token, user] if its token or web3 signature verified.
    """
    authorization: str = request.headers.get("Authorization")  # type: ignore
    scheme_raw, _ = get_authorization_scheme_param(authorization)
    scheme = scheme_raw.lower()
    if token is None or token == "":
        raise HTTPException(status_code=404, detail="Access token not found")

    signature_application: str = request.headers.get(BUGOUT_APPLICATION_ID_HEADER)  # type: ignore
    application_id = None
    if signature_application is not None:
        try:
            application_id = cast(UUID, signature_application)
        except Exception:
            raise HTTPException(
                status_code=403, detail="Wrong Web3 signature application provided"
            )

    try:
        if scheme == "web3":
            payload_json = base64.decodebytes(str(token).encode()).decode("utf-8")
            payload = json.loads(payload_json)
            verified = verify(
                authorization_payload=payload,
                application_to_check=str(application_id)
                if application_id is not None
                else "",
            )
            if not verified:
                logger.info("Web3 verification error")
                raise Web3VerificationError()
            web3_address = payload.get("address")
            if web3_address is None:
                logger.error("Web3 address in payload could not be None")
                raise Exception()
            web3_address = to_checksum_address(web3_address)
            user = actions.get_user(
                session=db_session,
                web3_address=web3_address,
                application_id=application_id,
            )
            is_token_restricted = False

        elif scheme == "bearer":
            (
                is_token_active,
                is_token_restricted,
                user,
            ) = actions.get_current_user_by_token(session=db_session, token=token)
            if not is_token_active:
                raise actions.TokenNotActive("Access token not active")
        else:
            raise HTTPException(
                status_code=401, detail="Unaccepted authorization scheme"
            )

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
    except Web3AuthorizationExpired:
        raise HTTPException(status_code=403, detail="Signature not verified")
    except Web3AuthorizationWrongApplication:
        raise HTTPException(status_code=403, detail="Signature not verified")
    except Web3VerificationError:
        raise HTTPException(status_code=403, detail="Signature not verified")
    except Exception:
        logger.error("Unhandled exception at get_current_user")
        raise HTTPException(status_code=500)

    return is_token_restricted, data.UserResponse(
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


async def request_user_authorization_with_groups(
    request: Request,
    token: UUID = Depends(oauth2_scheme),
    db_session=Depends(yield_db_read_only_session),
) -> Tuple[bool, data.UserWithGroupsResponse]:
    """
    Middleware returns user with groups it belongs if its token or web3 signature verified.
    """
    authorization: str = request.headers.get("Authorization")  # type: ignore
    scheme_raw, _ = get_authorization_scheme_param(authorization)
    scheme = scheme_raw.lower()
    if token is None or token == "":
        raise HTTPException(status_code=404, detail="Access token not found")

    signature_application: str = request.headers.get(BUGOUT_APPLICATION_ID_HEADER)  # type: ignore
    application_id = None
    if signature_application is not None:
        try:
            application_id = cast(UUID, signature_application)
        except Exception:
            raise HTTPException(
                status_code=403, detail="Wrong Web3 signature application provided"
            )

    try:
        if scheme == "web3":
            payload_json = base64.decodebytes(str(token).encode()).decode("utf-8")
            payload = json.loads(payload_json)
            verified = verify(
                authorization_payload=payload,
                application_to_check=str(application_id)
                if application_id is not None
                else "",
            )
            if not verified:
                logger.info("Web3 authorization verification error")
                raise Web3VerificationError()
            web3_address = payload.get("address")
            if web3_address is None:
                logger.error("Web3 address in payload could not be None")
                raise Exception()
            web3_address = to_checksum_address(web3_address)
            user_extended = actions.get_user_with_groups(
                session=db_session,
                web3_address=web3_address,
                application_id=application_id,
            )
            is_token_restricted = False

        elif scheme == "bearer":
            (
                is_token_active,
                is_token_restricted,
                user_extended,
            ) = actions.get_current_user_with_groups_by_token(
                session=db_session, token=token
            )
            if not is_token_active:
                raise actions.TokenNotActive("Access token not active")
        else:
            raise HTTPException(
                status_code=401, detail="Unaccepted authorization scheme"
            )

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
    except Web3AuthorizationExpired:
        raise HTTPException(status_code=403, detail="Signature not verified")
    except Web3AuthorizationWrongApplication:
        raise HTTPException(status_code=403, detail="Signature not verified")
    except Web3VerificationError:
        raise HTTPException(status_code=403, detail="Signature not verified")
    except Exception:
        logger.error("Unhandled exception at get_current_user_with_groups")
        raise HTTPException(status_code=500)

    return is_token_restricted, user_extended


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
    )  # type: ignore
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
