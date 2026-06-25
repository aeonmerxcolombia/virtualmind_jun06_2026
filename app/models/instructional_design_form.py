# app/models/instructional_design_form.py
from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base

class InstructionalDesignForm(Base):
    __tablename__ = "instructional_design_forms"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False)

    course_name = Column(String(255), nullable=False)
    module_name = Column(String(255))
    unit_name = Column(String(255))

    objetivo_instruccional = Column(Text)
    mensaje_clave = Column(Text)

    persona_narrativa = Column(JSON)        # selección/combinación de persona
    narrador_estilo = Column(JSON)          # estilos narrativos

    texto_pantalla_inicio = Column(Boolean, default=False)
    voz_en_off = Column(Boolean, default=False)

    recursos_visuales = Column(JSON)        # sugeridos autor/productor
    recursos_multimedia = Column(JSON)      # instrucciones técnicas y tipos
    interacciones = Column(JSON)            # [clic, drag&drop, hotspot, timeline, H5P, ...]
    actividades_aprendizaje = Column(JSON)  # por módulo/unidad/cierre

    feedback = Column(Text)
    evaluacion = Column(JSON)
    accesibilidad = Column(JSON)

    notas_productor = Column(Text)
    observaciones = Column(Text)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 🔗 Relación padre
    project = relationship("Project", back_populates="instructional_design_forms")

