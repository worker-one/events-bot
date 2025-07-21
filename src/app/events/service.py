import logging

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
