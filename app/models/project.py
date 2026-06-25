from sqlalchemy import (
    Column, BigInteger, String, Date, Text, DECIMAL, Boolean, DateTime, ForeignKey, func
)
from app.database.db import Base
from sqlalchemy.orm import relationship


class Project(Base):
    __tablename__ = "projects"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Nueva relación con Fase
    fase_id = Column(BigInteger, ForeignKey("fases.id"), nullable=True)
    fase = relationship("Fase", back_populates="proyectos")
    name = Column(String(255), nullable=False)
    client_id = Column(String(255), ForeignKey("usuarios.uid"), nullable=False)
    codigo_referencia = Column(String(100))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    tipo_proyecto = Column(String(50))
    tipo_proyecto_personalizado = Column(String(100))
    estado = Column(String(50), default="Planificado")
    description = Column(Text)

    lenguaje_incluyente = Column(Boolean, default=False)
    lenguaje_inclusivo_tipo = Column(String(50))
    lenguaje_inclusivo_otro = Column(String(100))

    inclusion_digital = Column(Boolean, default=False)
    inclusion_digital_web = Column(Boolean, default=False)
    inclusion_digital_asistiva = Column(Boolean, default=False)
    inclusion_digital_universal = Column(Boolean, default=False)
    inclusion_digital_educativa = Column(Boolean, default=False)
    inclusion_digital_otro = Column(String(100))

    idioma = Column(String(100))
    idioma_otro = Column(String(100))

    # Tipografía - Título
    tipografia_titulo_fuente = Column(String(100))
    tipografia_titulo_tamano = Column(String(20))
    tipografia_titulo_negrita = Column(Boolean, default=False)
    tipografia_titulo_cursiva = Column(Boolean, default=False)

    # Tipografía - Subtítulo
    tipografia_subtitulo_fuente = Column(String(100))
    tipografia_subtitulo_tamano = Column(String(20))
    tipografia_subtitulo_negrita = Column(Boolean, default=False)
    tipografia_subtitulo_cursiva = Column(Boolean, default=False)

    # Tipografía - Párrafo
    tipografia_parrafo_fuente = Column(String(100))
    tipografia_parrafo_tamano = Column(String(20))
    tipografia_parrafo_negrita = Column(Boolean, default=False)
    tipografia_parrafo_cursiva = Column(Boolean, default=False)

    horas_curso = Column(DECIMAL(7, 2))

    diseno_grafico_tipo = Column(String(50))
    diseno_grafico_paleta = Column(String(120))

    cesion_derechos = Column(Boolean, default=False)
    derechos_patrimoniales_autor = Column(Boolean, default=False)
    acuerdo_confidencialidad = Column(Boolean, default=False)
    entrega_fuentes = Column(Boolean, default=False)
    entrega_escrito_autor = Column(Boolean, default=False)
    entrega_diseno_instruccional = Column(Boolean, default=False)

    publico_objetivo = Column(Text)
    publico_objetivo_otro = Column(String(255))

    horas_aprendizaje_autonomo_virtual = Column(DECIMAL(7, 2))
    horas_actividades_aprendizaje = Column(DECIMAL(7, 2))
    observaciones = Column(Text)

    ultima_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())

    etapa = Column(String(255), nullable=True)

    documents = relationship("Document", back_populates="project")
    cronograma = relationship("Cronograma", back_populates="project", uselist=False, cascade="all, delete-orphan")
    tareas = relationship("Tarea", back_populates="project")
    author_content_forms = relationship("AuthorContentForm", back_populates="project", cascade="all, delete-orphan")
    instructional_design_forms = relationship("InstructionalDesignForm", back_populates="project", cascade="all, delete-orphan" )
