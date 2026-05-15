from pydantic import BaseModel, EmailStr


class Email(BaseModel):
    title: str
    content: str
    email: EmailStr
