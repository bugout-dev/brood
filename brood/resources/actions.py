from collections import defaultdict
import logging
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm.session import Session

from . import data
from . import exceptions
from . import models
from ..models import Application

logger = logging.getLogger(__name__)


def acl_auth(
    db_session: Session, user_id: str, user_group_id_list: List[str], resource_id: UUID
) -> Dict[data.HolderType, List[str]]:
    """
    Checks the authorization in ResourceHolderPermission model. If it represents
    a verified user or group user belongs to and generates dictionary with
    permissions for user and group. Otherwise raises a 403 error.
    """

    acl: Dict[data.HolderType, List[str]] = {
        data.HolderType.user: [],
        data.HolderType.group: [],
    }
    permissions = (
        db_session.query(
            models.ResourceHolderPermission.user_id,
            models.ResourceHolderPermission.group_id,
            models.ResourcePermission.permission,
        )
        .join(
            models.ResourcePermission,
            models.ResourcePermission.id
            == models.ResourceHolderPermission.permission_id,
        )
        .filter(models.ResourceHolderPermission.resource_id == resource_id)
        .filter(
            or_(
                models.ResourceHolderPermission.user_id == user_id,
                models.ResourceHolderPermission.group_id.in_(user_group_id_list),
            )
        )
        .all()
    )

    if not permissions:
        raise exceptions.PermissionsNotFound("No permissions for requested information")

    for permission in permissions:
        # [0] - user_id, [1] - group_id, [2] - permission name
        if permission[0] is not None:
            acl[data.HolderType.user].append(permission[2])
        if permission[1] is not None:
            acl[data.HolderType.group].append(permission[2])

    return acl


def acl_check(
    acl: Dict[data.HolderType, List[str]],
    required_scopes: Set[data.ResourcePermissions],
    check_type: data.HolderType = None,
) -> None:
    """
    Checks if provided permissions from handler intersect with existing permissions for user/group.
    """
    if check_type is None:
        # [["read", "update"], ["update"]] -> ["read", "update"]
        permissions = {value for values in acl.values() for value in values}
    elif check_type in data.HolderType:
        permissions = {value for value in acl[check_type]}
    else:
        logger.warning("Provided wrong HolderType")
        raise exceptions.PermissionsNotFound("No permissions for requested information")

    required_scopes_values = {scope.value for scope in required_scopes}
    if not required_scopes_values.issubset(permissions):
        raise exceptions.PermissionsNotFound("No permissions for requested information")


def create_resource(
    db_session: Session,
    user_id: UUID,
    application_id: UUID,
    resource_data: Dict[str, Any],
) -> models.Resource:
    """
    Create new resource and permissions for that resource.
    Also attach current user to this permissions.
    """
    resource = models.Resource(
        application_id=application_id,
        resource_data=resource_data,
    )
    db_session.add(resource)
    db_session.commit()

    application = (
        db_session.query(Application).filter(Application.id == application_id).first()
    )

    for permission in data.ResourcePermissions:
        resource_permission = models.ResourcePermission(
            resource_id=resource.id,
            permission=permission.value,
        )
        db_session.add(resource_permission)
        db_session.commit()

        user_permission = models.ResourceHolderPermission(
            user_id=user_id,
            group_id=None,
            resource_id=resource.id,
            permission_id=resource_permission.id,
        )
        application_group_permission = models.ResourceHolderPermission(
            user_id=None,
            group_id=application.group_id,
            resource_id=resource.id,
            permission_id=resource_permission.id,
        )
        db_session.add(user_permission)
        db_session.add(application_group_permission)
        db_session.commit()

    return resource


def get_list_of_resources(
    db_session: Session,
    user_id: UUID,
    user_groups_ids: List[UUID],
    params: Dict[str, Any],
    application_id: Optional[str] = None,
) -> List[models.Resource]:
    """
    Return list of available resource to user.
    """
    query = (
        db_session.query(models.Resource)
        .join(
            models.ResourceHolderPermission,
            models.ResourceHolderPermission.resource_id == models.Resource.id,
        )
        .filter(
            or_(
                models.ResourceHolderPermission.user_id == user_id,
                models.ResourceHolderPermission.group_id.in_(user_groups_ids),
            )
        )
    )
    if application_id is not None:
        query = query.filter(models.Resource.application_id == application_id)
    for key, value in params.items():
        query = query.filter(models.Resource.resource_data[key].astext == value)

    resources = query.all()

    return resources


def get_resource(db_session: Session, resource_id: UUID) -> models.Resource:
    """
    Get resource by id or name.
    """
    query = db_session.query(models.Resource).filter(models.Resource.id == resource_id)
    resource = query.one_or_none()
    if resource is None:
        raise exceptions.ResourceNotFound("Not found requested resource")

    return resource


def update_resource_data(
    db_session: Session,
    resource_id: UUID,
    update_data: data.ResourceDataUpdateRequest,
) -> models.Resource:
    """
    Update resource data.
    """
    query = db_session.query(models.Resource).filter(models.Resource.id == resource_id)
    resource = query.one_or_none()
    if resource is None:
        raise exceptions.ResourceNotFound("Not found requested resource")

    # Update existing data
    resource_data = dict(resource.resource_data)
    for key, value in update_data.update.items():
        resource_data[key] = value
    # Remove data by key
    for drop_key in update_data.drop_keys:
        try:
            del resource_data[drop_key]
        except Exception:
            pass
    resource.resource_data = resource_data

    db_session.commit()

    return resource


def delete_resource(db_session: Session, resource_id: UUID) -> models.Resource:
    """
    Delete resource by id.
    """
    query = db_session.query(models.Resource).filter(models.Resource.id == resource_id)
    resource = query.one_or_none()
    if resource is None:
        raise exceptions.ResourceNotFound("Not found requested resource")

    db_session.delete(resource)
    db_session.commit()

    return resource


