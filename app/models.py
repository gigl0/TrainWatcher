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
    trains: Mapped[list["TrainStatus"]] = relationship(back_populates="route", cascade="all, delete")

class TrainStatus(Base):
    __tablename__ = "trains"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"))
    train_code: Mapped[str] = mapped_column(String(20))
    last_status: Mapped[str] = mapped_column(String(40))  # InOrario/Ritardo/Cancellato
    delay_minutes: Mapped[int] = mapped_column(Integer, default=0)
    last_update: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    route: Mapped["Route"] = relationship(back_populates="trains")

class NotificationLog(Base):
    __tablename__ = "notifications_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"))
    train_code: Mapped[str] = mapped_column(String(20))
    event_type: Mapped[str] = mapped_column(String(30))  # ritardo/cancellazione/ripristino
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
