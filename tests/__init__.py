import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.db import Base, get_db
from app.models.user import User
from app.models.role import Role
from app.auth.jwt_handler import create_access_token as createJWT


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
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
    role = Role(id=1, name="superadmin", description="Super Admin")
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@pytest.fixture
def test_user(db, test_role):
    from app.auth.hashing import Hash
    user = User(
        uid="test-uid-123",
        nombre="Test User",
        tipo_documento="CC",
        documento="123456789",
        email="test@example.com",
        password=Hash.encrypt("testpass123"),
        estado=True
    )
    user.roles.append(test_role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    return createJWT({"user_id": test_user.uid, "email": test_user.email, "roles": ["superadmin"]})


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
