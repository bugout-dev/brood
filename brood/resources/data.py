from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ResourcePermissions(Enum):
    ADMIN = "admin"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class HolderType(Enum):
    user = "user"
    group = "group"


class ResourceResponse(BaseModel):
    id: UUID
    name: str
    application_id: str
    description: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ResourcesListResponse(BaseModel):
    resources: List[ResourceResponse] = Field(default_factory=list)


class ResourceHolderResponse(BaseModel):
    id: UUID
    holder_type: HolderType
    permissions: Optional[List[ResourcePermissions]] = Field(default_factory=list)


class ResourceHoldersListResponse(BaseModel):
    resource_id: UUID
    holders: List[ResourceHolderResponse] = Field(default_factory=list)


class ResourcePermissionsRequest(BaseModel):
    holder_id: UUID
    holder_type: HolderType
    permissions: List[ResourcePermissions] = Field(default_factory=list)
