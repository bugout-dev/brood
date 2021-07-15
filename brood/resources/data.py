from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
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


class ResourceCreationRequest(BaseModel):
    application_id: UUID
    resource_data: Dict[str, Any]


class ResourceResponse(BaseModel):
    id: UUID
    application_id: UUID
    resource_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ResourcesListResponse(BaseModel):
    resources: List[ResourceResponse] = Field(default_factory=list)


class ResourceDataUpdateRequest(BaseModel):
    update: Dict[str, Any]
    drop_keys: List[str] = Field(default_factory=list)


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
