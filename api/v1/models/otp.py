import re

from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime

from config import Base


class OTP(Base):
    __tablename__ = "otp"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("super_admins.id"), nullable=False, index=True)
    code = Column(String, nullable=False)
    issued_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)


class OTPRequest(BaseModel):
    email: EmailStr


class PasswordChangeRequest(BaseModel):
    email: EmailStr
    new_password: str
    otp_code: str

    @field_validator("new_password")
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
