from telegram import Update
from telegram.ext import CallbackContext
from data.user_manager import UserManager
from data.language_manager import LanguageManager


async def add_user(update: Update, context: CallbackContext) -> None:
    """
    Handle adding a user to the allowlist.

    This function checks if the user is an admin, then attempts to add a new user to the allowlist.
    If the user is not an admin, it returns a 'not_authorized' message.
    If no arguments are provided, it asks the user to specify a username.
    If the user is already in the allowlist, it returns a 'user_exists' message.
    Otherwise, it adds the user to the allowlist and returns a 'user_added' message.
    """
    user_id = update.effective_chat.id
    username = update.effective_user.username

    user_manager = UserManager()
    lang_manager = LanguageManager()
    lang = lang_manager.get_user_language(user_id)
    
    if not user_manager.is_admin(username):
        message = lang_manager.get_message('not_authorized')
    elif not context.args:
        message = lang_manager.get_message('add_user')
    else:
        new_user = context.args[0]
        new_user = new_user.replace('@', '')

        if user_manager.is_allowed_user(new_user):
            message = lang_manager.get_message('user_exists', lang).format(username=new_user)
        else:
            user_manager.add_user(new_user)
            message = lang_manager.get_message('user_added', lang).format(username=new_user)
            user_manager.logger.info(f'{username} added new user {new_user}')
    
    await update.message.reply_text(message)


async def add_admin(update: Update, context: CallbackContext) -> None:
    """
    Handle adding admin user.

    This function checks if the user is an admin, then attempts to add a new user to the allowlist.
    If the user is not an admin, it returns a 'not_authorized' message.
    If no arguments are provided, it asks the user to specify a username.
    If the user is already marked as admin in the allowlist, it returns a 'user_exists' message.
    Otherwise, it adds the user with admin's status to the allowlist and returns a 'user_added' message.
    
    """
    user_id = update.effective_chat.id
    username = update.effective_user.username

    user_manager = UserManager()
    lang_manager = LanguageManager()
    lang = lang_manager.get_user_language(user_id)
    
    if not user_manager.is_admin(username):
        message = lang_manager.get_message('not_authorized')
    elif not context.args:
        message = lang_manager.get_message('add_admin')
    else:
        new_user = context.args[0]
        new_user = new_user.replace('@', '')

        if user_manager.is_allowed_user(new_user) and user_manager.is_admin(new_user):
            message = lang_manager.get_message('user_exists', lang).format(username=new_user)
        else:
            user_manager.add_user(new_user, is_admin=1)
            message = lang_manager.get_message('user_added', lang).format(username=new_user)
            user_manager.logger.info(f'{username} added new user {new_user}')
    
    await update.message.reply_text(message)


async def del_user(update: Update, context: CallbackContext) -> None:
    """
    Handle removing a user from the allowlist.

    This function checks if the user is an admin, then attempts to remove a user from the allowlist.
    If the user is not an admin, it returns a 'not_authorized' message.
    If no arguments are provided, it prompts the user to specify a username.
    If the user is not in the allowlist, it returns a 'user_not_found' message.
    Otherwise, it removes the user from the allowlist and returns a 'user_removed' message.
    """
    user_id = update.effective_chat.id
    username = update.effective_user.username

    user_manager = UserManager()
    lang_manager = LanguageManager()
    lang = lang_manager.get_user_language(user_id)

    if not user_manager.is_admin(username):
        message = lang_manager.get_message('not_authorized')
    elif not context.args:
        message = lang_manager.get_message('specify_username')
    else:
        user_to_remove = context.args[0]
        user_to_remove = user_to_remove.replace('@', '')

        if user_manager.is_allowed_user(user_to_remove):
            user_manager.remove_user(user_to_remove)
            message = lang_manager.get_message('user_removed', lang).format(username=user_to_remove)
            user_manager.logger.info(f'{username} removed user {user_to_remove}')
        else:
            message = lang_manager.get_message('user_not_found', lang).format(username=user_to_remove)
    
    await update.message.reply_text(message)


async def show_users(update: Update, context: CallbackContext) -> None:
    """
    Handle showing the current users in the allowlist.

    This function checks if the user is an admin, then returns a list of users in the allowlist.
    If the user is not an admin, it returns a 'not_authorized' message.
    Otherwise, it returns a formatted list of users.
    """
    user_id = update.effective_chat.id
    username = update.effective_user.username

    user_manager = UserManager()
    lang_manager = LanguageManager()
    lang = lang_manager.get_user_language(user_id)

    if not user_manager.is_admin(username):
        message = lang_manager.get_message('not_authorized')
    else:
        users_list = [f"{e[0].replace('@', '')}, is admin: {e[1]}" for e in user_manager.list_users()]
        users_list = sorted(users_list, key=lambda x: x[0])
        users_list = '\n'.join(users_list)
        message = lang_manager.get_message('show_users', lang).format(users=users_list)

    await update.message.reply_text(message)
