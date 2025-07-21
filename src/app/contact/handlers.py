import logging
from pathlib import Path
from typing import Any, Dict

from omegaconf import OmegaConf
from telebot import TeleBot, types

from ..auth.service import read_users

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings


def register_handlers(bot: TeleBot) -> None:
    """
    Register all contact-related handlers for the bot.

    Args:
        bot: The Telegram bot instance to register handlers for
    """
    logger.info("Registering contact handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "contact")
    def contact(call: types.CallbackQuery, data: Dict[str, Any]) -> None:
        """
        Handle the contact callback.

        Args:
            call: The callback query
            data: The data dictionary containing user and state information
        """
        user = data["user"]

        bot.edit_message_text(
            chat_id=user.id,
            message_id=call.message.message_id,
            text=strings[user.lang].enter_message,
        )
        bot.register_next_step_handler(call.message, process_message, bot, data)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reply_"))
    def handle_reply(call: types.CallbackQuery, data: Dict[str, Any]) -> None:
        """
        Handle admin reply to user feedback.

        Args:
            call: The callback query
            data: The data dictionary containing user and state information
        """
        admin = data["user"]
        original_user_id = int(call.data.split("_")[1])

        bot.edit_message_text(
            chat_id=admin.id,
            message_id=call.message.message_id,
            text=strings[admin.lang].enter_reply,
        )
        bot.register_next_step_handler(
            call.message, process_admin_reply, bot, data, original_user_id
        )


def process_message(message: types.Message, bot: TeleBot, data: Dict[str, Any]):
    """
    Process the message from the user and send it to admins.
    """
    user = data["user"]
    db_session = data["db_session"]
    admins = read_users(db_session, role_id=1) + read_users(db_session, role_id=0)

    feedback_message = strings[user.lang].feedback_template.format(
        username=user.username, text=message.text
    )

    # Create reply button
    markup = types.InlineKeyboardMarkup()
    reply_button = types.InlineKeyboardButton(
        text="Reply", callback_data=f"reply_{user.id}"
    )
    markup.add(reply_button)

    for admin in admins:
        bot.send_message(admin.id, feedback_message, reply_markup=markup)

    bot.send_message(user.id, strings[user.lang].message_sent)


def process_admin_reply(
    message: types.Message, bot: TeleBot, data: Dict[str, Any], original_user_id: int
):
    """
    Process the reply from admin and send it to the original user.

    Args:
        message: The admin's reply message
        bot: The Telegram bot instance
        data: The data dictionary containing admin and state information
        original_user_id: The ID of the user who sent the original feedback
    """
    admin = data["user"]
    db_session = data["db_session"]

    # Get the original user to determine their language
    original_user = (
        read_users(db_session, ids=[original_user_id])[0]
        if read_users(db_session, ids=[original_user_id])
        else None
    )

    if original_user:
        reply_message = strings[original_user.lang].admin_reply_template.format(
            admin_username=admin.username or "Admin", reply_text=message.text
        )
        bot.send_message(original_user_id, reply_message)
        bot.send_message(admin.id, strings[admin.lang].reply_sent)
    else:
        bot.send_message(admin.id, strings[admin.lang].user_not_found)
