"""
Pydantic schemas for the Brood HTTP API
"""
from datetime import datetime
from enum import Enum, unique
from typing import List, Optional
import uuid

from pydantic import BaseModel, Field, validator, HttpUrl

from .models import Role, TokenType


@unique
class SubscriptionSessionType(Enum):
    portal = "portal"
    checkout = "checkout"
    humbug = "humbug"
    none = None


@unique
class SubscriptionPlanType(Enum):
    seats = "seats"
    events = "events"


class RequestDependencyResponse(BaseModel):
    """
    Model for __call__ response of RequestDependency Injection class.
    """

    auth_scheme: Optional[str]


class PingResponse(BaseModel):
    """
    Schema for ping response
    """

    status: str


class VersionResponse(BaseModel):
    """
    Schema for responses on /version endpoint
    """

    version: str


class CORSResponse(BaseModel):
    cors: str


class TokenResponse(BaseModel):
    """
    Schema for a registered token object

    TODO(kompotkot): DEPRECATED! access_token field with generate_access_token()
    validator deprecated and should be removed after 2021-01-16.
    """

    id: uuid.UUID
    access_token: Optional[uuid.UUID]
    user_id: uuid.UUID
    active: bool
    token_type: Optional[TokenType]
    note: Optional[str]
    created_at: datetime
    updated_at: datetime
    restricted: bool

    class Config:
        orm_mode = True

    @validator("access_token", always=True)
    def generate_access_token(cls, v, values):
        return values["id"]


class UserResponse(BaseModel):
    """
    Schema for a registered user.
    """

    id: uuid.UUID = Field(alias="user_id")
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    normalized_email: Optional[str] = None
    verified: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    autogenerated: Optional[bool] = None
    application_id: Optional[uuid.UUID] = None
    web3_address: Optional[str] = None

    class Config:
        orm_mode = True
        # https://github.com/tiangolo/fastapi/issues/923
        allow_population_by_field_name = True


class UserInListResponse(BaseModel):
    """
    Represents users in list of group members.
    """

    id: uuid.UUID
    username: str
    email: str
    user_type: Role


class UsersListResponse(BaseModel):
    """
    Returns list of members belongs to group
    """

    id: uuid.UUID
    name: str
    users: List[UserInListResponse] = Field(default_factory=list)
    num_users: int
    num_seats: int


class ResetPasswordResponse(BaseModel):
    """
    Schema for a password reset request
    """

    reset_password: str


class GroupInviteMessageResponse(BaseModel):
    """
    Schema for a group invites message.
    """

    personal: Optional[bool] = None
    message: Optional[str] = None


class GroupInviteResponse(BaseModel):
    """
    Schema for a group invites.
    """

    id: uuid.UUID
    group_id: uuid.UUID
    initiator_user_id: uuid.UUID
    email: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime


class GroupInvitesListResponse(BaseModel):
    invites: List[GroupInviteResponse] = Field(default_factory=list)


class GroupChildResponse(BaseModel):
    """
    Child group schema.
    """

    id: uuid.UUID
    name: str


class GroupFindResponse(BaseModel):
    id: uuid.UUID
    name: str
    autogenerated: bool


class GroupResponse(BaseModel):
    """
    Schema for a valid group.

    TODO(kompotkot): DEPRECATED! group_name field with generate_group_name()
    validator deprecated and should be removed after 2021-01-16.
    """

    id: uuid.UUID
    name: str
    group_name: Optional[str]
    autogenerated: bool
    subscriptions: List[uuid.UUID] = Field(default_factory=list)
    parent: Optional[uuid.UUID] = None
    children_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

    @validator("group_name", always=True)
    def generate_group_name(cls, v, values):
        return values["name"]


class GroupListResponse(BaseModel):
    """
    Returns list of groups.
    """

    groups: List[GroupResponse] = Field(default_factory=list)


class GroupUserResponse(BaseModel):
    """
    Joint Group and GroupUsers schema.
    """

    group_id: uuid.UUID
    user_id: uuid.UUID
    user_type: Role
    autogenerated: Optional[bool] = None
    group_name: Optional[str] = None
    parent: Optional[uuid.UUID] = None
    num_users: Optional[int] = None
    num_seats: Optional[int] = None


class GroupUserListResponse(BaseModel):
    """
    Returns list of groups for user with group id and name
    """

    groups: List[GroupUserResponse] = Field(default_factory=list)


class SubscriptionPlanResponse(BaseModel):
    """
    Schema for a valid subscription plan.
    """

    id: uuid.UUID
    name: str
    description: str

    class Config:
        orm_mode = True


class SubscriptionPlanListResponse(BaseModel):
    """
    Returns list of subscription plans.
    """

    plans: List[SubscriptionPlanResponse] = Field(default_factory=list)


class SubscriptionManageResponse(BaseModel):
    plan_id: uuid.UUID
    session_type: SubscriptionSessionType
    session_id: Optional[str]
    session_url: Optional[str]


class SubscriptionUnitsResponse(BaseModel):
    group_id: uuid.UUID
    plan_id: uuid.UUID
    plan_name: str
    plan_type: SubscriptionPlanType
    units: int


class SubscriptionUnitsListResponse(BaseModel):
    """
    Returns list of active subscriptions with units.
    """

    subscriptions: List[SubscriptionUnitsResponse] = Field(default_factory=list)


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    name: str
    description: Optional[str] = None


class ApplicationsListResponse(BaseModel):
    applications: List[ApplicationResponse] = Field(default_factory=list)


class UserWithGroupsResponse(UserResponse):
    groups: List[GroupUserResponse] = Field(default_factory=list)
