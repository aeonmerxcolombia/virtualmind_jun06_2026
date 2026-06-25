from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base
from app.models.user import user_roles  # importamos el pivote definido en user.py

# Tabla pivote rol ↔ permiso
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id",      Integer, ForeignKey("roles.id",       ondelete="CASCADE")),
    Column("permission_id",Integer, ForeignKey("permissions.id", ondelete="CASCADE"))
)

class Role(Base):
    __tablename__ = "roles"

    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    # Relación many-to-many con User
    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )

    # Relación many-to-many con Permission
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )

