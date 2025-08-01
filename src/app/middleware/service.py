import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from .models import LogEvent

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_event(
    db_session: Session,
    user_id: str,
    content_type: str,
    content: str,
    event_type: str,
    state: Optional[str] = None,
) -> LogEvent:
    """Create an event for a user."""
    event = LogEvent(
        user_id=user_id,
        content_type=content_type,
        content=content,
        state=state,
        event_type=event_type,
    )
    db_session.expire_on_commit = False
    db_session.add(event)
    db_session.commit()
    db_session.close()
    return event


def read_event(db_session: Session, event_id: int) -> Optional[LogEvent]:
    """Read an event by ID."""
    try:
        return db_session.query(LogEvent).filter(LogEvent.id == event_id).first()
    finally:
        db_session.close()


def read_events_by_user(db_session: Session, user_id: str) -> list[LogEvent]:
    """Read all events for a user."""
    try:
        return db_session.query(LogEvent).filter(LogEvent.user_id == user_id).all()
    finally:
        db_session.close()