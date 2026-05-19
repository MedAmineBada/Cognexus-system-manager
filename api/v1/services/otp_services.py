import datetime
from uuid import uuid4

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.models import OTPRequest, SuperAdmin, OTP, PasswordChangeRequest, Email
from api.v1.utils import NotFoundException, AppException
from api.v1.utils.email_utils import push_email
from api.v1.utils.password_helpers import (
    generate_secure_alphanumeric,
    hash_password,
    verify_password,
)


async def request_otp(r: OTPRequest, session: AsyncSession):
    query = await session.execute(select(SuperAdmin).where(SuperAdmin.email == r.email))
    user = query.scalars().first()

    if not user:
        raise NotFoundException("User not found")

    otp_code = generate_secure_alphanumeric()

    try:
        mail = Email(
            title="Your password reset code",
            content=f"This is your password reset code: {otp_code}, please do not share it with anyone, Note: This code expires in 10 minutes.",
            email=r.email,
        )
        await push_email(mail)
    except:
        raise AppException("Failed to send email")

    now = datetime.datetime.now()
    now = now.replace(microsecond=0, second=0)

    try:
        stmt = delete(OTP).where(OTP.user_id == user.id, OTP.used == False)
        await session.execute(stmt)
        await session.commit()

        new_otp: OTP = OTP(
            id=str(uuid4()),
            user_id=user.id,
            code=hash_password(otp_code),
            issued_at=now,
            expires_at=now + datetime.timedelta(minutes=10),
            used=False,
        )

        session.add(new_otp)
        await session.commit()
    except Exception as e:
        print(e)
        raise AppException("Failed to save OTP to db")

    return {"success": "OTP sent"}


async def change_password(r: PasswordChangeRequest, session: AsyncSession):
    query = await session.execute(select(SuperAdmin).where(SuperAdmin.email == r.email))
    user = query.scalars().first()

    if not user:
        raise NotFoundException("User not found")

    query = await session.execute(
        select(OTP).where(OTP.user_id == user.id, OTP.used == False)
    )
    otp = query.scalars().first()
    if not otp:
        raise NotFoundException("OTP request not found")

    if otp.expires_at < datetime.datetime.now():
        raise AppException("OTP expired")

    if not verify_password(r.otp_code, otp.code):
        raise AppException("Invalid OTP")

    user.password = hash_password(r.new_password)
    otp.used = True
    await session.commit()

    return {"success": "password changed"}
