from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, ForeignKey, Text, DateTime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    firebase_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    routes: Mapped[list["Route"]] = relationship(back_populates="user", cascade="all, delete")

class Route(Base):
    __tablename__ = "routes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    departure_name: Mapped[str] = mapped_column(String(120))
    arrival_name: Mapped[str] = mapped_column(String(120))
    departure_code: Mapped[str] = mapped_column(String(20))
    arrival_code: Mapped[str] = mapped_column(String(20))
    train_number: Mapped[str | None] = mapped_column(String(20), nullable=True)  # opzionale
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="routes")
    trains: Mapped[list["Train"]] = relationship(back_populates="route", cascade="all, delete")

class Train(Base):
    __tablename__ = "trains"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"))
    train_code: Mapped[str] = mapped_column(String(20))
    last_status: Mapped[str] = mapped_column(String(40))  # InOrario/Ritardo/Cancellato
    delay_minutes: Mapped[int] = mapped_column(Integer, default=0)
    last_update: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    route: Mapped["Route"] = relationship(back_populates="trains")

# app/models.py

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"))
    train_code: Mapped[str]
    event_type: Mapped[str]
    sent_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)

