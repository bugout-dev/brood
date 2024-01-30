import uuid
from enum import Enum, unique

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as PgEnum
from sqlalchemy import ForeignKey, Index, MetaData, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ..models import Application, Group, User, utcnow

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


@unique
class ResourcePermissionsEnum(Enum):
    """
    Admin able to modify resources and it's permissions.
    Create, Read, Update, Delete - ephemeral permissions for internal application usage.
    """

    admin = "admin"
    create = "create"
    read = "read"
    update = "update"
    delete = "delete"


class Resource(Base):  # type: ignore
    """
    Represents resource which have permissions.
    """

    __tablename__ = "resources"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey(Application.id, ondelete="CASCADE"),
        nullable=False,
    )
    resource_data = Column(JSONB, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=utcnow(),
        onupdate=utcnow(),
        nullable=False,
    )

    # SQLAlchemy relationships
    holders = relationship(
        "ResourceHolderPermission",
        back_populates="resource",
        cascade="all, delete, delete-orphan",
    )


class ResourcePermission(Base):  # type: ignore
    """
    Describe available permissions for provided resource.
    """

    __tablename__ = "resource_permissions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    resource_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="CASCADE"),
    )
    permission = Column(String, nullable=False)


class ResourceHolderPermission(Base):  # type: ignore
    __tablename__ = "resource_holder_permissions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey(User.id, ondelete="CASCADE"), nullable=True
    )
    group_id = Column(
        UUID(as_uuid=True), ForeignKey(Group.id, ondelete="CASCADE"), nullable=True
    )
    resource_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="CASCADE"),
    )
    permission = Column(
        PgEnum(ResourcePermissionsEnum, name="resource_permissions_enum"),
        nullable=False,
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

    __table_args__ = (
        Index(
            "uq_resource_holder_permissions_user_id_resource_id_permission",
            "user_id",
            "resource_id",
            "permission",
            unique=True,
            postgresql_where=user_id.isnot(None),
        ),
        Index(
            "uq_resource_holder_permissions_group_id_resource_id_permission",
            "group_id",
            "resource_id",
            "permission",
            unique=True,
            postgresql_where=group_id.isnot(None),
        ),
    )

    # SQLAlchemy relationships
    resource = relationship("Resource", back_populates="holders")
