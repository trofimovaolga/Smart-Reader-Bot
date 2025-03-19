from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import sources_per_page, supported_languages


def truncate_to_bytes(s: str, max_bytes: int = 64, encoding: str = "utf-8") -> str:
    """Button's callback_data can't exceed 64 bytes"""
    encoded = s.encode(encoding)
    truncated = encoded[:max_bytes]
    return truncated.decode(encoding, errors="ignore")


def get_list_markup(page: int, sources: List[str]):
    """Generate markup for a list of sources with pagination"""
    start_idx = page * sources_per_page
    end_idx = start_idx + sources_per_page
    docs_on_page = sources[start_idx:end_idx]

    keyboard = []
    for doc in docs_on_page:
        keyboard.append([
            InlineKeyboardButton(f"{doc}", callback_data=f"disabled"),
            InlineKeyboardButton("❌ Delete", callback_data=f"delete_{truncate_to_bytes(doc, 57)}")
        ])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"page_{page-1}"))
    if end_idx < len(sources):
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"page_{page+1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(keyboard)


def get_lang_markup():
    """Generate markup for language selection"""
    keyboard = []
    for lang in supported_languages:
        keyboard.append([
            InlineKeyboardButton(f"{lang.upper()}", callback_data=f"{lang}"),
        ])

    return InlineKeyboardMarkup(keyboard)
