import logging
import os
from pathlib import Path

import telebot
from dotenv import find_dotenv, load_dotenv
from omegaconf import OmegaConf
from telebot.states.sync.middleware import StateMiddleware

from .admin.handlers import register_handlers as admin_handlers
from .auth.data import init_roles_table, init_superuser
from .database.core import SessionLocal, create_tables, drop_tables
from .events.handlers import register_handlers as events_handlers
from .events.data import init_events_table
from .contact.handlers import register_handlers as contact_handlers
from .menu.handlers import register_handlers as menu_handlers
from .language.handler import register_handlers as language_handlers
from .middleware.antiflood import AntifloodMiddleware
from .middleware.database import DatabaseMiddleware
from .middleware.user import UserCallbackMiddleware, UserMessageMiddleware
from .public_message.handlers import register_handlers as public_message_handlers
from .users.handlers import register_handlers as users_handlers
from src.health_check import start_health_check_server

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")

# Load and get environment variables
load_dotenv(find_dotenv(usecwd=True))
SUPERUSER_USERNAME = os.getenv("SUPERUSER_USERNAME")
SUPERUSER_USER_ID = os.getenv("SUPERUSER_USER_ID")


def start_bot():
    """Start the Telegram bot with configuration, middlewares, and handlers."""
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    if not BOT_TOKEN:
        logging.critical("BOT_TOKEN is not set in environment variables")
        raise ValueError("BOT_TOKEN environment variable is required")

    logger.info(f"Initializing {config.app.name} v{config.app.version}")

    try:
        bot = telebot.TeleBot(BOT_TOKEN, use_class_middlewares=True)
        _setup_middlewares(bot)
        _register_handlers(bot)
        bot.add_custom_filter(telebot.custom_filters.StateFilter(bot))

        bot_info = bot.get_me()
        logger.info(
            f"Bot {bot_info.username} (ID: {bot_info.id}) initialized successfully"
        )

        _start_polling_loop(bot)

    except Exception as e:
        logging.critical(f"Failed to start bot: {str(e)}")
        raise


def _setup_middlewares(bot):
    """Configure bot middlewares."""
    if config.app.antiflood.enabled:
        logger.info(
            f"Enabling antiflood (window: {config.app.antiflood.time_window_seconds}s)"
        )
        bot.setup_middleware(
            AntifloodMiddleware(bot, config.app.antiflood.time_window_seconds)
        )

    bot.setup_middleware(StateMiddleware(bot))
    bot.setup_middleware(DatabaseMiddleware(bot))
    bot.setup_middleware(UserMessageMiddleware(bot))
    bot.setup_middleware(UserCallbackMiddleware(bot))


def _register_handlers(bot):
    """Register all bot handlers."""
    handlers = [
        admin_handlers,
        menu_handlers,
        public_message_handlers,
        users_handlers,
        events_handlers,
        contact_handlers,
        language_handlers
    ]
    for handler in handlers:
        handler(bot)


def _start_polling_loop(bot):
    """Start the main bot polling loop with error handling."""
    logger.info("Starting bot polling...")
    bot.polling(none_stop=True, interval=0, timeout=60, long_polling_timeout=60)


def init_db():
    """Initialize the database for applications."""
    # Create tables
    create_tables()

    # Create a new database session directly using SessionLocal
    db_session = SessionLocal()

    init_roles_table(db_session)

    # Add admin to user table
    if SUPERUSER_USER_ID:
        init_superuser(db_session, SUPERUSER_USER_ID, SUPERUSER_USERNAME)
        logger.info(f"Superuser {SUPERUSER_USERNAME} added successfully.")

    init_events_table(db_session)

    db_session.close()

    logger.info("Database initialized")

def main():
    """Main entry point for the application."""
    # Start health check server
    start_health_check_server(port=8080)


if __name__ == "__main__":
    # drop_tables()
    # init_db()
    main()
    start_bot()

