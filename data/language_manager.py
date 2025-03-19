import os
import json
import sqlite3
from typing import Dict

from config import messages_path, languages_db_path, supported_languages
from utils.logging_config import setup_logging
from utils.singleton import singleton



@singleton
class LanguageManager:
    """Manages language preferences and messages."""
    def __init__(self, db_path: str = languages_db_path, messages_file: str = messages_path):
        """
        Init with SQLite database and bot messages file.
        Args:
            db_path: Path to SQLite database for language preferences.
            messages_file: Path to JSON file containing messages.
        """
        self._init_db(db_path)
        self.supported_languages = supported_languages
        self.messages = self._load_messages(messages_file)
        self.logger = setup_logging('LanguageManager')


    def _init_db(self, db_path: str):
        """Initialize SQLite database with language preferences."""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_languages (
                user_id INTEGER PRIMARY KEY,
                language TEXT NOT NULL DEFAULT 'en'
            )
        """)
        self.conn.commit()

    
    def _load_messages(self, messages_file: str) -> Dict[str, Dict[str, str]]:
        """Load messages from external JSON file."""
        if not os.path.exists(messages_file):
            raise FileNotFoundError(f"Messages file '{messages_file}' not found.")
        with open(messages_file, 'r', encoding='utf-8') as f:
            return json.load(f)


    def set_user_language(self, user_id: int, lang: str) -> bool:
        """
        Set user's language preference.
        Args:
            user_id: Telegram user ID.
            lang: Language key ('en', 'ru', 'de').
        Returns:
            bool: True if successful, False if language is unsupported.
        """
        if lang not in self.supported_languages:
            return False
        
        self.cursor.execute("""
            INSERT OR REPLACE INTO user_languages (user_id, language)
            VALUES (?, ?)
        """, (user_id, lang))
        self.conn.commit()
        return True


    def get_user_language(self, user_id: int) -> str:
        """
        Get user's preferred language, default is 'en'.
        Args:
            user_id: Telegram user ID.
        Returns:
            str: Language key ('en', 'ru', 'de').
        """
        self.cursor.execute("""
            SELECT language FROM user_languages WHERE user_id = ?
        """, (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 'en'


    def get_message(self, message_key: str, lang: str = "en") -> str:
        """
        Get a message in specified language.
        Args:
            message_key: Key for the message ('welcome').
            lang: Language key.
        Returns:
            str: Message in requested language.
        """
        if message_key not in self.messages:
            return f"Message '{message_key}' not found."
        return self.messages[message_key][lang]


    def get_supported_languages(self) -> set:
        """Return supported languages."""
        return self.supported_languages
