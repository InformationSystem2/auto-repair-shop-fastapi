import uuid
from datetime import datetime

from sqlalchemy import (
    UUID, Boolean, Column, DateTime, ForeignKey, 
    Numeric, String, Table, func, text, Integer
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.module_users.models.models import User

# Tabla asociativa para relación Muchos a Muchos entre Workshop y Specialty
specialty_workshop = Table(
    "specialty_workshop",
    Base.metadata,
    Column("workshop_id", UUID(as_uuid=True), ForeignKey("workshops.id", ondelete="CASCADE"), primary_key=True),
    Column("specialty_id", UUID(as_uuid=True), ForeignKey("specialties.id", ondelete="CASCADE"), primary_key=True),
)

class Specialty(Base):
    __tablename__ = "specialties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True) # TEXT
    
    # Relaciones
    workshops: Mapped[list["Workshop"]] = relationship(
        "Workshop", secondary=specialty_workshop, back_populates="specialties"
    )

class Workshop(Base):
    __tablename__ = "workshops"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ruc_nit: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False) # TEXT
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(11, 8), nullable=True)
    
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("TRUE"))
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("FALSE"))
    commission_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=10.0)
    rating_avg: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True, default=0.0)
    total_services: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relaciones
    specialties: Mapped[list["Specialty"]] = relationship(
        "Specialty", secondary=specialty_workshop, back_populates="workshops"
    )
    technicians: Mapped[list["Technician"]] = relationship("Technician", back_populates="workshop")


class Technician(User):
    __tablename__ = "technicians"

    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("TRUE"))
    current_latitude: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    current_longitude: Mapped[float | None] = mapped_column(Numeric(11, 8), nullable=True)
    
    workshop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workshops.id", ondelete="CASCADE"), nullable=False)
    
    __mapper_args__ = {
        "polymorphic_identity": "technician",
    }

    # Relaciones
    workshop: Mapped["Workshop"] = relationship("Workshop", back_populates="technicians")
