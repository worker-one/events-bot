import logging
from pathlib import Path
from typing import Any, Dict

from omegaconf import OmegaConf
from telebot import TeleBot, types

from .markup import create_events_list_markup
from .service import read_event, read_events

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings


def register_handlers(bot: TeleBot) -> None:
    """
    Register all event-related handlers for the bot.

    Args:
        bot: The Telegram bot instance to register handlers for
    """
    logger.info("Registering event handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "events")
    def events_list(call: types.CallbackQuery, data: Dict[str, Any]) -> None:
        """
        Handle the events list callback.

        Args:
            call: The callback query
            data: The data dictionary containing user and state information
        """
        user = data["user"]
        db_session = data["db_session"]
        events = read_events(db_session)

        markup = create_events_list_markup(user.lang, events)

        bot.edit_message_text(
            chat_id=user.id,
            message_id=call.message.message_id,
            text=strings[user.lang].events_list,
            reply_markup=markup,
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("event_"))
    def event_details(call: types.CallbackQuery, data: Dict[str, Any]) -> None:
        """
        Show details of a specific event.

        Args:
            call: The callback query with event ID embedded in data
            data: The data dictionary containing user and database session
        """
        user = data["user"]
        db_session = data["db_session"]

        # Extract event ID and fetch the event
        event_id = int(call.data.split("_")[1])
        event = read_event(db_session, event_id)

        if not event:
            bot.send_message(
                user.id,
                strings[user.lang].event_not_found,
            )
            return

        # Format event details message
        message_text = strings[user.lang].event_details.format(
            name=event.name,
            description=event.description,
            qtickets_link=event.qtickets_link,
        )

        bot.edit_message_text(
            chat_id=user.id,
            message_id=call.message.message_id,
            text=message_text,
            parse_mode="Markdown",
        )
