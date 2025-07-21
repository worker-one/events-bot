import logging
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from .models import Event

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_events_list_markup(lang: str, events: list[Event]) -> InlineKeyboardMarkup:
    """Create the events menu markup"""
    markup = InlineKeyboardMarkup()
    for event in events:
        markup.add(
            InlineKeyboardButton(event.name, callback_data=f"event_{event.id}")
        )
    return markup
