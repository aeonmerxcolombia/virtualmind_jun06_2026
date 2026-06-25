from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base

class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = {'extend_existing': True}
    
    # 1. Quitamos el 'id' inventado.
    # 2. Renombramos 'user_id' a 'user_uid' para que haga match perfecto con user.py
    # 3. Las hacemos primary_key=True a ambas para formar la llave compuesta.
    user_uid = Column(String(255), ForeignKey("usuarios.uid", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

    # Relaciones de solo lectura para no chocar con el modelo User
    user = relationship("User", viewonly=True)
    role = relationship("Role", viewonly=True)
