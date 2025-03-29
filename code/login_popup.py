from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QMessageBox, QInputDialog, QSizePolicy
from PyQt6.QtCore import Qt
from code.userdata import User, UserDatabase
import bcrypt

class LoginPopup(QDialog):
    def __init__(self, user_db: UserDatabase):
        super().__init__()
        self.setWindowTitle("Login / Sign up")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: #8000c8;")

        self.user_db = user_db
        self.user = None

        layout = QVBoxLayout()
        layout.setSpacing(20)

        self.label = QLabel("QuizML")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 36px; font-weight: bold; color: white; background-color: #8000c8;")
        layout.addWidget(self.label)

        self.username_entry = QLineEdit()
        self.username_entry.setPlaceholderText("User Name")
        self.username_entry.setStyleSheet("""
            background-color: white; color: black; padding: 6px;
            border-radius: 10px; border: none;
        """)
        layout.addWidget(self.username_entry)

        self.password_entry = QLineEdit()
        self.password_entry.setPlaceholderText("Password")
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_entry.setStyleSheet("""
            background-color: white; color: black; padding: 6px;
            border-radius: 10px; border: none;
        """)
        layout.addWidget(self.password_entry)

        # Make Enter trigger login
        self.password_entry.returnPressed.connect(self.login)
        self.username_entry.returnPressed.connect(self.login)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        button_style = """
            QPushButton {
                font-weight: bold;
                border-radius: 10px;
                padding: 8px 16px;
                min-width: 100px;
            }
        """

        self.signup_button = QPushButton("Sign up")
        self.signup_button.clicked.connect(self.signup)
        self.signup_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #8000c8;
                color: white;
                border: 2px solid white;
            }
            QPushButton:hover {
                background-color: #a050e0;
            }
        """)
        self.signup_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        self.login_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: black;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        self.login_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        button_layout.addWidget(self.signup_button)
        button_layout.addWidget(self.login_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def login(self):
        username = self.username_entry.text().strip()
        password = self.password_entry.text().strip().encode()

        user = self.user_db.get_user(username)
        if not user:
            QMessageBox.critical(self, "Error", "No user found.")
            return

        if not bcrypt.checkpw(password, user.password_hash):
            QMessageBox.critical(self, "Error", "Wrong password.")
            return

        self.user = user
        self.accept()

    def signup(self):
        username = self.username_entry.text().strip()
        password = self.password_entry.text().strip().encode()

        if self.user_db.user_exists(username):
            QMessageBox.warning(self, "Already signed up", "Username already in use.")
            return

        name, ok = QInputDialog.getText(self, "Full name", "Please enter your full name:")
        if not ok or not name:
            return

        password_hash = bcrypt.hashpw(password, bcrypt.gensalt())
        user = User(name=name, username=username, password_hash=password_hash)
        self.user_db.add_user(user)
        self.user = user
        self.accept()
