# app/models/author_content_form.py
from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base

class AuthorContentForm(Base):
    __tablename__ = "author_content_forms"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False)

    # Campos base del formulario (alineados a tu formato)
    course_name = Column(String(255), nullable=False)   # nombre del curso/prog
    module_name = Column(String(255))                   # módulo
    author_name = Column(String(255))                   # autor

    derechos_patrimoniales = Column(Boolean, default=False)
    derechos_intelectuales = Column(Boolean, default=False)

    publico_objetivo = Column(Text)
    horas_curso = Column(Integer)
    horas_estudio_autonomo = Column(Integer)    # “Estudio autónomo”
    horas_estudio_asincronico = Column(Integer) # “Estudio asincrónico”

    # Bloques del formulario en JSON
    indice_estructura = Column(JSON)        # índice preliminar, unidades/subtemas/orden, tiempos, páginas
    objetivos = Column(JSON)                # obj gral/esp curso, obj módulo/unidad, resultados aprendizaje
    contenido_escrito = Column(JSON)        # presentación, introducción, desarrollo, glosario preliminar, preguntas
    narracion = Column(JSON)                # voz en off (sí/no/género), persona (1ra/2da/3ra/omnisciente/testigo)
    estilo_narrativo = Column(JSON)         # expositivo, descriptivo, dialogado, testimonial, metafórico, gamificado…
    recursos_multimedia = Column(JSON)      # tipos + formatos + duraciones + cantidades
    actividades_aprendizaje = Column(JSON)  # diagnóstico/modulares/unidad/cierre + instrucciones/materiales
    evaluacion = Column(JSON)               # tipos, banco, respuestas, nota mínima, intentos, tiempo, retro
    accesibilidad = Column(JSON)            # subtítulos, alt-text, teclado, transcripciones, etc.
    referencias = Column(Text)              # bibliografía y créditos
    glosario = Column(JSON)                 # [{termino, definicion, ejemplo?}, ...]

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 🔗 Relación padre
    project = relationship("Project", back_populates="author_content_forms")

