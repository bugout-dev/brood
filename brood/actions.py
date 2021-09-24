"""
User-related Brood operations
"""
from datetime import datetime, timedelta
import logging
from random import randint
import re
from typing import Any, cast, Callable, Dict, List, Optional, Set
import uuid

from passlib.context import CryptContext
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sqlalchemy.orm.base import PASSIVE_OFF
import stripe  # type: ignore
from sqlalchemy import func, or_, and_
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.exc import MultipleResultsFound

from . import data
from . import exceptions
from . import subscriptions
from .models import (
    KVBrood,
    User,
    VerificationEmail,
    Token,
    Group,
    GroupUser,
    GroupInvite,
    UserGroupLimit,
    Role,
    TokenType,
    ResetPassword,
    Subscription,
    SubscriptionPlan,
    Application,
)
from .settings import (
    BUGOUT_URL,
    BUGOUT_FROM_EMAIL,
    SENDGRID_API_KEY,
    DEFAULT_USER_GROUP_LIMIT,
    group_invite_link_from_env,
    TEMPLATE_ID_BUGOUT_WELCOME_EMAIL,
    TEMPLATE_ID_MOONSTREAM_WELCOME_EMAIL,
    MOONSTREAM_APPLICATION_ID,
)

logger = logging.getLogger(__name__)

SPACE_REGEX = re.compile(r"\s")


class PasswordInvalidParameters(ValueError):
    """
    Raised when provided password does not fit strength requirements.
    """

    generic_error_message = "Password is not strong enough:\n- Passwords must be at least 8 characters in length"


class UsernameInvalidParameters(ValueError):
    """
    Raised when provided username does not fit validation requirements.
    """


class UserIncorrectPassword(ValueError):
    """
    Raised when authentication attempt is made with the wrong password.
    """


class UserUnverified(Exception):
    """
    Raised when an unverified user tries to perform an action for which the user should be verified.
    """


class UserInvalidParameters(ValueError):
    """
    Raised when operations are applied to a user but invalid parameters are provided with which to
    specify that user.
    """


class UserNotFound(Exception):
    """
    Raised when user with the given parameters is not found in the database.
    """


class UserAlreadyExists(Exception):
    """
    Raised when given user name already exists in the database.
    """


class VerificationEmailNotFound(Exception):
    """
    Raised when no verification emails are found (for a given user).
    """


class VerificationIncorrectCode(ValueError):
    """
    Raised when verification is attempted with an incorrect code.
    """


class ResetPasswordNotAllowed(Exception):
    """
    Raised when requests for reset password repeats too often.
    """


class TokenNotFound(Exception):
    """
    Raised when token with the given parameters is not found in the database.
    """


class GroupInvalidParameters(ValueError):
    """
    Raised when operations are applied to a group but invalid parameters are provided with which to
    specify that group.
    """


class GroupNotFound(Exception):
    """
    Raised when group with the given parameters is not found in the database.
    """


class GroupAlreadyExists(Exception):
    """
    Raised when given group name already exists in the database.
    """


class InviteNotAllowed(Exception):
    """
    Raised when requests for invite repeats too often.
    """


class InviteNotFound(Exception):
    """
    Raised when invite with the given parameters is not found in the database.
    """


class RoleAlreadyExists(Exception):
    """
    Raised when user already belongs to group.
    """


class RoleNotFound(Exception):
    """
    Raised when user does not belong group.
    """


class NoPermissions(Exception):
    """
    Raised when user does not have permissions to change.
    """


class NoInheritancePermission(Exception):
    """
    Raised when user violates inheritance rules.
    """


class TokenInvalidParameters(ValueError):
    """
    Raised when operations are applied to a token but invalid parameters are provided.
    """


class LackOfUserSpace(Exception):
    """
    Raised when group doesn't have free space.
    """


class KVBroodInvalidParameters(ValueError):
    """
    Raised when provided kv variable does not found in the database.
    """


class KVBroodNotFound(Exception):
    """
    Raised when required kv_brood key not found in the database.
    """


def user_as_json_dict(user: User) -> Dict[str, Any]:
    """
    Returns a representation of the given user as a JSON-serializable dictionary.
    """
    user_json = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "normalized_email": user.normalized_email,
        "verified": user.verified,
        "created_at": str(user.created_at),
        "updated_at": str(user.updated_at),
        "tokens": [token_as_json_dict(token) for token in user.tokens],
    }
    return user_json


def verification_email_as_json_dict(
    verification_email: VerificationEmail,
) -> Dict[str, Any]:
    """
    Returns a representation of the given verification email as a JSON-serializable dictionary.
    """
    verification_email_json = {
        "id": str(verification_email.id),
        "user_id": str(verification_email.user_id),
        "active": verification_email.active,
        "verification_code": verification_email.verification_code,
        "created_at": str(verification_email.created_at),
        "updated_at": str(verification_email.updated_at),
    }
    return verification_email_json


def token_as_json_dict(token: Token) -> Dict[str, Any]:
    """
    Returns a representation of the given token as a JSON-serializable dictionary.
    """
    token_json = {
        "id": str(token.id),
        "user_id": str(token.user_id),
        "active": token.active,
        "token_type": token.token_type.value,
        "note": token.note,
        "created_at": str(token.created_at),
        "updated_at": str(token.updated_at),
        "restricted": token.restricted,
    }
    return token_json


