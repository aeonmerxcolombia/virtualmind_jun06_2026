# app/models/module.py

from sqlalchemy import Column, BigInteger, String, Text, DateTime, Boolean, ForeignKey, DECIMAL, Integer
from sqlalchemy.orm import relationship
from app.database.db import Base
from datetime import datetime

class Module(Base):
    __tablename__ = "modules"

    # Campos de control principales
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    study_plan_id = Column(BigInteger, ForeignKey("study_plans.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.now)
    ultima_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    notas_adicionales = Column(Text)

    # A. Identificación
    nombre_del_modulo = Column(String(255))
    nombre_corto_del_modulo = Column(String(100))
    codigo_id_del_modulo = Column(String(50))
    version = Column(String(50))
    palabras_clave = Column(Text)
    autor_responsable = Column(String(255))
    derechos_patrimoniales = Column(Boolean)
    derechos_intelectuales = Column(Boolean)
    organizacion_institucion = Column(String(255))

    # B. Objetivos y alcance
    objetivo_general = Column(Text)
    objetivos_especificos = Column(Text)
    publico_objetivo = Column(String(255))
    duracion_estimada = Column(String(50))
    requisitos_previos = Column(Text)
    criterios_de_logro = Column(Text)

    # C. Estructura de contenidos
    numero_unidades = Column(Integer)
    lista_unidades_temas = Column(Text)
    orden_unidades = Column(String(50))
    tiempo_estimado_por_unidad = Column(String(50))

    # D. Diseño visual y marca
    tipo_letra = Column(String(100))
    tamano_letra = Column(String(50))
    estilos_texto = Column(String(100))
    colores_principales = Column(String(255))
    logotipo = Column(String(50))
    
    # E. Portada
    tiene_portada = Column(Boolean)
    tipo_portada = Column(String(50))
    creditos_en_portada = Column(Boolean)
    texto_de_portada = Column(Text)

    # F. Recursos multimedia
    infografias_estaticas = Column(Integer)
    infografias_animadas = Column(Integer)
    imagenes = Column(Integer)
    videos = Column(Text)
    microvideos_cortos = Column(Boolean)
    audios = Column(Text)
    animaciones = Column(Integer)
    storytelling = Column(Boolean)
    presentaciones_interactivas = Column(Boolean)
    portada_animada = Column(Boolean)
    gamificacion = Column(Boolean)
    simulaciones = Column(Boolean)
    realidad_aumentada = Column(Boolean)
    lineas_tiempo_interactivas = Column(Boolean)
    mapas_interactivos = Column(Boolean)
    galerias_imagenes = Column(Boolean)
    elementos_descargables = Column(Text)
    otros_recursos = Column(Text)

    # G. Actividades e interactividad
    actividades_aprendizaje_unidad = Column(Text)
    actividades_cierre_modulo = Column(Text)
    tipos_actividades = Column(Text)
    materiales_descargables = Column(Text)
    
    # H. Evaluación
    tipos_preguntas = Column(Text)
    numero_total_preguntas = Column(Integer)
    nota_minima_aprobacion = Column(DECIMAL(5, 2))
    intentos_permitidos = Column(Integer)
    tiempo_limite = Column(Text)
    retroalimentacion = Column(Text)

    # I. Accesibilidad e inclusión
    subtitulos_videos = Column(Boolean)
    transcripciones_audio = Column(Boolean)
    navegacion_teclado = Column(Boolean)
    lectura_pantalla_compatible = Column(Boolean)
    idiomas_disponibles = Column(Text)

    # J. Entrega y uso
    plataforma_destino = Column(String(255))
    dispositivos_objetivo = Column(Text)
    modo_uso = Column(String(50))
    tamano_aproximado = Column(String(50))
    entrega_fuentes = Column(Boolean)
    entrega_scorm = Column(Boolean)
    entrega_multimedia = Column(Boolean)
    entrega_version_pdf = Column(Boolean)
    
    # Relaciones con StudyPlan y Unit
    study_plan = relationship("StudyPlan", back_populates="modules")
    units = relationship("Unit", back_populates="module", cascade="all, delete-orphan")
