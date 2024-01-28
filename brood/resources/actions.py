import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm.session import Session

from ..models import Application
from . import data, exceptions, models

logger = logging.getLogger(__name__)


def acl_auth(
    db_session: Session,
    user_id: UUID,
    user_group_id_list: List[UUID],
    resource_id: UUID,
) -> Tuple[
    Dict[data.HolderType, List[models.ResourcePermissionsEnum]], models.Resource
]:
    """
    Checks the authorization in ResourceHolderPermission model. If it represents
    a verified user or group user belongs to and generates dictionary with
    permissions for user and group. Otherwise raises a 403 error.
    """

    acl: Dict[data.HolderType, List[models.ResourcePermissionsEnum]] = {
        data.HolderType.user: [],
        data.HolderType.group: [],
    }
    permissions = (
        db_session.query(
            models.ResourceHolderPermission.user_id,
            models.ResourceHolderPermission.group_id,
            models.ResourceHolderPermission.permission,
            models.Resource,
        )
        .join(
            models.Resource,
            models.ResourceHolderPermission.resource_id == models.Resource.id,
        )
        .filter(models.ResourceHolderPermission.resource_id == resource_id)
        .filter(
            or_(
                models.ResourceHolderPermission.user_id == str(user_id),
                models.ResourceHolderPermission.group_id.in_(user_group_id_list),
            )
        )
        .all()
    )

    if not permissions:
        raise exceptions.PermissionsNotFound("No permissions for requested information")

    for permission in permissions:
        # [0] - user_id, [1] - group_id, [2] - permission name, [3] - resource
        if permission[0] is not None:
            acl[data.HolderType.user].append(permission[2])
        if permission[1] is not None:
            acl[data.HolderType.group].append(permission[2])

    resource = permissions[0][3]

    return acl, resource


def acl_check(
    acl: Dict[data.HolderType, List[models.ResourcePermissionsEnum]],
    required_scopes: Set[data.ResourcePermissions],
    check_type: Optional[data.HolderType] = None,
) -> None:
    """
    Checks if provided permissions from handler intersect with existing permissions for user/group.
    """
    if check_type is None:
        # [["read", "update"], ["update"]] -> ["read", "update"]
        permissions = {
            permission.value for d_values in acl.values() for permission in d_values
        }
    elif check_type in data.HolderType:
        permissions = {permission.value for permission in acl[check_type]}
    else:
        logger.warning("Provided wrong HolderType")
        raise exceptions.PermissionsNotFound("No permissions for requested information")

    required_scopes_values = {scope.value for scope in required_scopes}

    # If required_scopes is Any - user can access to resource if handle any permission for this resource.
    if data.ResourcePermissions.any.value in required_scopes_values:
        if len(permissions) == 0:
            raise exceptions.PermissionsNotFound(
                "No permissions for requested information"
            )
        return

    if not required_scopes_values.issubset(permissions):
        raise exceptions.PermissionsNotFound("No permissions for requested information")


def create_resource(
    db_session: Session,
    user_id: UUID,
    application_id: UUID,
    resource_data: Dict[str, Any],
    user_groups_ids: List[UUID],
) -> models.Resource:
    """
    Create new resource and permissions for that resource.
    """
    application: Application = (
        db_session.query(Application).filter(Application.id == application_id).first()
    )

    if application.group_id not in user_groups_ids:
        raise exceptions.NotEnoughPermissions(
            "Not enough permissions to create resource"
        )

    resource = models.Resource(
        id=uuid4(),
        application_id=application_id,
        resource_data=resource_data,
    )
    db_session.add(resource)

    user_permission = models.ResourceHolderPermission(
        user_id=user_id,
        group_id=None,
        resource_id=resource.id,
        permission=models.ResourcePermissionsEnum.admin,
    )
    application_group_permission = models.ResourceHolderPermission(
        user_id=None,
        group_id=application.group_id,
        resource_id=resource.id,
        permission=models.ResourcePermissionsEnum.admin,
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
    resource: models.Resource,
    update_data: data.ResourceDataUpdateRequest,
) -> models.Resource:
    """
    Update resource data.
    """
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


def update_holder_permissions(
    method: data.UpdatePermissionsMethod,
    db_session: Session,
    resource_id: UUID,
    permissions_request: data.ResourcePermissionsRequest,
) -> data.ResourceHoldersListResponse:
    """
    Create list of permissions for holder in resource.
    If permission already exists, this permissions will be passed.
    """
    existing_permissions_query = db_session.query(
        models.ResourceHolderPermission
    ).filter(
        models.ResourceHolderPermission.resource_id == resource_id,
    )
    if permissions_request.holder_type == data.HolderType.user:
        existing_permissions_query = existing_permissions_query.filter(
            models.ResourceHolderPermission.user_id == permissions_request.holder_id
        )
    elif permissions_request.holder_type == data.HolderType.group:
        existing_permissions_query = existing_permissions_query.filter(
            models.ResourceHolderPermission.group_id == permissions_request.holder_id
        )
    else:
        raise ValueError("Invalid holder type")

    existing_permissions = []
    existing_permissions_values = []
    for p in existing_permissions_query.all():
        existing_permissions.append(p)
        existing_permissions_values.append(p.permission.value)

    holder = data.ResourceHolderResponse(
        id=permissions_request.holder_id,
        holder_type=permissions_request.holder_type,
        permissions=existing_permissions_values,
    )

    update_permissions: List[models.ResourceHolderPermission] = []
    for permission in permissions_request.permissions:
        if (
            method == data.UpdatePermissionsMethod.ADD
            and permission.value not in existing_permissions_values
        ):
            update_permissions.append(
                models.ResourceHolderPermission(
                    user_id=permissions_request.holder_id
                    if permissions_request.holder_type == data.HolderType.user
                    else None,
                    group_id=permissions_request.holder_id
                    if permissions_request.holder_type == data.HolderType.group
                    else None,
                    resource_id=resource_id,
                    permission=permission.value,
                )
            )
            holder.permissions.append(permission.value)
        if (
            method == data.UpdatePermissionsMethod.DELETE
            and permission.value in existing_permissions_values
        ):
            update_permissions.append(
                list(
                    filter(lambda p: p.permission == permission, existing_permissions)
                )[0]
            )
            holder.permissions.remove(permission)

    if len(update_permissions) > 0:
        if method == data.UpdatePermissionsMethod.ADD:
            db_session.add_all(update_permissions)
        elif method == data.UpdatePermissionsMethod.DELETE:
            for p in update_permissions:
                db_session.delete(p)
        db_session.commit()

    return data.ResourceHoldersListResponse(
        resource_id=resource_id,
        holders=[holder],
    )


def get_resource_holders_permissions(
    db_session: Session, resource_id: UUID, holder_id: Optional[UUID] = None
) -> data.ResourceHoldersListResponse:
    """
    Get list of permissions for exact holder.
    """
    query = db_session.query(
        models.ResourceHolderPermission.user_id,
        models.ResourceHolderPermission.group_id,
        models.ResourceHolderPermission.permission,
    ).filter(models.ResourceHolderPermission.resource_id == resource_id)
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
