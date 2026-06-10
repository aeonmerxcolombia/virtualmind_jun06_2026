from sqlalchemy import Column, String, Integer, LargeBinary, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database.db import Base

class WebAuthnCredential(Base):
    __tablename__ = "webauthn_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_uid: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    credential_id: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, default=0)
    device_name: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
