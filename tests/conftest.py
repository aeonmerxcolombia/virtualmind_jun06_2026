import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.db import Base, get_db
from app.auth.hashing import Hash
from app.auth.jwt_handler import create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    return TestClient(app)


@pytest.fixture
def test_role(db):
    from app.models.role import Role

    role = Role(id=1, name="superadmin", description="Super Admin")
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@pytest.fixture
def test_role_abogado(db):
    from app.models.role import Role

    role = Role(id=2, name="abogado", description="Abogado")
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@pytest.fixture
def test_user(db, test_role):
    from app.models.user import User

    user = User(
        uid="test-uid-123",
        nombre="Test User",
        tipo_documento="CC",
        documento="123456789",
        email="test@example.com",
        password=Hash.encrypt("testpass123"),
        estado=True,
    )
    user.roles.append(test_role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user_2(db, test_role_abogado):
    from app.models.user import User

    user = User(
        uid="test-uid-456",
        nombre="Test User 2",
        tipo_documento="CC",
        documento="987654321",
        email="test2@example.com",
        password=Hash.encrypt("testpass456"),
        estado=True,
    )
    user.roles.append(test_role_abogado)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_project(db, test_user):
    from app.models.project import Project

    project = Project(
        name="Proyecto Test",
        client_id=test_user.uid,
        codigo_referencia="PRY-001",
        estado="activo",
        description="Proyecto de prueba",
        tipo_proyecto="curso_virtual",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def test_fase(db, test_project):
    from app.models.fase import Fase

    fase = Fase(nombre="Fase Test", project_id=test_project.id, orden=1)
    db.add(fase)
    db.commit()
    db.refresh(fase)
    return fase


@pytest.fixture
def test_etapa(db, test_fase):
    from app.models.etapa import Etapa

    etapa = Etapa(nombre="Etapa Test", fase_id=test_fase.id, orden=1)
    db.add(etapa)
    db.commit()
    db.refresh(etapa)
    return etapa


@pytest.fixture
def test_tarea(db, test_etapa, test_user):
    from app.models.tarea import Tarea

    tarea = Tarea(
        titulo="Tarea Test",
        descripcion="Descripción de prueba",
        etapa_id=test_etapa.id,
        asignado_a=test_user.uid,
        estado="pendiente",
    )
    db.add(tarea)
    db.commit()
    db.refresh(tarea)
    return tarea


@pytest.fixture
def test_permission(db):
    from app.models.permission import Permission

    perm = Permission(name="users.read", description="Leer usuarios")
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return perm


@pytest.fixture
def auth_token(test_user):
    return create_access_token(
        {"user_id": test_user.uid, "email": test_user.email, "roles": ["superadmin"]}
    )


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def auth_headers_abogado(test_user_2):
    token = create_access_token(
        {"user_id": test_user_2.uid, "email": test_user_2.email, "roles": ["abogado"]}
    )
    return {"Authorization": f"Bearer {token}"}