def add_holder_permissions(
    db_session: Session,
    resource_id: UUID,
    permissions_request: data.ResourcePermissionsRequest,
) -> None:
    """
    Create list of permissions for holder in resource.
    If permission already exists, this permissions will be passed.
    """
    holder_permissions_query = db_session.query(
        models.ResourceHolderPermission.permission_id
    ).filter(
        models.ResourceHolderPermission.resource_id == resource_id,
    )
    if permissions_request.holder_type == data.HolderType.user:
        holder_permissions_query = holder_permissions_query.filter(
            models.ResourceHolderPermission.user_id == permissions_request.holder_id
        )
    elif permissions_request.holder_type == data.HolderType.group:
        holder_permissions_query = holder_permissions_query.filter(
            models.ResourceHolderPermission.group_id == permissions_request.holder_id
        )
    else:
        raise Exception(f"Unexpected holder_type: {permissions_request.holder_type}")

    permissions_to_add_query = (
        db_session.query(models.ResourcePermission)
        .join(
            models.ResourceHolderPermission,
            models.ResourceHolderPermission.permission_id
            == models.ResourcePermission.id,
        )
        .filter(
            models.ResourceHolderPermission.resource_id == resource_id,
            models.ResourcePermission.permission.in_(
                [permission.value for permission in permissions_request.permissions]
            ),
            models.ResourcePermission.id.notin_(holder_permissions_query),
        )
    )

    new_permission = [
        models.ResourceHolderPermission(
            user_id=permissions_request.holder_id
            if permissions_request.holder_type == data.HolderType.user
            else None,
            group_id=permissions_request.holder_id
            if permissions_request.holder_type == data.HolderType.group
            else None,
            resource_id=resource_id,
            permission_id=permission.id,
        )
        for permission in permissions_to_add_query.all()
    ]

    db_session.add_all(new_permission)
    db_session.commit()


def get_resource_holders_permissions(
    db_session: Session, resource_id: UUID, holder_id: Optional[UUID] = None
) -> data.ResourceHoldersListResponse:
    """
    Get list of permissions for exact holder.
    """
    query = (
        db_session.query(
            models.ResourceHolderPermission.user_id,
            models.ResourceHolderPermission.group_id,
            models.ResourcePermission.permission,
        )
        .join(
            models.ResourcePermission,
            models.ResourcePermission.id
            == models.ResourceHolderPermission.permission_id,
        )
        .filter(models.ResourceHolderPermission.resource_id == resource_id)
    )
    if holder_id is not None:
        query = query.filter(
            or_(
                models.ResourceHolderPermission.user_id == holder_id,
                models.ResourceHolderPermission.group_id == holder_id,
            )
        )
    resource_holders_permissions = query.all()

    # Flat holders with their permissions.
    # (UUID_A, read), (UUID_A, update) -> (UUID_A, [read, update])
    users = list(
        filter(lambda holder: holder.user_id is not None, resource_holders_permissions)
    )
    users_sorted = sorted(users, key=lambda holder: holder[0])
    users_flat = defaultdict(list)
    for user in users_sorted:
        users_flat[user[0]].append(user[2])
    user_holders = [
        data.ResourceHolderResponse(
            id=user_id,
            holder_type=data.HolderType.user,
            permissions=[permission for permission in permissions],
        )
        for user_id, permissions in users_flat.items()
    ]

    groups = list(
        filter(lambda holder: holder.group_id is not None, resource_holders_permissions)
    )
    groups_sorted = sorted(groups, key=lambda holder: holder[1])
    groups_flat = defaultdict(list)
    for group in groups_sorted:
        groups_flat[group[1]].append(group[2])
    group_holders = [
        data.ResourceHolderResponse(
            id=group_id,
            holder_type=data.HolderType.group,
            permissions=[permission for permission in permissions],
        )
        for group_id, permissions in groups_flat.items()
    ]

    holders = user_holders + group_holders

    return data.ResourceHoldersListResponse(resource_id=resource_id, holders=holders)


def delete_resource_holder_permissions(
    db_session: Session,
    resource_id: UUID,
    permissions_request: data.ResourcePermissionsRequest,
) -> None:
    """
    Delete holder permissions if they exist.
    """
    holder_permissions_query = db_session.query(models.ResourceHolderPermission).filter(
        models.ResourceHolderPermission.resource_id == resource_id,
    )
    if permissions_request.holder_type == data.HolderType.user:
        holder_permissions_query = holder_permissions_query.filter(
            models.ResourceHolderPermission.user_id == permissions_request.holder_id
        )
    elif permissions_request.holder_type == data.HolderType.group:
        holder_permissions_query = holder_permissions_query.filter(
            models.ResourceHolderPermission.group_id == permissions_request.holder_id
        )
    else:
        raise Exception(f"Unexpected holder_type: {permissions_request.holder_type}")

    permissions_to_delete_query = holder_permissions_query.join(
        models.ResourcePermission,
        models.ResourcePermission.id == models.ResourceHolderPermission.permission_id,
    ).filter(
        models.ResourcePermission.permission.in_(
            [permission.value for permission in permissions_request.permissions]
        ),
    )

    permissions_to_delete = permissions_to_delete_query.all()
    if len(permissions_to_delete) == 0:
        raise exceptions.HolderPermissionsNotFound(
            f"There is no permissions for provided holder with id: {permissions_request.holder_id}"
        )

    for delete_permission in permissions_to_delete:
        db_session.delete(delete_permission)
    db_session.commit()
