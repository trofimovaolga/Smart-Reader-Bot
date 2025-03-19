from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    filters,
    MessageHandler,
)

from bot.handlers.manage_user_file import file_handler, docs_list_handler, list_buttons_handler
from bot.handlers.manage_users import add_user, add_admin, del_user, show_users
from bot.handlers.manage_lang import set_language, language_button
from bot.handlers.manage_message import start, user_query_handler, unsupported_file_handler
from config import supported_languages


class SmartReaderBot:
    def __init__(self, token: str):
        self.app = ApplicationBuilder().token(token).build()
        self._register_handlers()


    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", start))

        self.app.add_handler(CommandHandler("set_lang", set_language))
        lang_buttons = '|'.join(list(supported_languages))
        self.app.add_handler(CallbackQueryHandler(language_button, pattern=f'^({lang_buttons})$'))

        self.app.add_handler(MessageHandler(filters.Document.ALL, file_handler))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_query_handler))
        self.app.add_handler(MessageHandler(~filters.Document.ALL & ~filters.COMMAND & ~filters.TEXT, unsupported_file_handler))
        
        self.app.add_handler(CommandHandler("sources", docs_list_handler))
        self.app.add_handler(CallbackQueryHandler(list_buttons_handler))

        # Admin only
        self.app.add_handler(CommandHandler("add_admin", add_admin))
        self.app.add_handler(CommandHandler("add_user", add_user))
        self.app.add_handler(CommandHandler("del_user", del_user))
        self.app.add_handler(CommandHandler("show_users", show_users))
    

    def run(self):
        self.app.run_polling()
