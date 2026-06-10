from sqlalchemy import Column, Integer, ForeignKey
from app.database.db import Base

class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = {"extend_existing": True}  # <-- añade esto

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)

