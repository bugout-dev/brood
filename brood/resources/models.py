import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    MetaData,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID

from ..models import utcnow, User, Group, Application

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
    permissions = relationship(
        "ResourcePermission",
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

    # SQLAlchemy relationships
    resource = relationship("Resource", back_populates="permissions")


class ResourceHolderPermission(Base):  # type: ignore
    __tablename__ = "resource_holder_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", "resource_id", "permission_id"),
    )
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
    permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resource_permissions.id", ondelete="CASCADE"),
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
