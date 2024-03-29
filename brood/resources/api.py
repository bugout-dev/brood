import logging
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

from fastapi import Body, Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm.session import Session

from ..data import UserWithGroupsResponse, VersionResponse
from ..db import yield_db_read_only_session, yield_db_session_from_env
from ..middleware import (
    request_user_authorization,
    request_user_authorization_with_groups,
)
from ..settings import BROOD_OPENAPI_LIST, DOCS_TARGET_PATH, ORIGINS
from . import actions, data, exceptions, models
from .version import BROOD_RESOURCES_VERSION

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
    user_id: UUID,
    resource_id: UUID,
    required_scopes: Set[data.ResourcePermissions],
    user_groups_ids: List[UUID],
) -> Tuple[
    Dict[data.HolderType, List[models.ResourcePermissionsEnum]], models.Resource
]:
    """
    Checks if the given user (who is a member of the groups specified by user_groups_ids) holds the
    given permission on the resource specified by resource_id.

    Returns: None if the user is a holder of that scope, and raises the appropriate HTTPException
    otherwise.
    """
    try:
        acl, resource = actions.acl_auth(
            db_session=db_session,
            user_id=user_id,
            user_group_id_list=user_groups_ids,
            resource_id=resource_id,
        )
        actions.acl_check(acl=acl, required_scopes=required_scopes)
    except exceptions.PermissionsNotFound:
        logger.error(
            f"User with id: {str(user_id)} does not have the appropriate permissions: {required_scopes} "
            f"for resource with id: {resource_id}"
        )
        raise HTTPException(status_code=404)
    except Exception:
        logger.error(
            f"Error checking permissions with id: {resource_id} for user with id: {str(user_id)}"
        )
        raise HTTPException(status_code=500)

    return acl, resource


@app.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    return VersionResponse(version=BROOD_RESOURCES_VERSION)