def group_as_json_dict(group: Group) -> Dict[str, Any]:
    """
    Returns a representation of the given group as a JSON-serializable dictionary.
    """
    group_json = {"id": str(group.id), "name": group.name}
    return group_json


def group_users_as_json_dict(group_users: data.GroupUserResponse) -> Dict[str, Any]:
    """
    Returns a representation of the given group_users as a JSON-serializable dictionary.
    """
    group_users_json = {
        "group_id": str(group_users.group_id),
        "user_id": str(group_users.user_id),
        "user_type": str(group_users.user_type),
    }
    return group_users_json


def plan_as_json_dict(plan: SubscriptionPlan) -> Dict[str, Any]:
    """
    Returns a representation of the given subscription plan as a JSON-serializable dictionary.
    """
    plan_json = {
        "id": str(plan.id),
        "name": plan.name,
        "description": plan.description,
        "stripe_product_id": plan.stripe_product_id,
        "stripe_price_id": plan.stripe_price_id,
        "default_units": plan.default_units,
        "plan_type": plan.plan_type,
        "public": plan.public,
    }
    return plan_json


def subscription_as_json_dict(subscription: Subscription) -> Dict[str, Any]:
    """
    Returns a representation of the given group subscription as a JSON-serializable dictionary.
    """
    subscription_json = {
        "group_id": str(subscription.group_id),
        "subscription_plan_id": str(subscription.subscription_plan_id),
        "stripe_customer_id": subscription.stripe_customer_id,
        "stripe_subscription_id": subscription.stripe_subscription_id,
        "units": subscription.units,
        "active": subscription.active,
    }
    return subscription_json


def kv_brood_as_json_dict(kv_brood: KVBrood) -> Dict[str, Any]:
    """
    Returns a representation of the given kv variables as a JSON-serializable dictionary.
    """
    kv_brood_json = {
        "kv_key": kv_brood.kv_key,
        "kv_value": kv_brood.kv_value,
    }
    return kv_brood_json


def application_as_json_dict(application: Application) -> Dict[str, Any]:
    application_json = {
        "id": str(application.id),
        "group_id": str(application.group_id),
        "name": application.name,
        "description": application.description,
    }
    return application_json


def get_password_context() -> CryptContext:
    """
    Generate a passlib context for Brood passwords.
    """
    password_context = CryptContext(schemes=["argon2"])
    return password_context


def generate_verification_code(
    randint_generator: Optional[Callable[[int, int], int]] = None,
) -> str:
    """
    Uses the given random integer generator to generate a string with six digits.
    This string can be used as a verification code for Brood user registration.
    """
    if randint_generator is None:
        randint_generator = randint

    verification_code_int = randint_generator(0, 10 ** 6 - 1)
    verification_code_raw = str(verification_code_int)
    verification_code = f"{'0'*(6 - len(verification_code_raw))}{verification_code_raw}"
    return verification_code


def normalize_email(email: str) -> str:
    """
    Normalize an email to store it in the database.
    """
    segments = email.split("@")
    assert len(segments) > 1
    hostname = segments[-1]
    username_raw = "@".join(segments[:-1])
    username_no_dots = "".join(username_raw.split("."))
    assert username_no_dots != ""
    plus_segments = username_no_dots.split("+")
    assert len(plus_segments) > 0
    assert plus_segments[0] != ""
    normalized_username = plus_segments[0].lower()
    return f"{normalized_username}@{hostname}"


def verify_password_strength(password: str) -> None:
    required_len = 8
    if len(password) < required_len:
        raise PasswordInvalidParameters(
            f"Password must contain at least {required_len} characters"
        )


def verify_username(username: str) -> None:
    white_space_matches = SPACE_REGEX.search(username)
    if white_space_matches is not None:
        raise UsernameInvalidParameters(f"Username must not contain spaces")


def password_confirm(
    user: User,
    password: Optional[str] = None,
    password_hash: Optional[str] = None,
) -> bool:
    """
    Confirm password provided by user.
    """
    if password is None and password_hash is None:
        raise UserInvalidParameters(
            "In order to check user password, at least one of password, "
            "or password_hash must be specified"
        )
    password_context = get_password_context()
    if password is not None:
        if password_context.verify(password, user.password_hash):
            return True
    if password_hash is not None:
        if user.password_hash == password_hash:
            return True

    return False


def create_user(
    session: Session,
    username: str,
    email: str,
    password: str,
    autogenerated_user: bool = False,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    application_id: Optional[uuid.UUID] = None,
) -> User:
    """
    Creates a new user in the given database session and
    returns the created user object.

    According with autogenerated_user var it create bugout user for Slack/Github installation or
    normal user.

    Sessions are expected to be sqlalchemy Session objects:
    https://docs.sqlalchemy.org/en/13/orm/session_api.html#sqlalchemy.orm.session.Session
    """
    assert username != ""
    assert email != ""
    assert password != ""

    # Username and email should be stored as lowercase strings in the database.
    username = username.lower()
    normalized_email = normalize_email(email)

    verify_username(username)
    verify_password_strength(password)

    password_context = get_password_context()
    password_hash = password_context.hash(password)
    auth_type = "brood"

    user_object = User(
        username=username,
        email=email,
        normalized_email=normalized_email,
        password_hash=password_hash,
        auth_type=auth_type,
        verified=True if autogenerated_user else False,
        autogenerated=True if autogenerated_user else False,
        first_name=first_name,
        last_name=last_name,
        application_id=application_id,
    )
    user_group_limit = UserGroupLimit(group_limit=DEFAULT_USER_GROUP_LIMIT)
    user_group_limit.user = user_object

    try:
        session.add(user_object)
        session.add(user_group_limit)
        session.commit()
    except Exception as e:
        logger.error(e)
        raise UserAlreadyExists("This user already exists")

    return user_object


