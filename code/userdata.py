import pickle
from pathlib import Path
from collections import defaultdict
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt

USERDATA_FILE = 'data/userdata.pkl'

def default_stat():
    return {'correct': 0, 'wrong': 0}

class User:
    def __init__(self, name, username, password_hash, saved_quizzes=None, question_stats=None):
        self.name = name
        self.username = username
        self.password_hash = password_hash
        self.saved_quizzes = saved_quizzes if saved_quizzes is not None else []

        # Bruk eksisterende stats hvis det finnes, ellers lag ny defaultdict
        self.question_stats = (
            defaultdict(default_stat, question_stats)
            if question_stats is not None
            else defaultdict(default_stat)
        )

    def add_quiz(self, quiz):
        self.saved_quizzes.append(quiz)


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

        self.user_db.save()
        self.accept()

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
