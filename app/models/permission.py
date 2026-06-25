from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base
from app.models.role import role_permissions  # importamos pivote de role.py

class Permission(Base):
    __tablename__ = "permissions"

    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    # Relación many-to-many con Role
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )

