from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from ..models import Base

users_events = Table(
    "users_events",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("event_id", Integer, ForeignKey("events.id")),
)


class Event(Base):
    """Event model"""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    qtickets_link = Column(String, nullable=True)

    users = relationship("User", secondary=users_events, back_populates="events")
