import enum

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
