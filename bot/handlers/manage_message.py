from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from config import add_relative_queries
from data.utils import sanitize_response
from data.user_manager import UserManager
from data.language_manager import LanguageManager
from utils.rag import RAG, QueryExpander



async def start(update: Update, context: CallbackContext) -> None:
    """Handles the /start command. Sends a welcome message and asks for language preference."""
    user_id = update.effective_chat.id
    username = update.effective_user.username

    user_manager = UserManager()
    lang_manager = LanguageManager()
    lang = lang_manager.get_user_language(user_id)

    if not user_manager.is_allowed_user(username):
        user_manager.logger.warning(f'{username} ({user_id}) tried issuing a command but was not allowed.')
        await update.message.reply_text(lang_manager.get_message("access_denied"))
        return

    await update.message.reply_text(lang_manager.get_message("welcome", lang))


async def user_query_handler(update: Update, context: CallbackContext) -> None:
    """Handles a question from the user and replies with the assistant's response."""
    user_id = update.effective_chat.id
    username = update.effective_user.username
    user_query = update.message.text

    user_manager = UserManager()
    lang_manager = LanguageManager()
    lang = lang_manager.get_user_language(user_id)

    if not user_manager.is_allowed_user(username):
        user_manager.logger.warning(f'{username} ({user_id}) tried issuing a command but was not allowed.')
        message = lang_manager.get_message('access_denied')
        await update.message.reply_text(message)
        return
    
    message = lang_manager.get_message('proc_request', lang)
    await update.message.reply_text(message)
    user_manager.logger.info(f'{username} ({user_id}) asked "{user_query}".')

    try:
        if add_relative_queries:
            relative_questions = QueryExpander().expand_query(user_query, lang)
        else:
            relative_questions = None

        response = RAG().process(user_query, user_id, lang, relative_questions)
        clean_response = sanitize_response(response)

        try:
            await update.message.reply_text(clean_response, parse_mode=ParseMode.MARKDOWN_V2)
        except BadRequest:
            user_manager.logger.warning(f"Failed to apply parse_mode MARKDOWN_V2 to message {response}")
            await update.message.reply_text(response)
    
    except Exception as e:
        user_manager.logger.error(f'Error while generating response: {e}')
        err = lang_manager.get_message('error', lang).format(error=e)
        await update.message.reply_text(err)

async def unsupported_file_handler(update: Update, context: CallbackContext) -> None:
    """Handles unsupported file types like images, videos, etc."""
    user_id = update.effective_chat.id
    username = update.effective_user.username

    user_manager = UserManager()
    lang_manager = LanguageManager()
    lang = lang_manager.get_user_language(user_id)

    if not user_manager.is_allowed_user(username):
        user_manager.logger.warning(f'{username} ({user_id}) tried issuing a command but was not allowed.')
        await update.message.reply_text(lang_manager.get_message("access_denied"))
        return

    await update.message.reply_text(lang_manager.get_message("unsupported_file_type", lang))