"""Handler to show information about the application configuration."""
import logging
import os
from ast import Call
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from omegaconf import OmegaConf
from telebot.types import CallbackQuery, Message

from ..database.core import export_all_tables
from ..events.service import read_events, remove_event
from .markup import create_admin_menu_markup

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
app_strings = config.strings
global_config = OmegaConf.load("./src/app/config.yaml")


from telebot import types
from telebot.handler_backends import State, StatesGroup

from app.events.service import create_event
from .markup import create_cancel_button

class CreateEventState(StatesGroup):
    title = State()
    description = State()
    qtickets_link = State()
    datetime = State()
    image = State()


def register_handlers(bot):
    """Register about handlers"""
    logger.info("Registering `about` handlers")

    @bot.message_handler(commands=["admin"])
    def admin_menu_command(message: Message, data: dict):
        """Handler to show the admin menu."""
        user = data["user"]
        if user.role_id not in {0, 1}:
            # Inform the user that they do not have admin rights
            bot.send_message(message.from_user.id, app_strings[user.lang].no_rights)
            return

        # Send the admin menu
        bot.send_message(
            message.from_user.id,
            app_strings[user.lang].menu.title,
            reply_markup=create_admin_menu_markup(user.lang),
        )

    @bot.callback_query_handler(func=lambda call: call.data == "admin")
    def admin_menu_handler(call: CallbackQuery, data: dict):
        """Handler to show the admin menu."""
        user = data["user"]
        if user.role_id not in {0, 1}:
            # Inform the user that they do not have admin rights
            bot.send_message(
                call.message.from_user.id, app_strings[user.lang].no_rights
            )
            return

        # Edit message instead
        bot.edit_message_text(
            app_strings[user.lang].menu.title,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_admin_menu_markup(user.lang),
        )

    @bot.callback_query_handler(func=lambda call: call.data == "about")
    def about_handler(call: Call, data: dict):
        user_id = call.from_user.id

        app_config_str = OmegaConf.to_yaml(global_config.app)

        # Send config
        bot.send_message(user_id, f"```yaml\n{app_config_str}\n```", parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data == "export_data")
    def export_data_handler(call, data):
        user = data["user"]
        db_session = data["db_session"]
        # Export data
        export_dir = f'./data/{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.makedirs(export_dir)
        try:
            export_all_tables(db_session, export_dir)
            for table in config.db.tables:
                # save as excel in temp folder and send to a user
                filename = f"{export_dir}/{table}.csv"
                bot.send_document(user.id, open(filename, "rb"))
                # remove the file
                os.remove(filename)
        except Exception as e:
            bot.send_message(user.id, str(e))
            logger.error(f"Error exporting data: {e}")

    @bot.callback_query_handler(func=lambda call: call.data == "create_event")
    def create_event_start(call: types.CallbackQuery, data: dict):
        user = data["user"]
        if user.role_id not in {0, 1}:
            bot.send_message(call.message.chat.id, app_strings[user.lang].no_rights)
            return
        bot.send_message(
            user.id,
            app_strings[user.lang].create_event.title_prompt,
            reply_markup=create_cancel_button(user.lang),
        )
        data["state"].set(CreateEventState.title)

    @bot.message_handler(state=CreateEventState.title)
    def create_event_title(message: types.Message, data: dict):
        user = data["user"]
        if message.text.lower() == "cancel":
            bot.send_message(user.id, app_strings[user.lang].create_event.cancel)
            data["state"].reset()
            return
        data["state"].add_data(name=message.text)
        bot.send_message(
            user.id,
            app_strings[user.lang].create_event.description_prompt,
            reply_markup=create_cancel_button(user.lang),
        )
        data["state"].set(CreateEventState.description)

    @bot.message_handler(state=CreateEventState.description)
    def create_event_description(message: types.Message, data: dict):
        user = data["user"]
        if message.text.lower() == "cancel":
            bot.send_message(user.id, app_strings[user.lang].create_event.cancel)
            data["state"].reset()
            return
        data["state"].add_data(description=message.text)
        bot.send_message(
            user.id,
            app_strings[user.lang].create_event.qtickets_prompt,
            reply_markup=create_cancel_button(user.lang),
        )
        data["state"].set(CreateEventState.qtickets_link)

    @bot.message_handler(state=CreateEventState.qtickets_link)
    def create_event_qtickets(message: types.Message, data: dict):
        user = data["user"]
        if message.text.lower() == "cancel":
            bot.send_message(user.id, app_strings[user.lang].create_event.cancel)
            data["state"].reset()
            return
        qtickets_link = None if message.text.lower() == "skip" else message.text
        data["state"].add_data(qtickets_link=qtickets_link)
        bot.send_message(
            user.id,
            app_strings[user.lang].create_event.datetime_prompt,
            reply_markup=create_cancel_button(user.lang),
        )
        data["state"].set(CreateEventState.datetime)

    @bot.message_handler(state=CreateEventState.datetime)
    def create_event_datetime(message: types.Message, data: dict):
        user = data["user"]
        if message.text.lower() == "cancel":
            bot.send_message(user.id, app_strings[user.lang].create_event.cancel)
            data["state"].reset()
            return
        if message.text.lower() == "skip":
            event_datetime = None
        else:
            try:
                from datetime import datetime as dt
                event_datetime = dt.strptime(message.text, "%Y-%m-%d %H:%M")
            except Exception:
                bot.send_message(user.id, app_strings[user.lang].create_event.invalid_datetime)
                return
        data["state"].add_data(datetime=event_datetime)
        bot.send_message(
            user.id,
            app_strings[user.lang].create_event.image_prompt,
            reply_markup=create_cancel_button(user.lang),
        )
        data["state"].set(CreateEventState.image)

    @bot.message_handler(content_types=["photo", "document", "text"], state=CreateEventState.image)
    def create_event_image(message: types.Message, data: dict):
        user = data["user"]
        db_session = data["db_session"]
        if message.content_type == "text" and message.text.lower() == "cancel":
            bot.send_message(user.id, app_strings[user.lang].create_event.cancel)
            data["state"].reset()
            return

        image_url = None
        if message.content_type == "photo":
            # Get the largest photo
            file_id = message.photo[-1].file_id
            image_url = file_id
        elif message.content_type == "document":
            file_id = message.document.file_id
            image_url = file_id
        elif message.content_type == "text":
            if message.text.lower() == "skip":
                image_url = None
            else:
                image_url = message.text

        # Gather all event data
        data["state"].add_data(content=image_url)
        with data["state"].data() as data_items:
            event_data = {
                "name": data_items.get("name"),
                "description": data_items.get("description"),
                "qtickets_link": data_items.get("qtickets_link"),
                "datetime": data_items.get("datetime"),
                "image_url": data_items.get("content"),
            }
            try:
                event = create_event(db_session, event_data)
                bot.send_message(
                    user.id,
                    app_strings[user.lang].create_event.success.format(name=event.name),
                )
            except Exception as e:
                bot.send_message(
                    user.id,
                    app_strings[user.lang].create_event.error.format(error=str(e)),
                )
        data["state"].delete()

    @bot.callback_query_handler(func=lambda call: call.data == "delete_event")
    def delete_event_list(message: types.Message, data: Dict[str, Any]) -> None:
        """
        Show all events as buttons for deletion.
        """
        user = data["user"]
        db_session = data["db_session"]
        events = read_events(db_session, skip=0, limit=100)
        if not events:
            bot.send_message(user.id, "Нет мероприятий для удаления.")
            return
        markup = types.InlineKeyboardMarkup()
        for event in events:
            markup.add(
                types.InlineKeyboardButton(
                    f"❌ {event.name}", callback_data=f"delete_event_{event.id}"
                )
            )
        bot.send_message(user.id, "Выберите мероприятие для удаления:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_event_"))
    def delete_event_handler(call: types.CallbackQuery, data: Dict[str, Any]) -> None:
        """
        Handle event deletion.
        """
        user = data["user"]
        db_session = data["db_session"]
        event_id = int(call.data.split("_")[2])
        success = remove_event(db_session, event_id)
        if success:
            bot.edit_message_text(
                chat_id=user.id,
                message_id=call.message.message_id,
                text="Мероприятие удалено."
            )
        else:
            bot.edit_message_text(
                chat_id=user.id,
                message_id=call.message.message_id,
                text="Мероприятие не найдено."
            )
