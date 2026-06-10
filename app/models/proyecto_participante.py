from sqlalchemy import Column, BigInteger, String, ForeignKey, Integer, UniqueConstraint
from app.database.db import Base

class ProyectoParticipante(Base):
    __tablename__ = "proyecto_participantes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_uid = Column(String(255), nullable=False, index=True)
    role_id = Column(Integer, nullable=False, default=1, index=True)

    __table_args__ = (
        UniqueConstraint('project_id', 'user_uid', name='idx_proyecto_usuario_unico'),
    )
