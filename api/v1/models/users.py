from sqlalchemy import Column, String, Boolean

from config import Base


class SuperAdmin(Base):
    __tablename__ = "super_admins"

    id = Column(String, unique=True, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), nullable=False, index=False)
    password = Column(String(255), nullable=False, index=False)
    active = Column(Boolean, nullable=False, default=False)
