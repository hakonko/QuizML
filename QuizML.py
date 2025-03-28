import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from pathlib import Path
from code.login_popup import LoginPopup
from code.dashboard import DashboardApp
from code.userdata import UserDatabase
from code.quiz import Quiz
from code.quiz_gui import QuizApp

NUM_PROBLEMS = 20
QUIZ_FILE = Path("quiz/quiz_3310.csv")

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuizML")
        self.setGeometry(100, 100, 800, 600)

        self.user_db = UserDatabase()
        self.user = None

        self.login_popup = LoginPopup(self.user_db)
        if self.login_popup.exec():
            self.user = self.login_popup.user
        else:
            sys.exit()
        self.dashboard = DashboardApp(
            self.user,
            self.user_db,
            quiz_callback=self.start_new_quiz,  # denne må ta imot num_questions
            retake_callback=self.retake_quiz
        )

        self.setCentralWidget(self.dashboard)

    def refresh_dashboard(self):
        self.dashboard.refresh_quiz_list()

    def start_new_quiz(self, num_questions):
        quiz = Quiz(num_questions, user_file=None, quiz_file=QUIZ_FILE)
        self.quiz_window = QuizApp(quiz, self.user.name)
        self.quiz_window.quiz_completed.connect(self.on_quiz_complete)
        self.quiz_window.show()
        self.hide()


    def retake_quiz(self, quiz):
        self.quiz_window = QuizApp(quiz, self.user.name)
        self.quiz_window.quiz_completed.connect(lambda _: self.on_quiz_complete(None))
        self.quiz_window.show()
        self.hide()

    def on_quiz_complete(self, quiz):
        if quiz:
            self.user.add_quiz(quiz)
            self.user_db.save()
        self.show()
        self.refresh_dashboard()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())
