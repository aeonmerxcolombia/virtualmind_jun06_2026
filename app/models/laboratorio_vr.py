from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base

class LaboratorioVR(Base):
    __tablename__ = 'laboratorios_vr'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    categoria = Column(String(50), default='general')
    modelo_3d = Column(String(100))
    escenario = Column(String(100), default='laboratorio')
    contenido = Column(JSON)
    estado = Column(String(20), default='activo')
    usuario_creacion = Column(Integer)
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
    
    experimentos = relationship('ExperimentoVR', back_populates='laboratorio')

class ModeloVR(Base):
    __tablename__ = 'modelos_vr'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    categoria = Column(String(50))
    tipo = Column(String(50), default='primitive')
    archivo = Column(String(255))
    geometry_data = Column(JSON)
    material_data = Column(JSON)
    posicion = Column(String(50), default='0 1.5 -2')
    rotacion = Column(String(50), default='0 0 0')
    escala = Column(String(50), default='1 1 1')
    animacion = Column(JSON)
    estado = Column(String(20), default='activo')
    usuario_creacion = Column(Integer)
    fecha_creacion = Column(DateTime, default=func.now())

class ExperimentoVR(Base):
    __tablename__ = 'experimentos_vr'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    laboratorio_id = Column(Integer, ForeignKey('laboratorios_vr.id'))
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    pasos = Column(JSON, nullable=False)
    modelos_requeridos = Column(JSON)
    evaluacion = Column(JSON)
    duracion_estimada = Column(Integer, default=30)
    dificultad = Column(String(20), default='basico')
    estado = Column(String(20), default='activo')
    fecha_creacion = Column(DateTime, default=func.now())
    
    laboratorio = relationship('LaboratorioVR', back_populates='experimentos')

class SesionVR(Base):
    __tablename__ = 'sesiones_vr'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, nullable=False)
    laboratorio_id = Column(Integer)
    experimento_id = Column(Integer)
    modelo_id = Column(Integer)
    respuesta = Column(Text)
    duracion = Column(Integer, default=0)
    resultado = Column(JSON)
    completado = Column(Boolean, default=False)
    fecha_inicio = Column(DateTime, default=func.now())
    fecha_fin = Column(DateTime)