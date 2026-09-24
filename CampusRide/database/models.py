import enum
from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class RideStatus(enum.Enum):
    OPEN = "OPEN"
    FULL = "FULL"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)  # Telegram ID
    username = Column(String(64), nullable=True)
    full_name = Column(String(128), nullable=False)
    room_number = Column(String(32), nullable=False)
    sbp_phone = Column(String(32), nullable=False)
    sbp_bank = Column(String(64), nullable=False)
    rating = Column(Float, default=5.0)

    hosted_rides = relationship(
        "RideLobby", back_populates="host", cascade="all, delete-orphan"
    )
    passengers = relationship(
        "Passenger", back_populates="user", cascade="all, delete-orphan"
    )


class RideLobby(Base):
    __tablename__ = "ride_lobbies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    from_location = Column(String(256), nullable=False)
    to_location = Column(String(256), nullable=False)
    meeting_point = Column(String(256), nullable=False)
    departure_time = Column(String(64), nullable=False)
    max_seats = Column(Integer, default=3)
    status = Column(Enum(RideStatus), default=RideStatus.OPEN, nullable=False)
    total_cost = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    host = relationship("User", back_populates="hosted_rides")
    passengers = relationship(
        "Passenger", back_populates="lobby", cascade="all, delete-orphan"
    )


class Passenger(Base):
    __tablename__ = "passengers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lobby_id = Column(Integer, ForeignKey("ride_lobbies.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    is_paid = Column(Integer, default=0)  # 0: Not paid, 1: Sent, 2: Confirmed

    lobby = relationship("RideLobby", back_populates="passengers")
    user = relationship("User", back_populates="passengers")