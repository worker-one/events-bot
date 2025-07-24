import logging
from pathlib import Path
from typing import Any, Dict

from omegaconf import OmegaConf
from telebot import TeleBot, types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from .markup import create_events_list_markup
from .service import read_event, read_events, remove_event
from .scheduler import schedule_message

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

    @bot.message_handler(commands=["start"])
    def events_list(message: types.Message, data: Dict[str, Any]) -> None:
        """
        Handle the events list command.

        Args:
            call: The callback query
            data: The data dictionary containing user and state information
        """
        user = data["user"]
        db_session = data["db_session"]
        events = read_events(db_session)

        markup = create_events_list_markup(user.lang, events)
        # Add "Обратная связь" button
        markup.add(InlineKeyboardButton("Обратная связь", callback_data="contact"))

        bot.send_message(
            user.id,
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
            description=event.description
        )
        
        print("event.qtickets_link:", event.qtickets_link)
        
        inline_keyboard_markup = InlineKeyboardMarkup()
        inline_keyboard_markup.row(
            InlineKeyboardButton(
                strings[user.lang].sign_up,
                url=event.qtickets_link
            )
        )

        # If event has an image, send it first, then send details as a message
        if event.image:
            bot.send_photo(
                user.id,
                event.image,
                caption=message_text,
                parse_mode="Markdown",
                reply_markup=inline_keyboard_markup,
            )
        else:
            bot.edit_message_text(
                chat_id=user.id,
                message_id=call.message.message_id,
                text=message_text,
                parse_mode="Markdown",
                reply_markup=inline_keyboard_markup,
            )

        # Schedule message about email confirmation in 90 seconds
        schedule_message(
            bot,
            90,
            user.id,
            strings[user.lang].email_confirmation
        )

        # Schedule message about checking spam in 5 minutes (300 seconds)
        schedule_message(
            bot,
            300,
            user.id,
            strings[user.lang].check_spam
        )
