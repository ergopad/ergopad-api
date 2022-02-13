from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func

from db.session import Base

# USER MODEL


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)


class JWTBlackList(Base):
    __tablename__ = "jwtBlacklist"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