def get_user(
    session: Session,
    username: Optional[str] = None,
    email: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    application_id: Optional[uuid.UUID] = None,
) -> User:
    """
    Get a user by username, email, or user_id. If more than one of those fields is provided, will
    look for a user having ALL the given parameters.

    Emails are first normalized and then the lookup is performed against the normalized_email column
    of the users table.
    """
    if username is None and email is None and user_id is None:
        raise UserInvalidParameters(
            "In order to get user, at least one of username, email, or user_id must be specified"
        )

    query = session.query(User)

    if username is not None:
        username = cast(str, username)
        username = username.lower()
        query = query.filter(User.username == username)

    normalized_email = None
    if email is not None:
        normalized_email = normalize_email(email)
        query = query.filter(User.normalized_email == normalized_email)

    if user_id is not None:
        query = query.filter(User.id == user_id)

    if application_id is not None:
        query = query.filter(User.application_id == application_id)

    user = query.first()
    if user is None:
        raise UserNotFound(
            f"Did not find user with filters username={username}, normalized_email={normalized_email}"
        )

    return user


def update_user(
    session: Session,
    user_id: uuid.UUID,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> User:
    """
    Update user's first_name and last_name with the given ID.
    """
    if first_name is None and last_name is None:
        raise UserInvalidParameters(
            "In order to update user, at least one of first_name, or last_name must be specified"
        )

    query = session.query(User).filter(User.id == user_id)
    user_object = query.first()

    if first_name is not None:
        query.update({User.first_name: first_name})
    if last_name is not None:
        query.update({User.last_name: last_name})

    session.commit()
    return user_object


def delete_user(
    session: Session,
    username: Optional[str] = None,
    email: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    current_password: Optional[str] = None,
) -> User:
    """
    Delete a user by username, email, or user_id. Uses get_user to locate the specified user.
    """
    if username is None and email is None and user_id is None:
        raise UserInvalidParameters(
            "In order to delete user, at least one of username, email, or user_id must be specified"
        )
    user = get_user(session, username, email, user_id)

    if user.autogenerated is False:
        if current_password is None:
            raise UserIncorrectPassword(
                "Attempted to delete user please provide password"
            )
        else:
            password_abide = password_confirm(user, password=current_password)
            if password_abide is False:
                raise UserIncorrectPassword(
                    "Attempted to delete user with incorrect password"
                )

    session.delete(user)
    session.commit()
    return user


def change_password(
    session: Session,
    new_password: str,
    current_password: Optional[str] = None,
    current_password_hash: Optional[str] = None,
    username: Optional[str] = None,
    email: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
) -> User:
    """
    Change a user's password.
    """
    user = get_user(session, username, email, user_id)

    password_abide = password_confirm(
        user,
        password=current_password,
        password_hash=current_password_hash,
    )
    if password_abide is False:
        raise UserIncorrectPassword(
            "Attempted to change password with incorrect password"
        )

    verify_password_strength(new_password)

    password_context = get_password_context()
    new_password_hash = password_context.hash(new_password)
    user.password_hash = new_password_hash
    session.add(user)
    session.commit()
    return user


def send_welcome_email(user: User, application_id: Optional[uuid.UUID] = None) -> None:
    """
    Send welcome email to each new user.
    """
    user_id = str(user.id)
    if SENDGRID_API_KEY is None:
        logger.error(
            f"Missed SENDGRID_API_KEY, message was not sent to user with id: {user_id}"
        )
        return

    message = Mail(
        from_email=f"Sophia from Bugout <{BUGOUT_FROM_EMAIL}>", to_emails=user.email
    )
    message.dynamic_template_data = {"username": user.username}

    if application_id is not None:
        if str(application_id) != MOONSTREAM_APPLICATION_ID:
            logger.error(
                f"Unhandled welcome email for application with id: {str(application_id)}"
            )
            return
        else:
            message.template_id = TEMPLATE_ID_MOONSTREAM_WELCOME_EMAIL
    else:
        message.template_id = TEMPLATE_ID_BUGOUT_WELCOME_EMAIL

    logger.info(f"Sending welcome email for user with id={user_id}...")

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        logger.info(
            f"Welcome email successfully submitted to Sendgrid for user with id={user_id}"
        )
    except Exception as e:
        logger.error(f"Error sending welcome email {e}")
        pass


def send_verification_email(
    session: Session,
    username: Optional[str] = None,
    email: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
) -> VerificationEmail:
    """
    Send verification email for the given (user identified using get_user).

    Pulls configuration from the following two environment variables:
    - BROOD_VERIFICATION_FROM_EMAIL - Email address from which verification emails are sent.
    - BROOD_SENDGRID_API_KEY - SendGrid API key
    """
    user = get_user(session, username, email, user_id)
    query = (
        session.query(VerificationEmail)
        .filter(VerificationEmail.active == True)
        .filter(VerificationEmail.user_id == user.id)
    )
    for old_email in query:
        old_email.active = False
        session.add(old_email)

    verification_code = generate_verification_code()
    verification_email = VerificationEmail(
        verification_code=verification_code,
        active=True,
        user_id=user.id,
    )
    session.add(verification_email)
    session.commit()

    if SENDGRID_API_KEY:
        message = Mail(
            from_email=BUGOUT_FROM_EMAIL,
            to_emails=user.email,
            subject="Bugout.dev account verification",
            html_content=f"Verification code: <strong>{verification_email.verification_code}</strong>",
        )

        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
        except Exception as e:
            logger.exception(e)
            raise

    return verification_email


def complete_verification(
    session: Session,
    code: str,
    username: Optional[str] = None,
    email: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
) -> User:
    """
    Complete verification flow for the given user.
    """
    user = get_user(session, username, email, user_id)
    query = (
        session.query(VerificationEmail)
        .filter(VerificationEmail.active == True)
        .filter(VerificationEmail.user_id == user.id)
    )
    verification_email = query.first()
    if verification_email is None:
        raise VerificationEmailNotFound(
            f"No verification emails found for user with ID: {user.id}"
        )

    if code != verification_email.verification_code:
        raise VerificationIncorrectCode(
            f"Code ({code}) does not match code of any active verification for user with ID {user.id}"
        )

    verification_email.active = False
    session.add(verification_email)
    user.verified = True
    session.add(user)
    session.commit()
    return user


def generate_reset_password(session: Session, email: str) -> ResetPassword:
    """
    Checks if user exists and password reset requests happens not too often.

    We use delay 1 minute to prevent spam.

    TODO(kompotkot): This function looks monstrous because of problem with UTC timezone.
    Datetime from PC: 020-10-14 17:39:08.798535+00:00
    Datetime from DB: 2020-10-14 17:49:05.567316-07:00
    It requires changes and DB migration to has possibility compare datetime outside of Postgres.
    """
    if email is None:
        raise UserInvalidParameters("In order to get user, email must be specified")

    user = get_user(session, email=email)

    query = session.query(ResetPassword).filter(ResetPassword.user_id == user.id)
    reset_object = query.one_or_none()

    if reset_object is None:
        reset_object = ResetPassword(user_id=user.id)
        session.add(reset_object)
        session.commit()

        return reset_object

    current_time = datetime.utcnow()
    ts_delay = current_time - timedelta(minutes=1)

    reset_object_fresh = query.filter(ResetPassword.created_at > ts_delay).one_or_none()

    if reset_object_fresh is not None:
        raise ResetPasswordNotAllowed(
            f"Please wait {ts_delay} until next password reset"
        )

    session.delete(reset_object)
    session.commit()

    reset_object = ResetPassword(user_id=user.id)
    session.add(reset_object)
    session.commit()

    return reset_object


def send_reset_password_email(reset_object: ResetPassword, email: str) -> None:
    """
    Send reset password for given email.
    """
    message = Mail(
        from_email=BUGOUT_FROM_EMAIL,
        to_emails=email,
        subject="Bugout.dev password reset",
        html_content=f"Reset password url: {BUGOUT_URL}/password/reset/index.html?reset_id={str(reset_object.id)}",
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
    except Exception as e:
        logger.exception(e)
        raise


def reset_password_confirmation(
    session: Session, reset_id: uuid.UUID, new_password: str
) -> User:
    """
    Process password change for user. Last step in password reset workflow.
    Mark as completed password reset in DB.
    """
    query = (
        session.query(ResetPassword)
        .filter(ResetPassword.id == reset_id)
        .filter(ResetPassword.completed == False)
    )
    reset_object = query.one_or_none()

    if reset_object is None:
        raise UserNotFound(f"Did not find user to reset password")

    verify_password_strength(new_password)

    user = get_user(session, user_id=reset_object.user_id)
    try:
        change_password(
            session,
            new_password=new_password,
            current_password_hash=user.password_hash,
            user_id=reset_object.user_id,
        )

        query.update({ResetPassword.completed: True})
        session.commit()
    except Exception as e:
        logger.error(f"Unable to change password, error: {e}")
        raise

    return user


def create_token(
    session: Session,
    user_id: uuid.UUID,
    token_type: Optional[TokenType] = TokenType.bugout,
    token_note: Optional[str] = None,
    restricted: bool = False,
) -> Token:
    """
    Generate an access token for the given user (user retrieved using get_user).
    """
    token = Token(
        user_id=user_id,
        active=True,
        token_type=token_type,
        note=token_note,
        restricted=restricted,
    )
    session.add(token)
    session.commit()
    return token


def get_token(session: Session, token: uuid.UUID) -> Token:
    """
    Retrieve the token with the given ID from the database (if it exists).
    """
    token_object = session.query(Token).filter(Token.id == token).first()
    if token_object is None:
        raise TokenNotFound(f"Token not found with ID: {token}")
    token_object = cast(Token, token_object)
    return token_object


def update_token(
    session: Session,
    token: uuid.UUID,
    token_type: Optional[TokenType] = None,
    token_note: Optional[str] = None,
    target_token: Optional[uuid.UUID] = None,
) -> Token:
    """
    Update the token's type and note with the given ID.
    """
    if token_type is None and token_note is None:
        raise TokenInvalidParameters(
            "In order to update token, at least one of token_type, or token_note must be specified"
        )
    if token_type is not None and token_type not in TokenType:
        raise TokenInvalidParameters("Incorrect token type provided.")

    token_object = get_token(session, token)
    if token_object.restricted:
        raise exceptions.RestrictedTokenUnauthorized(
            "Restricted tokens cannot update tokens"
        )

    target_object = token_object
    if target_token is not None:
        target_object = get_token(session, target_token)
    if token_object.user_id != target_object.user_id:
        raise exceptions.AccessTokenUnauthorized(
            "Could not perform the desired operation."
        )

    if token_type is not None:
        token_object.token_type = token_type
    if token_note is not None:
        token_object.note = token_note

    session.add(token_object)
    session.commit()
    return token_object


def revoke_token(
    session: Session, token: uuid.UUID, target: Optional[uuid.UUID] = None
) -> Token:
    """
    Revoke the token with the given ID (if it exists).
    """
    token_object = get_token(session, token)
    if token_object.restricted:
        raise exceptions.RestrictedTokenUnauthorized(
            "Restricted tokens are not authorized to revoke tokens"
        )
    target_object = token_object
    if target is not None:
        target_object = get_token(session, target)
    if token_object.user_id != target_object.user_id:
        raise exceptions.AccessTokenUnauthorized(
            "Could not perform the desired operation."
        )
    target_object.active = False
    session.add(target_object)
    session.commit()
    return target_object


def login(
    session: Session,
    username: str,
    password: str,
    token_type: Optional[TokenType] = TokenType.bugout,
    token_note: Optional[str] = None,
    restricted: bool = False,
    application_id: Optional[uuid.UUID] = None,
) -> Token:
    """
    Login with the given username and password to get a new token for the user with that username.
    If token_type and token_note provieded it works as token generation handler. By default it
    creates "bugout" token with None in note.
    """
    user = get_user(session, username=username, application_id=application_id)

    password_abide = password_confirm(user, password=password)
    if password_abide is False:
        raise UserIncorrectPassword("Attempted to login with incorrect password")

    token = create_token(
        session,
        user_id=user.id,
        token_type=token_type,
        token_note=token_note,
        restricted=restricted,
    )
    return token


def get_user_limit(session: Session, group: Group, modifier: int) -> bool:
    """
    Comparing number of free seats and number of users in group and
    subgroups with parent groups.

    :return: False if space is exhausted.
    """
    max_seats = get_num_seats(session, group)
    num_users = get_num_users(session, group)

    free_space = max_seats - num_users + 1
    if modifier > 0 and free_space - modifier <= 0:
        return False

    return True


def get_group_children(
    session: Session,
    group_id: uuid.UUID,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Group]:
    """
    Return list of children who have provided group id in parent field.
    """
    query = session.query(Group).filter(Group.parent == group_id)
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    children = query.all()
    return children


def get_num_users(session: Session, group: Group) -> int:
    """
    Calculates number of unique users in group, group's children and
    parent if it is exists.
    """
    top_group_id = group.id
    if group.parent is not None:
        top_group_id = group.parent

    num_users = (
        session.query(func.count(func.distinct(User.id)))
        .join(GroupUser, GroupUser.user_id == User.id)
        .filter(User.autogenerated == False, GroupUser.group_id == top_group_id)
    ).one()[0]

    return num_users


def get_num_seats(session: Session, group: Group) -> int:
    """
    Calculate number of maximum seats for provided group.
    It includes all active subscriptions.
    """
    seats_plans = (
        session.query(SubscriptionPlan)
        .filter(SubscriptionPlan.plan_type == data.SubscriptionPlanType.seats.value)
        .all()
    )
    seats_plans_ids = [plan.id for plan in seats_plans]
    subscriptions = (
        session.query(Subscription)
        .filter(Subscription.active == True)
        .filter(
            or_(
                Subscription.group_id == group.parent, Subscription.group_id == group.id
            )
        )
        .all()
    )
    num_seats = sum(
        [
            subscription.units
            for subscription in subscriptions
            if subscription.subscription_plan_id in seats_plans_ids
        ]
    )
    return num_seats


def find_group(session: Session, group_id: uuid.UUID) -> Group:
    group = session.query(Group).filter(Group.id == group_id).one_or_none()
    if group is None:
        raise GroupNotFound("Did not find group")

    return group


def get_group(
    session: Session,
    group_id: Optional[uuid.UUID] = None,
    group_name: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
) -> Group:
    """
    Get a group by group_name, or group_id. If more than one of those fields is provided, will
    look for a group having ALL the given parameters.

    TODO: This should return a list of groups because the group_name is no longer unique. For now,
    if a user tries to find a group by group_name and there are multiple groups with that name,

    """

    if group_id is None and group_name is None:
        raise GroupInvalidParameters(
            "In order to get group, at least one of group_id, or group_name must be specified"
        )
    query = session.query(Group)
    if group_id is not None:
        query = query.filter(Group.id == group_id)
    if group_name is not None:
        query = query.filter(Group.name == group_name)

    if user_id is not None:
        query = query.join(GroupUser, Group.id == GroupUser.group_id).filter(
            GroupUser.user_id == user_id
        )

    try:
        group = query.one_or_none()
    except MultipleResultsFound:
        raise GroupAlreadyExists(f"Multiple groups exist with name: {group_name}")

    if group is None:
        raise GroupNotFound(f"Did not find group with filters group_id={group_id}")

    return group


def create_group(
    session: Session, group_name: str, user: User, parent_id: Optional[uuid.UUID] = None
) -> Group:
    """
    Creates a new group in the given database session and
    returns the created group object.
    """
    num_user_groups = count_user_groups(session, user.id)
    user_group_limit = get_user_group_limit(session, user.id)
    if num_user_groups >= user_group_limit:
        raise exceptions.UserGroupLimitExceeded(
            f"You have exceeded your quota for group membership ({user_group_limit}). You are in {num_user_groups} groups."
        )

    free_plan_id = get_kv_variable(
        session, "BUGOUT_GROUP_FREE_SUBSCRIPTION_PLAN"
    ).kv_value
    free_plan = subscriptions.get_subscription_plan(session, free_plan_id)

    assert group_name != ""

    # Group name should be stored as lowercase string in the database
    group_name = cast(str, group_name)

    is_child = False
    if parent_id is not None:
        parent_group = session.query(Group).filter(Group.id == parent_id).one_or_none()
        if parent_group is None:
            raise GroupNotFound("There is no provided group with parent id")
        if parent_group.parent is not None:
            raise GroupInvalidParameters(
                "Wrong group parent provided, it is forbidden to have more then one level of inheritance"
            )
        is_child = True

    group = Group(
        name=group_name,
        autogenerated=True if user.autogenerated is True else False,
        parent=parent_id,
    )

    try:
        session.add(group)
        session.commit()
        if not is_child:
            subscriptions.add_group_subscription(
                session,
                group_id=group.id,
                plan_id=free_plan.id,
                units=free_plan.default_units,
                active=True,
            )

        set_user_in_group(
            session=session,
            group_id=group.id,
            current_user_type=Role.owner,
            current_user_autogenerated=True if user.autogenerated is True else False,
            user_type=Role.owner.value,
            username=user.username,
        )
    except Exception as e:
        logger.error(e)
        raise GroupAlreadyExists("Error due adding subscription or set user in group")

    return group


def get_groups_for_user(
    session: Session, user_id: uuid.UUID
) -> List[data.GroupUserResponse]:
    """
    Get list of groups current user belongs to.
    """
    groups = (
        session.query(
            Group.id,
            Group.name,
            GroupUser.user_type,
            GroupUser.user_id,
            Group.autogenerated,
            Group.parent,
        )
        .join(Group)
        .filter(user_id == GroupUser.user_id)
        .all()
    )

    groups_response = [
        data.GroupUserResponse(
            group_id=group.id,
            user_id=group.user_id,
            user_type=group.user_type,
            autogenerated=group.autogenerated,
            group_name=group.name,
            parent=group.parent,
            num_users=get_num_users(session, group),
            num_seats=get_num_seats(session, group),
        )
        for group in groups
    ]

    return groups_response


def count_user_groups(session: Session, user_id: uuid.UUID) -> int:
    """
    Returns the number of groups the given user belongs to.
    """
    query = session.query(func.count(GroupUser.group_id)).filter(
        GroupUser.user_id == user_id
    )
    num_groups = query.one()[0]
    return num_groups


def get_user_group_limit(session: Session, user_id: uuid.UUID) -> int:
    """
    Returns the user's quota for how many groups they can belong to.
    """
    query = session.query(UserGroupLimit).filter(UserGroupLimit.user_id == user_id)
    row = query.one_or_none()
    if row is None:
        return DEFAULT_USER_GROUP_LIMIT
    return row.group_limit


def set_user_group_limit(session: Session, user_id: uuid.UUID, limit: int) -> None:
    """
    Sets the users group limit to the given value.
    """
    query = session.query(UserGroupLimit).filter(UserGroupLimit.user_id == user_id)
    user_group_limit = query.one_or_none()
    if user_group_limit is None:
        user_group_limit = UserGroupLimit(user_id=user_id, group_limit=limit)
        session.add(user_group_limit)
    else:
        user_group_limit.group_limit = limit
    session.commit()


def set_user_in_group(
    session: Session,
    group_id: uuid.UUID,
    current_user_type: Role,
    current_user_autogenerated: bool,
    user_type: str,
    username: Optional[str] = None,
    email: Optional[str] = None,
) -> data.GroupUserResponse:
    """
    Associate user with group or change user type in group if you have permissions.

    This function contains additional arguments to give possibility create groups
    when user doesn't have any roles because group doesn't exist.
    """
    if username is None and email is None:
        raise GroupInvalidParameters(
            "In order to manage user in group, user_type and at least one of username, or email must be specified"
        )

    # Convert to stored format
    if username is not None:
        username = cast(str, username)
        username = username.lower()
        user = get_user(session, username=username)
    else:
        user = get_user(session, email=email)

    group = get_group(session, group_id=group_id)

    # Check what role proposed user already has
    user_role = (
        session.query(GroupUser)
        .filter(GroupUser.group_id == group.id, GroupUser.user_id == user.id)
        .one_or_none()
    )
    if current_user_autogenerated == False and user.autogenerated == True:
        logger.error("Only autogenerated users allowed to modify autogenerated users")
        raise NoPermissions("You nave no permission to change roles in group")

    # Check group has paren and add user to parent if he doesn't belong to it
    if group.parent is not None:
        parent_user_role = (
            session.query(GroupUser)
            .filter(GroupUser.group_id == group.parent, GroupUser.user_id == user.id)
            .one_or_none()
        )
        if parent_user_role is None:
            raise NoInheritancePermission(
                "User should belong to parent group before he will be added to child group"
            )

    # Check user permissions
    if current_user_type not in Role:
        raise NoPermissions("You nave no permission to change roles in group")

    if current_user_type == Role.member:
        user_type = Role.member.value
    elif current_user_type == Role.admin and user_type == Role.owner.value:
        user_type = Role.admin.value

    role_object = GroupUser(group_id=group.id, user_id=user.id, user_type=user_type)

    # Create new one or update existed
    if user_role is None:
        user_space = get_user_limit(session, group, 1)
        if user_space is False:
            raise LackOfUserSpace("There are no space in group to add new user")

        session.add(role_object)
        session.commit()
    else:
        session.query(GroupUser).filter(
            GroupUser.group_id == group.id, GroupUser.user_id == user.id
        ).update({GroupUser.user_type: user_type})
        session.commit()

    return data.GroupUserResponse(
        group_id=role_object.group_id,
        user_id=role_object.user_id,
        user_type=role_object.user_type,
        group_name=group.name,
        autogenerated=group.autogenerated,
    )


def change_group_name(
    session: Session,
    group_id: uuid.UUID,
    group_name: str,
) -> data.GroupResponse:
    """
    Change group name by group id.
    """
    query = session.query(Group).filter(Group.id == group_id)
    group = query.one_or_none()
    if group is None:
        raise GroupNotFound(f"Did not find any group with group_id={group_id}")

    query.update({Group.name: group_name})
    session.commit()

    return data.GroupResponse(
        id=group.id,
        name=group_name,
        group_name=group_name,
        autogenerated=group.autogenerated,
        subscriptions=[
            subscription_plan.subscription_plan_id
            for subscription_plan in group.subscriptions
        ],
        parent=group.parent,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


def delete_user_from_group(
    session: Session,
    group_id: uuid.UUID,
    current_user_autogenerated: bool,
    username: Optional[str] = None,
    email: Optional[str] = None,
) -> data.GroupUserResponse:
    """
    Delete user from group.
    """
    if username is None and email is None:
        raise GroupInvalidParameters(
            "In order to add user to group, at least one of username, or email must be specified"
        )

    # Convert to stored format
    if username is not None:
        username = cast(str, username)
        username = username.lower()
        user = get_user(session, username=username)
    else:
        user = get_user(session, email=email)

    group = get_group(session, group_id=group_id)

    # Get role
    role_object = (
        session.query(GroupUser)
        .filter(GroupUser.group_id == group.id, GroupUser.user_id == user.id)
        .one_or_none()
    )
    if role_object is None:
        raise RoleNotFound("Raised when user does not belong group")

    if current_user_autogenerated == False and user.autogenerated == True:
        logger.error("Only autogenerated users allowed to modify autogenerated users")
        raise NoPermissions("You nave no permission to change roles in group")

    session.delete(role_object)
    session.commit()

    # Check group has children and delete user from children groups if he is in list
    children = get_group_children(session, group.id)
    for child_group in children:
        child_role_object = (
            session.query(GroupUser)
            .filter(GroupUser.group_id == child_group.id, GroupUser.user_id == user.id)
            .one_or_none()
        )
        if child_role_object is not None:
            session.delete(child_role_object)
            session.commit()

    return data.GroupUserResponse(
        group_id=role_object.group_id,
        user_id=role_object.user_id,
        user_type=role_object.user_type,
        group_name=group.name,
        autogenerated=group.autogenerated,
    )


def delete_group(session: Session, group_id: uuid.UUID, current_user: User) -> Group:
    """
    Delete a group by group_name. Use get_group to locate the specified group.
    """
    group = get_group(session, group_id=group_id)
    if current_user.autogenerated == False and group.autogenerated == True:
        logger.error("Only autogenerated users allowed to delete autogenerated groups")
        raise NoPermissions("You nave no permission to delete group")
    session.delete(group)
    session.commit()
    return group


def check_user_type_in_group(
    session: Session,
    user_id: uuid.UUID,
    group_id: uuid.UUID,
) -> data.GroupUserResponse:
    """
    Checks if user is an owner or member of requested group.
    """
    group_user = (
        session.query(
            Group.id,
            GroupUser.user_id,
            GroupUser.user_type,
            Group.autogenerated,
            Group.name,
        )
        .join(Group)
        .filter(user_id == GroupUser.user_id)
        .filter(group_id == GroupUser.group_id)
        .one_or_none()
    )

    if group_user is None:
        raise GroupNotFound(f"Did not find available group for user with id={user_id}")

    return data.GroupUserResponse(
        group_id=group_user.id,
        user_id=group_user.user_id,
        user_type=group_user.user_type,
        autogenerated=group_user.autogenerated,
        group_name=group_user.name,
    )


def get_group_users(
    session: Session, group_id: uuid.UUID, group_name: Optional[str]
) -> data.UsersListResponse:
    """
    Extract member list of group.

    # TODO(kompotkot): Optimize and reduce unnecessary SQL queries.
    """
    group = get_group(session, group_id=group_id)

    num_users = get_num_users(session, group)
    max_seats = get_num_seats(session, group)

    group_users_response = data.UsersListResponse(
        id=group_id, name=group_name, users=[], num_users=num_users, num_seats=max_seats
    )

    # Extract users information for requested group
    group_users = (
        session.query(
            GroupUser.group_id,
            Group.name,
            GroupUser.user_id,
            User.username,
            User.email,
            GroupUser.user_type,
        )
        .join(Group, GroupUser.group_id == Group.id)
        .join(User, GroupUser.user_id == User.id)
        .filter(GroupUser.group_id == group_id)
        .all()
    )
    if len(group_users) > 0:
        group_users_response.users = [
            data.UserInListResponse(
                id=user.user_id,
                username=user.username,
                email=user.email,
                user_type=user.user_type,
            )
            for user in group_users
        ]

    return group_users_response


def create_invite(
    db_session: Session,
    group_id: uuid.UUID,
    initiator_user_id: uuid.UUID,
    invited_email: Optional[str] = None,
    user_type: Role = Role.member,
) -> GroupInvite:
    """
    Create invite to group.
    """
    current_time = datetime.utcnow()
    ts_delay = current_time - timedelta(seconds=5)

    invite_object_fresh = (
        db_session.query(GroupInvite)
        .filter(GroupInvite.group_id == group_id, GroupInvite.created_at > ts_delay)
        .one_or_none()
    )
    if invite_object_fresh is not None:
        raise InviteNotAllowed(f"Please wait {ts_delay} until send another invite")

    invite = GroupInvite(
        group_id=group_id,
        initiator_user_id=initiator_user_id,
        invited_email=invited_email,
        user_type=user_type.value,
    )
    db_session.add(invite)
    db_session.commit()

    return invite


def send_group_invite(invite_id: uuid.UUID, email: str, initiator_email: str) -> None:
    """
    Send invite to group for given email.
    """
    group_invite_link = group_invite_link_from_env(str(invite_id), email)
    message = Mail(
        from_email=BUGOUT_FROM_EMAIL,
        to_emails=email,
        subject="Bugout.dev invite to group",
        html_content=(
            f"You have been invited to group by {initiator_email}!\n"
            f"Invite url: {group_invite_link}"
        ),
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
    except Exception as e:
        logger.exception(e)
        raise


def list_invites(
    db_session: Session, group_id: uuid.UUID, active: Optional[bool] = None
) -> List[GroupInvite]:
    """
    Return a list of group invites.
    """
    query = db_session.query(GroupInvite).filter(GroupInvite.group_id == group_id)
    if active is not None:
        query = query.filter(GroupInvite.active == active)
    invites = query.all()

    return invites


def get_invite(db_session: Session, invite_id: uuid.UUID) -> GroupInvite:
    """
    Get group invite by id.
    """
    invite = (
        db_session.query(GroupInvite).filter(GroupInvite.id == invite_id).one_or_none()
    )
    if invite is None:
        raise InviteNotFound(f"Invite with id {invite_id} is not presented in database")
    return invite


def update_invite(db_session: Session, invite_id: uuid.UUID, active: bool) -> None:
    """
    Update accepted status of group invite.
    """
    query = db_session.query(GroupInvite).filter(GroupInvite.id == invite_id)
    invite = query.one_or_none()
    if invite is None:
        raise InviteNotFound(f"Invite with id {invite_id} is not presented in database")

    query.update({GroupInvite.active: active})
    db_session.commit()


def get_kv_variable(
    db_session: Session, kv_key: Optional[str] = None, kv_value: Optional[str] = None
) -> KVBrood:
    """
    Extract kv record with key and value from database.
    """
    if kv_key is None and kv_value is None:
        raise KVBroodInvalidParameters(
            "In oder to get kv variables specify at least kv_key or kv_value"
        )

    query = db_session.query(KVBrood)
    if kv_key is not None:
        query = query.filter(KVBrood.kv_key == kv_key)
    if kv_value is not None:
        query = query.filter(KVBrood.kv_value == kv_value)

    kv_variable = query.one_or_none()
    # if kv_variable is None:
    #     raise KVBroodNotFound("Variable not found in KVBrood table")

    return kv_variable


def create_application(
    db_session: Session,
    group_id: uuid.UUID,
    name: str,
    description: Optional[str] = None,
) -> Application:
    """
    Create new record in Application table.
    """
    application = Application(group_id=group_id, name=name, description=description)
    db_session.add(application)
    db_session.commit()

    return application


def get_applications(
    db_session: Session,
    application_id: Optional[uuid.UUID] = None,
    groups_ids: Optional[List[uuid.UUID]] = None,
) -> List[Application]:
    query = db_session.query(Application)

    if application_id is not None:
        query = query.filter(Application.id == application_id)
    if groups_ids is not None:
        query = query.filter(Application.group_id.in_(groups_ids))

    applications = query.all()

    if len(applications) == 0:
        raise exceptions.ApplicationsNotFound("There are no applications found")

    return applications


def delete_application(
    db_session: Session,
    application_id: uuid.UUID,
    groups_ids: List[uuid.UUID],
) -> Application:
    application = (
        db_session.query(Application)
        .filter(Application.id == application_id, Application.group_id.in_(groups_ids))
        .one_or_none()
    )
    if application is None:
        raise exceptions.ApplicationsNotFound(
            f"There are no application with id: {application_id}"
        )

    db_session.delete(application)
    db_session.commit()

    return application
