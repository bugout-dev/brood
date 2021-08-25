import os
from typing import Optional

import stripe  # type: ignore

RAW_ORIGIN = os.environ.get("BROOD_CORS_ALLOWED_ORIGINS")
if RAW_ORIGIN is None:
    raise ValueError(
        "BROOD_CORS_ALLOWED_ORIGINS environment variable must be set (comma-separated list of CORS allowed origins"
    )
ORIGINS = RAW_ORIGIN.split(",")

BUGOUT_URL = os.environ.get("BUGOUT_WEB_URL", "https://bugout.dev")

# Emails
BUGOUT_FROM_EMAIL = os.environ.get("BROOD_VERIFICATION_FROM_EMAIL", "info@bugout.dev")
SENDGRID_API_KEY = os.environ.get("BROOD_SENDGRID_API_KEY")

REQUIRE_EMAIL_VERIFICATION: bool = False
SEND_EMAIL_WELCOME: bool = True
TEMPLATE_ID_BUGOUT_WELCOME_EMAIL = os.environ.get(
    "SENDGRID_TEMPLATE_ID_BUGOUT_WELCOME_EMAIL"
)
TEMPLATE_ID_MOONSTREAM_WELCOME_EMAIL = os.environ.get(
    "SENDGRID_TEMPLATE_ID_MOONSTREAM_WELCOME_EMAIL"
)
MOONSTREAM_APPLICATION_ID = os.environ.get("MOONSTREAM_APPLICATION_ID")

DB_URI = os.environ.get("BROOD_DB_URI")

BOT_INSTALLATION_TOKEN = os.environ.get("BUGOUT_BOT_INSTALLATION_TOKEN")
BOT_INSTALLATION_TOKEN_HEADER_RAW = os.environ.get(
    "BUGOUT_BOT_INSTALLATION_TOKEN_HEADER"
)
if BOT_INSTALLATION_TOKEN_HEADER_RAW is not None:
    BOT_INSTALLATION_TOKEN_HEADER = BOT_INSTALLATION_TOKEN_HEADER_RAW
else:
    raise ValueError(
        "BUGOUT_BOT_INSTALLATION_TOKEN_HEADER environment variable must be set"
    )

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY
STRIPE_SIGNING_SECRET = os.environ.get("STRIPE_SIGNING_SECRET")

DEFAULT_USER_GROUP_LIMIT = 15


def group_invite_link_from_env(code: str, email: Optional[str] = None) -> str:
    bugout_url_origin = BUGOUT_URL.rstrip("/")
    group_invite_link = f"{bugout_url_origin}/invites/index.html?code={code}"
    if email is not None:
        group_invite_link = f"{group_invite_link}&email={email}"
    return group_invite_link


# OpenAPI
DOCS_TARGET_PATH = "docs"
BROOD_OPENAPI_LIST = []
BROOD_OPENAPI_LIST_RAW = os.environ.get("BROOD_OPENAPI_LIST")
if BROOD_OPENAPI_LIST_RAW is not None:
    BROOD_OPENAPI_LIST = BROOD_OPENAPI_LIST_RAW.split(",")
