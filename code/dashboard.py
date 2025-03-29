from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QSlider
)
from PyQt6.QtCore import Qt
from code.userdata import User, UserDatabase
from datetime import datetime

class DashboardApp(QWidget):

    def __init__(self, user: User, user_db: UserDatabase, quiz_callback, retake_callback, edit_callback):
        super().__init__()
        self.user = user
        self.user_db = user_db
        self.quiz_callback = quiz_callback
        self.retake_callback = retake_callback
        self.edit_callback = edit_callback

        self.setWindowTitle("QuizML Dashboard")
        self.setMinimumSize(1000, 600)
        self.setStyleSheet("background-color: black;")

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        ### Left panel
        left_container = QWidget()
        left_container.setStyleSheet("background-color: black;")
        left_panel = QVBoxLayout(left_container)
        left_panel.setContentsMargins(0, 0, 0, 0)
        left_panel.setSpacing(10)
        title = QLabel("Your Quiztory")
        title.setStyleSheet("font-size: 20pt; color: white; padding: 5px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_panel.addWidget(title)

        self.quiz_list = QListWidget()
        self.quiz_list.setStyleSheet("background-color: black; color: white; font-size: 14pt; border: none;")
        left_panel.addWidget(self.quiz_list, stretch=1)

        self.refresh_quiz_list()

        # Action buttons
        self.retake_btn = QPushButton("Retake selected quiz")
        self.retake_btn.clicked.connect(self._retake_selected)

        self.delete_btn = QPushButton("Delete selected quiz")
        self.delete_btn.clicked.connect(self._delete_selected)

        self.new_quiz_btn = QPushButton("Take new quiz")
        self.new_quiz_btn.clicked.connect(self._start_new_quiz_with_slider)

        self.edit_btn = QPushButton("Edit questions")
        self.edit_btn.clicked.connect(self.edit_callback)  # Du må sende inn en edit_callback fra MainApp

        for btn in [self.new_quiz_btn, self.retake_btn, self.delete_btn, self.edit_btn]:
            btn.setStyleSheet(
                "font-size: 14pt; padding: 10px; background-color: #8000c8; color: white; "
                "border-radius: 10px; border: none; font-weight: bold;"
            )
            left_panel.addWidget(btn)

        ### Right panel
        right_container = QWidget()
        right_container.setStyleSheet("background-color: black;")
        right_panel = QVBoxLayout(right_container)
        right_panel.setContentsMargins(0, 0, 0, 0)
        right_panel.setSpacing(0)
        stats_label = QLabel("Category Stats (coming soon)")
        stats_label.setStyleSheet("font-size: 24pt; color: white; background-color: black;")
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_panel.addWidget(stats_label)

        self.num_problems_label = QLabel("Number of questions: 10")
        self.num_problems_label.setStyleSheet("color: white; font-size: 14pt;")
        left_panel.addWidget(self.num_problems_label)

        self.num_problems_slider = QSlider(Qt.Orientation.Horizontal)
        self.num_problems_slider.setMinimum(5)
        self.num_problems_slider.setMaximum(30)
        self.num_problems_slider.setValue(13) # Default number of questions (number of categories)
        self.num_problems_slider.setStyleSheet("background-color: black;")
        self.num_problems_slider.valueChanged.connect(self._update_slider_label)
        left_panel.addWidget(self.num_problems_slider)

        layout.addWidget(left_container, 2)
        layout.addWidget(right_container, 3)

        self.setLayout(layout)

    def refresh_quiz_list(self):
        self.quiz_list.clear()
 
        sorted_quizzes = sorted(self.user.saved_quizzes, key=lambda q: q.date_taken, reverse=True)

        for idx, quiz in enumerate(sorted_quizzes):
            percent = round((sum(quiz.results) / len(quiz.results)) * 100) if quiz.results else 0
            grade = quiz.grade
            quiz_date = quiz.date_taken.strftime("%d. %B %Y %H:%M") if hasattr(quiz, "date_taken") else "Unknown date"
            num_questions = len(quiz.results)
            item = QListWidgetItem(f"Quiz {idx + 1} ({percent}%, {grade}) - {quiz_date} ({num_questions} questions)")
            self.quiz_list.addItem(item)

    def _update_slider_label(self, value):
        self.num_problems_label.setText(f"Number of questions: {value}")

    def _start_new_quiz_with_slider(self):
        num_questions = self.num_problems_slider.value()
        self.quiz_callback(num_questions)

    def _retake_selected(self):
        selected_items = self.quiz_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Select Quiz", "Please select a quiz to retake.")
            return
        index = self.quiz_list.currentRow()
        quiz = self.user.saved_quizzes[index]
        self.retake_callback(quiz)

    def _delete_selected(self):
        selected_items = self.quiz_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Select Quiz", "Please select a quiz to delete.")
            return
        index = self.quiz_list.currentRow()
        del self.user.saved_quizzes[index]
        self.user_db.save()
        self.refresh_quiz_list()