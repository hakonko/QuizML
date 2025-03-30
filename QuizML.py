import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from pathlib import Path
from code.login_popup import LoginPopup
from code.dashboard import DashboardApp
from code.userdata import UserDatabase
from code.quiz import Quiz
from code.quiz_gui import QuizApp
from code.editor import QuestionEditor
from code.summary import SummaryWindow

QUIZ_FILE = Path("data/quizdata.pkl")

class MainApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuizML")
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.95), int(screen.height() * 0.95))

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
            quiz_callback=self.start_new_quiz,
            retake_callback=self.retake_quiz,
            edit_callback=self.open_question_editor,
            summary_callback=self.show_summary_dashboard,
            return_to_login=self.return_to_login
        )

        self.setCentralWidget(self.dashboard)

    def refresh_dashboard(self):
        self.dashboard.refresh_quiz_list()
        self.dashboard.update_stats()

    def start_new_quiz(self, num_questions):
        quiz = Quiz(num_questions, user_file=None, quiz_file=QUIZ_FILE, user=self.user)
        self.quiz_window = QuizApp(quiz, self.user)
        self.quiz_window.quiz_completed.connect(self.show_summary_quiz)
        self.quiz_window.show()
        self.hide()

    def retake_quiz(self, quiz):
        self.quiz_window = QuizApp(quiz, self.user)
        self.quiz_window.quiz_completed.connect(self.show_summary_quiz)
        self.quiz_window.show()
        self.hide()

    def show_summary_dashboard(self, quiz):
        self.dashboard.hide()
        self.summary_window = SummaryWindow(quiz, return_callback=self.return_from_summary)
        self.setCentralWidget(self.summary_window)

    def show_summary_quiz(self, quiz):
        # Lagre quizresultatet før vi viser summary
        if quiz:
            self.user.add_quiz(quiz)
            self.user_db.save()

        self.show()  # Vis MainApp-vinduet igjen
        self.summary_window = SummaryWindow(quiz, return_callback=self.return_from_summary)
        self.setCentralWidget(self.summary_window)


    def return_from_summary(self):
        # Opprett nytt dashboard-vindu
        self.dashboard = DashboardApp(
            self.user,
            self.user_db,
            quiz_callback=self.start_new_quiz,
            retake_callback=self.retake_quiz,
            edit_callback=self.open_question_editor,
            summary_callback=self.show_summary_dashboard,  # <-- Denne manglet
            return_to_login=self.return_to_login
        )
        self.setCentralWidget(self.dashboard)
        self.refresh_dashboard()

    def return_from_editor(self):
        self.editor_window.close()
        self.show()
        self.refresh_dashboard()

    def return_to_login(self):
        self.user = None
        self.close()
        self.__init__()  # Restart appen og vis login på nytt

    def open_question_editor(self):
        self.editor_window = QuestionEditor(return_callback=self.return_from_editor)
        self.editor_window.show()
        self.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())