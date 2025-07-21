import logging
import threading
from typing import Any, Dict

from telebot import TeleBot

logger = logging.getLogger(__name__)


def schedule_message(bot: TeleBot, delay_seconds: int, user_id: int, message: str) -> None:
    """
    Schedule a message to be sent after a specified delay.
    
    Args:
        bot: The Telegram bot instance
        delay_seconds: Delay in seconds before sending the message
        user_id: The user ID to send the message to
        message: The message text to send
    """
    def send_delayed_message():
        try:
            bot.send_message(user_id, message)
            logger.info(f"Scheduled message sent to user {user_id} after {delay_seconds} seconds")
        except Exception as e:
            logger.error(f"Failed to send scheduled message to user {user_id}: {e}")
    
    timer = threading.Timer(delay_seconds, send_delayed_message)
    timer.start()
    logger.info(f"Message scheduled for user {user_id} in {delay_seconds} seconds")
