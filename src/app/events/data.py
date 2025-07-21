from .models import Event
from sqlalchemy.orm import Session

def init_events_table(db_session: Session):
    events_data = [
        {
            "id": 1,
            "name": "Tech Conference 2025",
            "description": "An annual conference for tech enthusiasts.",
            "qtickets_link": "https://example.com/tech-conference-2025",
        },
        {
            "id": 2,
            "name": "Music Festival 2025",
            "description": "A weekend of live music from various artists.",
            "qtickets_link": "https://example.com/music-festival-2025",
        },
    ]

    for event_data in events_data:
        event = Event(**event_data)
        db_session.add(event)

    db_session.commit()
