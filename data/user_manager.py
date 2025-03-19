import os
import sqlite3
from typing import List

from config import users_data_db_path, ADMIN_NICKNAME
from utils.logging_config import setup_logging
from utils.singleton import singleton



@singleton
class UserManager:
    def __init__(self, db_path: str = users_data_db_path):
        self.default_admin = ADMIN_NICKNAME.replace("@", "")
        self._init_db(db_path)
        self.logger = setup_logging('UserManager')

    def _init_db(self, db_path: str):
        """Initialize SQLite database with the users table."""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, 
                is_admin INTEGER DEFAULT 0
            )
        """)

        self.cursor.execute("SELECT username FROM users WHERE username = ?", (self.default_admin,))
        if self.cursor.fetchone() is None:  # Only add if not already present
            self.cursor.execute("INSERT INTO users (username, is_admin) VALUES (?, 1)", (self.default_admin,))

        self.conn.commit()

    def is_admin(self, username: str) -> bool:
        """Check if a user is an admin."""
        username = username.replace("@", "")
        self.cursor.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        return result is not None and result[0] == 1
    

    def is_allowed_user(self, username: str) -> bool:
        """Check if a user is allowed to use the bot."""
        username = username.replace("@", "")
        self.cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone() is not None
        return result
    

    def add_user(self, username: str, is_admin: int = 0) -> None:
        """Add a user to the allowed list (or update, admin only)."""
        username = username.replace("@", "")
        self.cursor.execute("INSERT OR REPLACE INTO users (username, is_admin) VALUES (?, ?)", (username, is_admin))
        self.conn.commit()


    def remove_user(self, username: str) -> None:
        """Remove a user from the allowed list (admin only)."""
        username = username.replace("@", "")
        self.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        self.conn.commit()


    def list_users(self) -> List:
        """Return a list of all users and their roles (admin only)."""
        self.cursor.execute("SELECT username, is_admin FROM users")
        users = self.cursor.fetchall()
        return users
