from __future__ import annotations

from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RadarScan(Base):
    __tablename__ = "radar_scans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    station: Mapped[str] = mapped_column(String(4), nullable=False)
    scan_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_key: Mapped[str] = mapped_column(Text, nullable=False)
    bio_gate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class BioGate(Base):
    __tablename__ = "bio_gates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    scan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("radar_scans.id", ondelete="CASCADE"), nullable=False
    )
    reflectivity: Mapped[float] = mapped_column(Float, nullable=False)
    zdr: Mapped[float] = mapped_column(Float, nullable=False)
    rhohv: Mapped[float] = mapped_column(Float, nullable=False)
    geom: Mapped[object] = mapped_column(Geometry("POLYGON", srid=4326), nullable=False)


class RoostCentroid(Base):
    __tablename__ = "roost_centroids"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    scan_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("radar_scans.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    geom: Mapped[object] = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
