import pickle
from pathlib import Path
from collections import defaultdict
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
import time
import os

USERDATA_FILE = 'data/userdata.pkl'

def default_stat():
    return {'correct': 0, 'wrong': 0}

class User:
    def __init__(self, name, username, password_hash, saved_quizzes=None, question_stats=None, current_question_set=None):
        self.name = name
        self.username = username
        self.password_hash = password_hash
        self.saved_quizzes = saved_quizzes or []
        self.question_stats = question_stats or {}

        self.current_question_set = current_question_set or "data/quizdata.pkl"


        # Use existing stats if populated, or else make new defaultdict
        self.question_stats = (
            defaultdict(default_stat, question_stats)
            if question_stats is not None
            else defaultdict(default_stat)
        )

    def add_quiz(self, quiz):
        self.saved_quizzes.append(quiz)

    def update_question_stat(self, pid, correct):
        if pid not in self.question_stats:
            self.question_stats[pid] = [0, 0, time.time()]
        if correct:
            self.question_stats[pid][0] += 1
        self.question_stats[pid][1] += 1
        self.question_stats[pid][2] = time.time()


class UserDatabase:
    def __init__(self, filepath=USERDATA_FILE):
        self.filepath = Path(filepath)
        self.users = self._load_users()

    def _load_users(self):
        if self.filepath.exists():
            with open(self.filepath, 'rb') as f:
                self.users = pickle.load(f)
            
            for user in self.users.values():
                if not isinstance(user.question_stats, defaultdict):
                    user.question_stats = defaultdict(default_stat, user.question_stats)
                if not hasattr(user, "current_question_set"):
                    user.current_question_set = "data/quizdata.pkl"
        else:
            self.users = {}
            
        return self.users
    
    def save(self):
        with open(self.filepath, 'wb') as f:
            pickle.dump(self.users, f)

    def add_user(self, user: User):
        self.users[user.username] = user
        self.save()

    def get_user(self, username):
        return self.users.get(username)
    
    def user_exists(self, username):
        return username in self.users

class UserSettingsPopup(QDialog):
    def __init__(self, user, user_db, parent=None):
        super().__init__(parent)
        self.user = user
        self.user_db = user_db
        self.setWindowTitle("User Settings")
        self.setMinimumWidth(350)

        # === Styling (global stylesheet) ===
        self.setStyleSheet("""
            QDialog {
                background-color: #8000c8;
            }

            QLabel {
                background-color: #8000c8;
                color: white;
                font-size: 12pt;
            }

            QLineEdit {
                background-color: white;
                color: black;
                border: 2px solid white;
                border-radius: 10px;
                padding: 6px;
                font-size: 12pt;
            }

            QPushButton {
                background-color: black;
                color: white;
                border: 2px solid #8000c8;
                border-radius: 10px;
                font-weight: bold;
                padding: 8px 16px;
                font-size: 12pt;
            }

            QPushButton:hover {
                background-color: #f0e6fa;
            }

            QPushButton#delete {
                background-color: #8000c8;
                color: white;
                border: 2px solid white;
            }

            QPushButton#delete:hover {
                background-color: #9d32d9;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        self.username_input = QLineEdit(user.username)
        self.name_input = QLineEdit(user.name)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addWidget(QLabel("Username:"))
        layout.addWidget(self.username_input)

        layout.addWidget(QLabel("Full Name:"))
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("New Password:"))
        layout.addWidget(self.password_input)

        # OpenAI API key input
        self.api_key_input = QLineEdit()
        existing_api_key = os.getenv("OPENAI_API_KEY", "")
        self.api_key_input.setText(existing_api_key)
        self.api_key_input.setPlaceholderText("Enter OpenAI API Key here...")

        layout.addWidget(QLabel("OpenAI API Key:"))
        layout.addWidget(self.api_key_input)


        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_changes)
        layout.addWidget(self.save_btn)

        # Separate style for delete button
        self.delete_btn = QPushButton("Delete Account")
        self.delete_btn.setObjectName("delete")
        self.delete_btn.clicked.connect(self.confirm_delete)
        layout.addWidget(self.delete_btn)

        self.setLayout(layout)

    def save_changes(self):
        self.user.username = self.username_input.text()
        self.user.name = self.name_input.text()

        new_password = self.password_input.text().strip()
        if new_password:
            import bcrypt
            hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
            self.user.password_hash = hashed

        # Lagre OpenAI API-nøkkel til .env-fil
        api_key = self.api_key_input.text().strip()
        self._save_api_key_to_env(api_key)

        self.user_db.save()
        self.accept()

    def _save_api_key_to_env(self, api_key):
        env_path = Path(".env")
        env_lines = []

        # Hvis .env-filen allerede finnes, les og oppdater eksisterende nøkkel
        if env_path.exists():
            with env_path.open("r") as f:
                env_lines = f.readlines()
            
            # Sjekk om OPENAI_API_KEY allerede finnes
            updated = False
            for i, line in enumerate(env_lines):
                if line.startswith("OPENAI_API_KEY="):
                    env_lines[i] = f'OPENAI_API_KEY="{api_key}"\n'
                    updated = True
                    break

            # Hvis nøkkelen ikke eksisterte fra før, legg den til
            if not updated:
                env_lines.append(f'OPENAI_API_KEY="{api_key}"\n')
        else:
            # Opprett ny .env-fil
            env_lines.append(f'OPENAI_API_KEY="{api_key}"\n')

        # Skriv endringene tilbake til .env
        with env_path.open("w") as f:
            f.writelines(env_lines)


    def confirm_delete(self):
        confirm = QMessageBox.question(
            self,
            "Delete Account",
            "Are you sure you want to delete your account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            del self.user_db.users[self.user.username]
            self.user_db.save()
            self.accept()
            self.parent().return_to_login()
