from telegram import Update
from telegram.ext import CallbackContext

from bot.keyboard_markup import get_lang_markup
from data.user_manager import UserManager
from data.language_manager import LanguageManager



async def set_language(update: Update, context: CallbackContext) -> None:
    """
    Handle the language selection command. Displays language options if the user has permission.
    """
    user_id = update.effective_chat.id
    username = update.effective_user.username

    user_manager = UserManager()
    lang_manager = LanguageManager()

    if not user_manager.is_allowed_user(username):
        user_manager.logger.warning(f'{username} ({user_id}) tried issuing a command but was not allowed.')
        await update.message.reply_text(lang_manager.get_message("access_denied"))
        return

    cur_lang = lang_manager.get_user_language(user_id)
    message = lang_manager.get_message('choose_lang', cur_lang)
    await update.message.reply_text(message, reply_markup=get_lang_markup())


async def language_button(update: Update, context: CallbackContext) -> None:
    """
    Handle language selection callback when user clicks a language button. Sets the user's preferred language.
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_chat.id
    lang_manager = LanguageManager()

    pref_lang = query.data
    lang_manager.set_user_language(user_id, pref_lang)
    lang_manager.logger.info(f"{user_id} set {pref_lang} language.")
    
    message = lang_manager.get_message('lang_is_set', pref_lang).format(lang=pref_lang.upper())
    await query.message.reply_text(message)