@app.post("/", tags=["resources"], response_model=data.ResourceResponse)
async def create_resource_handler(
    create_data: data.ResourceCreationRequest = Body(...),
    user_authorization_with_groups: Tuple[bool, UserWithGroupsResponse] = Depends(
        request_user_authorization_with_groups
    ),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceResponse:
    """
    Create the resource.
    Current user will inherit admin permissions to the resource.

    - **create_data** (dict):
        - **application_id** (uuid)
        - **resource_data** (dict)
    """
    is_token_restricted, current_user_with_groups = user_authorization_with_groups
    if is_token_restricted:
        raise HTTPException(
            status_code=403,
            detail="Restricted tokens are not authorized to create resource.",
        )

    try:
        application = actions.verify_application_ownership(
            db_session=db_session,
            application_id=create_data.application_id,
        )
    except exceptions.ApplicationNotFound:
        raise HTTPException(status_code=404, detail="Not found")
    except Exception as err:
        logger.error(f"Unhandled error in create_resource_handler: {str(err)}")
        raise HTTPException(status_code=500)

    if application.group_id not in [
        group.group_id for group in current_user_with_groups.groups
    ]:
        logger.info(
            f"User with ID: {str(current_user_with_groups.id)} does not have enough permissions to create resource in application with ID: {str(application.id)}"
        )
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        resource = actions.create_resource(
            db_session=db_session,
            user_id=current_user_with_groups.id,
            application=application,
            resource_data=create_data.resource_data,
        )
    except Exception as err:
        logger.error(f"Unhandled error in create_resource_handler: {str(err)}")
        raise HTTPException(status_code=500)

    return resource


@app.get("/", tags=["resources"], response_model=data.ResourcesListResponse)
async def get_resources_list_handler(
    request: Request,
    user_authorization_with_groups: Tuple[bool, UserWithGroupsResponse] = Depends(
        request_user_authorization_with_groups
    ),
    db_session=Depends(yield_db_read_only_session),
) -> data.ResourcesListResponse:
    """
    Get a list of available resources for the user.

    - **<query>** (string): Any query param to filter resources output by resource_data key
    """
    is_token_restricted, current_user_with_groups = user_authorization_with_groups
    if is_token_restricted:
        raise HTTPException(
            status_code=403,
            detail="Restricted tokens are not authorized to list resources.",
        )

    params = {param: request.query_params[param] for param in request.query_params}
    application_id = None
    if "application_id" in params.keys():
        application_id = params["application_id"]
        del params["application_id"]

    try:
        resources = actions.get_list_of_resources(
            db_session=db_session,
            user_id=current_user_with_groups.id,
            user_groups_ids=[
                group.group_id for group in current_user_with_groups.groups
            ],
            params=params,
            application_id=application_id,
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
    user_authorization_with_groups: Tuple[bool, UserWithGroupsResponse] = Depends(
        request_user_authorization_with_groups
    ),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceResponse:
    """
    Provides resource information.

    - **resource_id** (uuid): Resource ID
    """
    is_token_restricted, current_user_with_groups = user_authorization_with_groups
    if is_token_restricted:
        raise HTTPException(
            status_code=403,
            detail="Restricted tokens are not authorized to get resource.",
        )

    _, resource = ensure_resource_permission(
        db_session=db_session,
        user_id=current_user_with_groups.id,
        resource_id=resource_id,
        required_scopes={data.ResourcePermissions.any},
        user_groups_ids=[group.group_id for group in current_user_with_groups.groups],
    )

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
    user_authorization_with_groups: Tuple[bool, UserWithGroupsResponse] = Depends(
        request_user_authorization_with_groups
    ),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceResponse:
    """
    Update data of resource.

    - **resource_id** (uuid): Resource ID
    - **update** (dict): Key-value pair to update
    - **drop_keys** (list): List of keys to drop
    """
    is_token_restricted, current_user_with_groups = user_authorization_with_groups
    if is_token_restricted:
        raise HTTPException(
            status_code=403,
            detail="Restricted tokens are not authorized to update resource.",
        )

    _, resource = ensure_resource_permission(
        db_session=db_session,
        user_id=current_user_with_groups.id,
        resource_id=resource_id,
        required_scopes={data.ResourcePermissions.admin},
        user_groups_ids=[group.group_id for group in current_user_with_groups.groups],
    )
    try:
        updated_resource = actions.update_resource_data(
            db_session=db_session,
            resource=resource,
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
    user_authorization_with_groups: Tuple[bool, UserWithGroupsResponse] = Depends(
        request_user_authorization_with_groups
    ),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceResponse:
    """
    Delete existing resource.

    - **resource_id** (uuid): Resource ID
    """
    is_token_restricted, current_user_with_groups = user_authorization_with_groups
    if is_token_restricted:
        raise HTTPException(
            status_code=403,
            detail="Restricted tokens are not authorized to delete resource.",
        )

    _, resource = ensure_resource_permission(
        db_session=db_session,
        user_id=current_user_with_groups.id,
        resource_id=resource_id,
        required_scopes={data.ResourcePermissions.admin},
        user_groups_ids=[group.group_id for group in current_user_with_groups.groups],
    )
    try:
        db_session.delete(resource)
        db_session.commit()
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
    user_authorization_with_groups: Tuple[bool, UserWithGroupsResponse] = Depends(
        request_user_authorization_with_groups
    ),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceHoldersListResponse:
    """
    Add holder permissions to resource.

    - **resource_id** (uuid): Resource ID
    - **holder_id** (uuid): User or group ID
    - **holder_type** (string): Type of holder (user or group)
    - **permissions** (list): List of permissions to add (admin, create, read, update, delete)
    """
    is_token_restricted, current_user_with_groups = user_authorization_with_groups
    if is_token_restricted:
        raise HTTPException(
            status_code=403,
            detail="Restricted tokens are not authorized to add resource holder permissions.",
        )

    _, resource = ensure_resource_permission(
        db_session=db_session,
        user_id=current_user_with_groups.id,
        resource_id=resource_id,
        required_scopes={data.ResourcePermissions.admin},
        user_groups_ids=[group.group_id for group in current_user_with_groups.groups],
    )

    try:
        holder_permissions = actions.update_holder_permissions(
            method=data.UpdatePermissionsMethod.ADD,
            db_session=db_session,
            resource_id=resource.id,
            permissions_request=permissions_request,
        )
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
    user_authorization_with_groups: Tuple[bool, UserWithGroupsResponse] = Depends(
        request_user_authorization_with_groups
    ),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceHoldersListResponse:
    """
    Get resource holders separated to users and groups lists.

    - **resource_id** (uuid): Resource ID
    - **holder_id** (uuid, null): User or group ID
    """
    is_token_restricted, current_user_with_groups = user_authorization_with_groups
    if is_token_restricted:
        raise HTTPException(
            status_code=403,
            detail="Restricted tokens are not authorized to get resource holder permissions.",
        )

    _, resource = ensure_resource_permission(
        db_session=db_session,
        user_id=current_user_with_groups.id,
        resource_id=resource_id,
        required_scopes={data.ResourcePermissions.any},
        user_groups_ids=[group.group_id for group in current_user_with_groups.groups],
    )
    try:
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
    user_authorization_with_groups: Tuple[bool, UserWithGroupsResponse] = Depends(
        request_user_authorization_with_groups
    ),
    db_session=Depends(yield_db_session_from_env),
) -> data.ResourceHoldersListResponse:
    """
    Delete existing resource holder permissions.

    - **resource_id** (uuid): Resource ID
    - **holder_id** (uuid): User or group ID
    - **holder_type** (string): Type of holder (user or group)
    - **permissions** (list): List of permissions to add (admin, create, read, update, delete)
    """
    is_token_restricted, current_user_with_groups = user_authorization_with_groups
    if is_token_restricted:
        raise HTTPException(
            status_code=403,
            detail="Restricted tokens are not authorized to delete resource holder permissions.",
        )

    _, resource = ensure_resource_permission(
        db_session=db_session,
        user_id=current_user_with_groups.id,
        resource_id=resource_id,
        required_scopes={data.ResourcePermissions.admin},
        user_groups_ids=[group.group_id for group in current_user_with_groups.groups],
    )

    try:
        holder_permissions = actions.update_holder_permissions(
            method=data.UpdatePermissionsMethod.DELETE,
            db_session=db_session,
            resource_id=resource.id,
            permissions_request=permissions_request,
        )
    except Exception as err:
        logger.error(
            f"Unhandled error in delete_resource_holder_permissions_handler: {str(err)}"
        )
        raise HTTPException(status_code=500)

    return holder_permissions
