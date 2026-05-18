import enum
import re

from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import Column, String, Enum

from config import Base


class Status(enum.Enum):
    active = "active"
    inactive = "inactive"
    pending = "pending"


class SuperAdmin(Base):
    __tablename__ = "super_admins"

    id = Column(String, unique=True, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), nullable=False, index=False)
    password = Column(String(255), nullable=False, index=False)
    status = Column(Enum(Status), nullable=False, default=Status.pending)


class AdminAdd(BaseModel):
    email: EmailStr
    name: str
    password: str
    status: Status

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:

        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one number")

        if not re.search(r"[^\w\s]", value):
            raise ValueError("Password must contain at least one symbol")

        return value
