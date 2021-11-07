import logging
from typing import Any, Dict, List, Set
from uuid import UUID

from fastapi import (
    Body,
    FastAPI,
    Form,
    Path,
    Depends,
    Request,
    Query,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm.session import Session

from . import actions
from . import data
from . import exceptions
from .version import BROOD_RESOURCES_VERSION
from ..data import VersionResponse
from .. import models as brood_models
from ..external import yield_db_session_from_env
from ..middleware import get_current_user
from ..settings import ORIGINS, DOCS_TARGET_PATH, BROOD_OPENAPI_LIST

SUBMODULE_NAME = "resources"

tags_metadata = [
    {"name": "resources", "description": "Operations with resources."},
    {"name": "resource holders", "description": "Operations with resource holders."},
]

logger = logging.getLogger(__name__)

app = FastAPI(
    title=f"Bugout {SUBMODULE_NAME} submodule",
    description=f"{SUBMODULE_NAME.capitalize()} API endpoints to provide users with groups management for external applications.",
    version=BROOD_RESOURCES_VERSION,
    openapi_tags=tags_metadata,
    openapi_url=f"/{DOCS_TARGET_PATH}/openapi.json"
    if SUBMODULE_NAME in BROOD_OPENAPI_LIST
    else None,
    docs_url=None,
    redoc_url=f"/{DOCS_TARGET_PATH}",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_resource_permission(
    db_session: Session,
    user_id: str,
    resource_id: UUID,
    required_scopes: Set[data.ResourcePermissions],
) -> None:
    """
    Checks if the given user (who is a member of the groups specified by user_groups_ids) holds the
    given permission on the resource specified by resource_id.

    Returns: None if the user is a holder of that scope, and raises the appropriate HTTPException
    otherwise.
    """
    try:
        group_users_list = (
            db_session.query(brood_models.GroupUser)
            .filter(brood_models.GroupUser.user_id == user_id)
            .all()
        )
        user_groups_ids = [group.group_id for group in group_users_list]
        acl = actions.acl_auth(db_session, user_id, user_groups_ids, resource_id)
        actions.acl_check(acl, required_scopes)
    except exceptions.PermissionsNotFound:
        logger.error(
            f"User with id: {user_id} does not have the appropriate permissions: {required_scopes} "
            f"for resource with id: {resource_id}"
        )
        raise HTTPException(status_code=404)
    except Exception:
        logger.error(
            f"Error checking permissions for user with id: {user_id} in journal with id: {resource_id}"
        )
        raise HTTPException(status_code=500)


@app.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    return VersionResponse(version=BROOD_RESOURCES_VERSION)


@app.post("/", tags=["resources"], response_model=data.ResourceResponse)
async def create_resource_handler(
    data: data.ResourceCreationRequest = Body(...),
    current_user: brood_models.User = Depends(get_current_user),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceResponse:
    """
    Create the resource.
    Current user will inherit all permissions to the resource.

    - **data** (dict):
        - **application_id** (uuid)
        - **resource_data** (dict)
    """
    try:
        resource = actions.create_resource(
            db_session=db_session,
            user_id=current_user.id,
            application_id=data.application_id,
            resource_data=data.resource_data,
        )
    except Exception as err:
        logger.error(f"Unhandled error in create_resource_handler: {str(err)}")
        raise HTTPException(status_code=500)

    return resource


@app.get("/", tags=["resources"], response_model=data.ResourcesListResponse)
async def get_resources_list_handler(
    request: Request,
    current_user: brood_models.User = Depends(get_current_user),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourcesListResponse:
    """
    Get a list of available resources for the user.

    - **<query>** (string): Any query param to filter resources output by resource_data key
    """
    params = {param: request.query_params[param] for param in request.query_params}
    application_id = None
    if "application_id" in params.keys():
        application_id = params["application_id"]
        del params["application_id"]

    try:
        group_users_list = (
            db_session.query(brood_models.GroupUser)
            .filter(brood_models.GroupUser.user_id == current_user.id)
            .all()
        )
        user_groups_ids = [group.group_id for group in group_users_list]
        resources = actions.get_list_of_resources(
            db_session, current_user.id, user_groups_ids, params, application_id
        )
    except Exception as err:
        logger.error(f"Unhandled error in get_resources_list_handler: {str(err)}")
        raise HTTPException(status_code=500)

    return data.ResourcesListResponse(
        resources=[
            data.ResourceResponse(
                id=resource.id,
                application_id=resource.application_id,
                resource_data=resource.resource_data,
                created_at=resource.created_at,
                updated_at=resource.updated_at,
            )
            for resource in resources
        ]
    )


@app.get("/{resource_id}", tags=["resources"], response_model=data.ResourceResponse)
async def get_resource_handler(
    resource_id: UUID = Path(...),
    current_user: brood_models.User = Depends(get_current_user),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceResponse:
    """
    Provides resource information.

    - **resource_id** (uuid): Resource ID
    """
    ensure_resource_permission(
        db_session,
        current_user.id,
        resource_id,
        {data.ResourcePermissions.READ},
    )
    try:
        resource = actions.get_resource(db_session, resource_id=resource_id)
    except exceptions.ResourceNotFound:
        raise HTTPException(status_code=404, detail="Resource not found")
    except Exception as err:
        logger.error(f"Unhandled error in get_resource_handler: {str(err)}")
        raise HTTPException(status_code=500)

    return data.ResourceResponse(
        id=resource.id,
        application_id=resource.application_id,
        resource_data=resource.resource_data,
        created_at=resource.created_at,
        updated_at=resource.updated_at,
    )


@app.put("/{resource_id}", tags=["resources"], response_model=data.ResourceResponse)
async def update_resource_handler(
    resource_id: UUID = Path(...),
    update_data: data.ResourceDataUpdateRequest = Body(...),
    current_user: brood_models.User = Depends(get_current_user),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceResponse:
    """
    Update data of resource.

    - **resource_id** (uuid): Resource ID
    - **update** (dict): Key-value pair to update
    - **drop_keys** (list): List of keys to drop
    """
    ensure_resource_permission(
        db_session,
        current_user.id,
        resource_id,
        {data.ResourcePermissions.UPDATE},
    )
    try:
        updated_resource = actions.update_resource_data(
            db_session=db_session,
            resource_id=resource_id,
            update_data=update_data,
        )
    except exceptions.ResourceNotFound:
        raise HTTPException(status_code=404, detail="Resource not found")
    except Exception as err:
        logger.error(f"Unhandled error in get_resource_handler: {str(err)}")
        raise HTTPException(status_code=500)

    return data.ResourceResponse(
        id=updated_resource.id,
        application_id=updated_resource.application_id,
        resource_data=updated_resource.resource_data,
        created_at=updated_resource.created_at,
        updated_at=updated_resource.updated_at,
    )


@app.delete("/{resource_id}", tags=["resources"], response_model=data.ResourceResponse)
async def delete_resource_handler(
    resource_id: UUID = Path(...),
    current_user: brood_models.User = Depends(get_current_user),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceResponse:
    """
    Delete existing resource.

    - **resource_id** (uuid): Resource ID
    """
    ensure_resource_permission(
        db_session,
        current_user.id,
        resource_id,
        {data.ResourcePermissions.ADMIN},
    )
    try:
        resource = actions.delete_resource(db_session, resource_id)
    except exceptions.ResourceNotFound:
        raise HTTPException(status_code=404, detail="Resource not found")
    except Exception as err:
        logger.error(f"Unhandled error in delete_resource_handler: {str(err)}")
        raise HTTPException(status_code=500)

    return data.ResourceResponse(
        id=resource.id,
        application_id=resource.application_id,
        resource_data=resource.resource_data,
        created_at=resource.created_at,
        updated_at=resource.updated_at,
    )


@app.post(
    "/{resource_id}/holders",
    tags=["resource holders"],
    response_model=data.ResourceHoldersListResponse,
)
async def add_resource_holder_permissions_handler(
    resource_id: UUID = Path(...),
    permissions_request: data.ResourcePermissionsRequest = Body(...),
    current_user: brood_models.User = Depends(get_current_user),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceHoldersListResponse:
    """
    Add holder permissions to resource.

    - **resource_id** (uuid): Resource ID
    - **holder_id** (uuid): User or group ID
    - **holder_type** (string): Type of holder (user or group)
    - **permissions** (list): List of permissions to add (admin, create, read, update, delete)
    """
    required_permissions = {data.ResourcePermissions.UPDATE}
    if data.ResourcePermissions.ADMIN in permissions_request.permissions:
        required_permissions.add(data.ResourcePermissions.ADMIN)
    if data.ResourcePermissions.DELETE in permissions_request.permissions:
        required_permissions.add(data.ResourcePermissions.DELETE)
    ensure_resource_permission(
        db_session,
        current_user.id,
        resource_id,
        required_permissions,
    )

    try:
        resource = actions.get_resource(db_session, resource_id=resource_id)
        actions.add_holder_permissions(db_session, resource.id, permissions_request)
        holder_permissions = actions.get_resource_holders_permissions(
            db_session, resource_id, permissions_request.holder_id
        )
    except exceptions.ResourceNotFound:
        raise HTTPException(status_code=404, detail="Resource not found")
    except Exception as err:
        logger.error(
            f"Unhandled error in add_resource_holder_permissions_handler: {str(err)}"
        )
        raise HTTPException(status_code=500)

    return holder_permissions


@app.get(
    "/{resource_id}/holders",
    tags=["resource holders"],
    response_model=data.ResourceHoldersListResponse,
)
async def get_resource_holders_permissions_handler(
    resource_id: UUID = Path(...),
    holder_id: UUID = Query(None),
    current_user: brood_models.User = Depends(get_current_user),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceHoldersListResponse:
    """
    Get resource holders separated to users and groups lists.

    - **resource_id** (uuid): Resource ID
    - **holder_id** (uuid, null): User or group ID
    """
    ensure_resource_permission(
        db_session,
        current_user.id,
        resource_id,
        {data.ResourcePermissions.READ},
    )
    try:
        resource = actions.get_resource(db_session, resource_id=resource_id)
        resource_holders_permissions = actions.get_resource_holders_permissions(
            db_session, resource.id, holder_id=holder_id
        )
    except exceptions.ResourceNotFound:
        raise HTTPException(status_code=404, detail="Resource not found")
    except Exception as err:
        logger.error(
            f"Unhandled error in get_resource_holders_permissions_handler: {str(err)}"
        )
        raise HTTPException(status_code=500)

    return resource_holders_permissions


@app.delete(
    "/{resource_id}/holders",
    tags=["resource holders"],
    response_model=data.ResourceHoldersListResponse,
)
async def delete_resource_holder_permissions_handler(
    resource_id: UUID = Path(...),
    permissions_request: data.ResourcePermissionsRequest = Body(...),
    current_user: brood_models.User = Depends(get_current_user),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceHoldersListResponse:
    """
    Delete existing resource holder permissions.

    - **resource_id** (uuid): Resource ID
    - **holder_id** (uuid): User or group ID
    - **holder_type** (string): Type of holder (user or group)
    - **permissions** (list): List of permissions to add (admin, create, read, update, delete)
    """
    required_permissions = {data.ResourcePermissions.UPDATE}
    if data.ResourcePermissions.ADMIN in permissions_request.permissions:
        required_permissions.add(data.ResourcePermissions.ADMIN)
    if data.ResourcePermissions.DELETE in permissions_request.permissions:
        required_permissions.add(data.ResourcePermissions.DELETE)
    ensure_resource_permission(
        db_session,
        current_user.id,
        resource_id,
        required_permissions,
    )

    try:
        resource = actions.get_resource(db_session, resource_id=resource_id)
        actions.delete_resource_holder_permissions(
            db_session, resource.id, permissions_request
        )
        holder_permissions = actions.get_resource_holders_permissions(
            db_session, resource_id, permissions_request.holder_id
        )
    except exceptions.ResourceNotFound:
        raise HTTPException(status_code=404, detail="Resource not found")
    except exceptions.HolderPermissionsNotFound:
        raise HTTPException(
            status_code=404, detail="Holder does not have these permissions"
        )
    except Exception as err:
        logger.error(
            f"Unhandled error in delete_resource_holder_permissions_handler: {str(err)}"
        )
        raise HTTPException(status_code=500)

    return holder_permissions
