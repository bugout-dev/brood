"""
Ref to changing an Enum in Python using SQLAlchemy:
https://markrailton.com/blog/creating-migrations-when-changing-an-enum-in-python-using-sql-alchemy
"""
from enum import Enum, unique
import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Enum as PgEnum,
    PrimaryKeyConstraint,
    MetaData,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.schema import UniqueConstraint

"""
Naming conventions doc
https://docs.sqlalchemy.org/en/13/core/constraints.html#configuring-constraint-naming-conventions
"""
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)

"""
Creating a utcnow function which runs on the Posgres database server when created_at and updated_at
fields are populated.

Following:
1. https://docs.sqlalchemy.org/en/13/core/compiler.html#utc-timestamp-function
2. https://www.postgresql.org/docs/current/functions-datetime.html#FUNCTIONS-DATETIME-CURRENT
3. https://stackoverflow.com/a/33532154/13659585
"""


class utcnow(expression.FunctionElement):
    type = DateTime


@compiles(utcnow, "postgresql")
def pg_utcnow(element, compiler, **kwargs):
    return "TIMEZONE('utc', statement_timestamp())"


@unique
class Role(Enum):
    """
    Owners able to see payment information and subscribe to plans.
    Admins able to manage group as owners but without access to payment information.
    Members only able to add new members to group without additional permission.
    """

    owner = "owner"
    admin = "admin"
    member = "member"


@unique
class TokenType(Enum):
    bugout = "bugout"
    slack = "slack"
    github = "github"


class User(Base):  # type: ignore
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    username = Column(String(100), unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, nullable=False)
    normalized_email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    auth_type = Column(String(50), nullable=False)
    verified = Column(Boolean, default=False, nullable=False, index=True)
    autogenerated = Column(Boolean, default=False, nullable=False)

    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "applications.id", name="fk_users_applications_id", ondelete="CASCADE"
        ),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=utcnow(),
        onupdate=utcnow(),
        nullable=False,
    )

    tokens = relationship(
        "Token", back_populates="user", cascade="all, delete, delete-orphan"
    )
    groups = relationship(
        "GroupUser", back_populates="user", cascade="all, delete, delete-orphan"
    )
    group_limit = relationship(
        "UserGroupLimit", back_populates="user", cascade="all, delete, delete-orphan"
    )


class Token(Base):  # type: ignore
    __tablename__ = "tokens"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="fk_tokens_user_id", ondelete="CASCADE"),
    )
    active = Column(Boolean, default=False, nullable=False, index=True)

    token_type = Column(PgEnum(TokenType, name="token_type"), nullable=False)
    note = Column(String, nullable=True)

    # Restricted tokens cannot perform any operations against the Brood API besides identifying
    # a user
    restricted = Column(Boolean, default=False, nullable=False, index=True)

    created_at = Column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=utcnow(),
        onupdate=utcnow(),
        nullable=False,
    )

    user = relationship("User", back_populates="tokens")


class VerificationEmail(Base):  # type: ignore
    __tablename__ = "verification_emails"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    verification_code = Column(String(6))
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id", name="fk_verification_emails_user_id", ondelete="CASCADE"
        ),
        index=True,
    )
    active = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=utcnow(),
        onupdate=utcnow(),
        nullable=False,
    )


class ResetPassword(Base):  # type: ignore
    __tablename__ = "reset_passwords"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="fk_reset_passwords_user_id", ondelete="CASCADE"),
        index=True,
    )
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )


class Group(Base):  # type: ignore
    __tablename__ = "groups"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    name = Column(String(100), nullable=False)
    parent = Column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", name="fk_groups_parent", ondelete="SET NULL"),
        nullable=True,
    )
    autogenerated = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=utcnow(),
        onupdate=utcnow(),
        nullable=False,
    )

    user_ids = relationship(
        "GroupUser", back_populates="group", cascade="all, delete, delete-orphan"
    )
    subscriptions = relationship(
        "Subscription", back_populates="group", cascade="all, delete, delete-orphan"
    )


class GroupUser(Base):  # type: ignore
    """
    Relationship between users and groups. User can be
    an owner or a regular member of groups.

    Relevant sqlalchemy documentation on many-many relationships:
    https://docs.sqlalchemy.org/en/13/orm/basic_relationships.html#many-to-many
    """

    __tablename__ = "group_users"
    __table_args__ = (PrimaryKeyConstraint("group_id", "user_id"),)

    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", name="fk_group_users_group_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="fk_group_users_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_type = Column(PgEnum(Role, name="user_type"), nullable=False)

    group = relationship("Group", back_populates="user_ids")
    user = relationship("User", back_populates="groups")


class GroupInvite(Base):  # type: ignore
    """
    Invite to group from user who belongs to this group.
    """

    __tablename__ = "group_invites"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", name="fk_group_invites_group_id", ondelete="CASCADE"),
        nullable=False,
    )
    initiator_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id", name="fk_group_invites_initiator_user_id", ondelete="CASCADE"
        ),
        nullable=False,
    )
    invited_email = Column(String, nullable=True)
    user_type = Column(String, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=utcnow(),
        onupdate=utcnow(),
        nullable=False,
    )


class UserGroupLimit(Base):  # type: ignore
    """
    This model is used to impose a limit on how many groups a given user can be a part of (in any
    role).
    """

    __tablename__ = "user_group_limits"

    id = Column(Integer, primary_key=True, autoincrement=True,)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="fk_user_group_limits_user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    group_limit = Column(Integer, nullable=False)

    user = relationship("User", back_populates="group_limit")


class Subscription(Base):  # type: ignore
    __tablename__ = "subscriptions"
    __table_args__ = (PrimaryKeyConstraint("group_id", "subscription_plan_id"),)

    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", name="fk_subscriptions_group_id", ondelete="CASCADE"),
        nullable=False,
    )
    subscription_plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "subscription_plans.id",
            name="fk_subscription_plans_subscription_plan_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    units = Column(Integer, nullable=False)
    active = Column(Boolean, default=False, nullable=False)

    group = relationship("Group", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")


class SubscriptionPlan(Base):  # type: ignore
    """
    Describes the available subscription plans for organizations.
    """

    __tablename__ = "subscription_plans"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    default_units = Column(Integer, nullable=True)
    plan_type = Column(String, nullable=False)
    public = Column(Boolean, nullable=False)

    stripe_product_id = Column(String, nullable=True)
    stripe_price_id = Column(String, nullable=True)

    subscriptions = relationship(
        "Subscription", back_populates="plan", cascade="all, delete, delete-orphan"
    )


class KVBrood(Base):  # type: ignore
    """
    Special table for unique variables.
    """

    __tablename__ = "kv_brood"

    kv_key = Column(String, primary_key=True, unique=True, nullable=False,)
    kv_value = Column(String, nullable=False,)


class Application(Base):  # type: ignore
    """
    Resource pooling application.
    """

    __tablename__ = "applications"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", name="fk_applications_group_id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
