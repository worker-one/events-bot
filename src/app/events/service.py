import logging
from datetime import datetime

from sqlalchemy.orm import Session

from .models import Event

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def read_event(db_session: Session, event_id: int):
    """Get an event by ID"""
    return db_session.query(Event).filter(Event.id == event_id).first()


def read_events(db_session: Session, skip: int = 0, limit: int = 10):
    """Get all events"""
    return db_session.query(Event).offset(skip).limit(limit).all()


def create_event(db_session: Session, event_data: dict) -> Event:
    """Create a new event"""
    new_event = Event(
        name=event_data["name"],
        description=event_data.get("description"),
        image=event_data.get("image_url"),
        qtickets_link=event_data.get("qtickets_link"),
        datetime=event_data.get("datetime"),
    )
    db_session.add(new_event)
    db_session.commit()
    db_session.refresh(new_event)
    logger.info(f"Event created: {new_event.name}")
    return new_event


def remove_event(db_session: Session, event_id: int) -> bool:
    """Remove an event by ID. Returns True if deleted, False if not found."""
    event = db_session.query(Event).filter(Event.id == event_id).first()
    if event:
        db_session.delete(event)
        db_session.commit()
        logger.info(f"Event removed: {event.name}")
        return True
    return False