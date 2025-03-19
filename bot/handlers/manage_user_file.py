import os
from typing import List

from telegram import Update
from telegram.ext import CallbackContext

from bot.keyboard_markup import get_list_markup
from config import uploads_path, cleanup_original, cleanup_markdown
from data.user_manager import UserManager
from data.language_manager import LanguageManager
from data.database_manager import DatabaseManager
from utils.file_processor import process_file



async def file_handler(update: Update, context: CallbackContext) -> None:
    """
    Handles the file upload process.
    Takes an uploaded file from a user, checks if the user is allowed, saves the file temporarily,
    attempts to process the file, and then deletes the file if processing is successful and cleanup is enabled.

    Returns:
    - int: The state of the conversation after handling the file.
    """
    user_id = update.effective_chat.id
    username = update.effective_user.username

    user_manager = UserManager()
    lang_manager = LanguageManager()
    lang = lang_manager.get_user_language(user_id)

    if not user_manager.is_allowed_user(username):
        user_manager.logger.warning(f'{username} ({user_id}) tried issuing a command but was not allowed.')
        await update.message.reply_text(lang_manager.get_message("access_denied"))
        return

    file_name = update.message.document.file_name
    file_path = os.path.join(uploads_path, str(user_id), file_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    message = lang_manager.get_message('proc_file', lang)
    await update.message.reply_text(message)

    try:
        file_content = await update.message.document.get_file()
        await file_content.download_to_drive(file_path)
        user_manager.logger.info(f'File from {username} ({user_id}) temporarily loaded to {file_path}.')
        is_processed = await process_file(
            file_path,
            user_id,
            source=file_name,
            cleanup_original=cleanup_original,
            cleanup_markdown=cleanup_markdown,
        )
        if is_processed:
            message = lang_manager.get_message('proc_file_ok', lang).format(file_name=file_name)
        else:
            message = lang_manager.get_message('proc_file_fail', lang).format(file_name=file_name)
        await update.message.reply_text(message)

    except Exception as e:
        message = lang_manager.get_message('file_failed', lang).format(e=e)
        await update.message.reply_text(message)
        user_manager.logger.error(f"File processing failed: {e}")


async def docs_list_handler(update: Update, context: CallbackContext) -> None:
    """Handler for listing user's documents."""
    user_id = update.effective_chat.id
    username = update.effective_user.username

    db_manager = DatabaseManager()
    user_manager = UserManager()
    lang_manager = LanguageManager()
    lang = lang_manager.get_user_language(user_id)

    if not user_manager.is_allowed_user(username):
        user_manager.logger.warning(f'{username} ({user_id}) tried issuing a command but was not allowed.')
        await update.message.reply_text(lang_manager.get_message("access_denied"))
        return

    lang = lang_manager.get_user_language(user_id)
    users_docs = db_manager.get_users_docs(user_id)
    db_manager.logger.info(f'{username} ({user_id}) has {len(users_docs)} saved sources.')

    if len(users_docs) == 0:
        message = lang_manager.get_message('empty', lang)
        await update.message.reply_text(message)
    else:
        await send_docs_list(update, context, page=0, users_docs=users_docs)

    
async def send_docs_list(update: Update, context: CallbackContext, page: int, users_docs: List) -> None:
    """Send a list of documents with pagination to the user."""
    user_id = update.effective_chat.id

    lang_manager = LanguageManager()
    lang = lang_manager.get_user_language(user_id)

    if update.callback_query:
        reply_method = update.callback_query.edit_message_text
    else:
        reply_method = update.message.reply_text
    
    reply_markup = get_list_markup(page, users_docs)
    message = lang_manager.get_message('sources', lang)
    await reply_method(message, reply_markup=reply_markup)


async def list_buttons_handler(update: Update, context: CallbackContext) -> None:
    """Handle source deletion and page navigation callback queries."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_chat.id
    username = update.effective_user.username

    db_manager = DatabaseManager()
    lang_manager = LanguageManager()
    lang = lang_manager.get_user_language(user_id)

    if query.data.startswith("delete_"):
        deleted_doc = query.data.replace("delete_", "", 1)
        db_manager.delete_doc(user_id=user_id, source=deleted_doc)
        
        db_manager.logger.info(f'{username} ({user_id}) deleted document {deleted_doc}.')
        message = lang_manager.get_message('deleted_doc', lang).format(deleted_doc=deleted_doc)
        await query.message.reply_text(message)
        await docs_list_handler(update, context)  # Reset to the first page after deletion

    elif query.data.startswith("page_"):
        page = int(query.data.split("_")[1])
        users_docs = db_manager.get_users_docs(user_id)
        await send_docs_list(update, context, page, users_docs=users_docs)
