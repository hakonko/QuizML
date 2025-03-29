import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QSlider, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from code.userdata import User, UserDatabase
from code.login_popup import LoginPopup
from datetime import datetime
import pandas as pd
from collections import defaultdict

CATEGORY_NAMES = {
    "1": "Linear Models",
    "2": "Neural Nets",
    "3": "CNNs",
    "4": "Deep Architectures",
    "5": "Backprop and Optimization",
    "6": "Performance Estimation",
    "7": "Data Augmentation",
    "8": "RNNs",
    "9": "Vision Transformers",
    "10": "Adversarial Attacks",
    "11": "Object Detection",
    "12": "Image Segmentation",
    "13": "Distribution Shifts"
}

class DashboardApp(QWidget):
    def __init__(self, user: User, user_db: UserDatabase, quiz_callback, retake_callback, edit_callback, return_to_login):
        super().__init__()
        self.user = user
        self.user_db = user_db
        self.quiz_callback = quiz_callback
        self.retake_callback = retake_callback
        self.edit_callback = edit_callback
        self.return_to_login = return_to_login

        self.setWindowTitle("QuizML Dashboard")
        self.setMinimumSize(1000, 600)
        self.setStyleSheet("background-color: black;")

        layout = QHBoxLayout()

        left_container = QWidget()
        left_container.setStyleSheet("background-color: transparent;")
        left_panel = QVBoxLayout(left_container)
        left_panel.setContentsMargins(0, 0, 0, 0)
        left_panel.setSpacing(10)
        title = QLabel("Your Quizzes")
        title.setStyleSheet("font-size: 20pt; color: white; padding: 5px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_panel.addWidget(title)

        self.quiz_list = QListWidget()

        self.quiz_list.setStyleSheet("""
            QListWidget {
                color: white;
                font-size: 14pt;
                border: none;
                background-color: transparent;
            }
            QListWidget::item {
                border-bottom: 1px dashed #8000c8;
                padding: 8px 4px;
            }
            QListWidget::item:selected {
                background-color: #8000c8;
            }
        """)

        left_panel.addWidget(self.quiz_list, stretch=1)
        self.refresh_quiz_list()

        self.num_problems_label = QLabel("Number of questions: 10")
        self.num_problems_label.setStyleSheet("color: white; font-size: 14pt;")
        left_panel.addWidget(self.num_problems_label)

        self.num_problems_slider = QSlider(Qt.Orientation.Horizontal)
        self.num_problems_slider.setMinimum(5)
        self.num_problems_slider.setMaximum(30)
        self.num_problems_slider.setValue(10)
        self.num_problems_slider.valueChanged.connect(self._update_slider_label)
        left_panel.addWidget(self.num_problems_slider)

        self.new_quiz_btn = QPushButton("Take new quiz")
        self.new_quiz_btn.clicked.connect(self._start_new_quiz_with_slider)

        self.retake_btn = QPushButton("Retake selected quiz")
        self.retake_btn.clicked.connect(self._retake_selected)

        self.delete_btn = QPushButton("Delete selected quiz")
        self.delete_btn.clicked.connect(self._delete_selected)

        self.edit_btn = QPushButton("Edit questions")
        self.edit_btn.clicked.connect(self.edit_callback)

        for btn in [self.new_quiz_btn, self.retake_btn, self.delete_btn, self.edit_btn]:
            btn.setStyleSheet(
                "font-size: 14pt; padding: 10px; background-color: #8000c8; color: white; "
                "border-radius: 10px; border: none; font-weight: bold;"
            )
            left_panel.addWidget(btn)

        right_container = QWidget()

        right_container.setStyleSheet("""
            background-color: black;
            border-radius: 15px;
        """)

        right_panel = QVBoxLayout(right_container)
        right_panel.setContentsMargins(20, 20, 20, 20)
        right_panel.setSpacing(10)

        stats_label = QLabel("Category Stats")
        stats_label.setStyleSheet("font-size: 24pt; color: white; background-color: black;")
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_panel.addWidget(stats_label)

        self.stats_display = QLabel()
        self.stats_display.setStyleSheet("color: white; font-size: 14pt;")
        self.stats_display.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stats_display.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        right_panel.addWidget(self.stats_display, stretch=1)

        self.quit_btn = QPushButton("Save and Quit")
        self.quit_btn.clicked.connect(self._save_and_quit)

        self.reset_btn = QPushButton("Reset Statistics")
        self.reset_btn.clicked.connect(self._reset_statistics)
        self.reset_btn.setStyleSheet(
            "font-size: 14pt; padding: 10px; background-color: black; color: white; "
            "border-radius: 10px; border: 2px solid white; font-weight: bold;"
        )
        
        self.quit_btn.setStyleSheet(
            "font-size: 14pt; padding: 10px; background-color: black; color: white; "
            "border-radius: 10px; border: 2px solid white; font-weight: bold;"
        )

        quit_layout = QHBoxLayout()
        quit_layout.addWidget(self.reset_btn)
        quit_layout.addStretch()
        quit_layout.addWidget(self.quit_btn)

        right_panel.addLayout(quit_layout)

        layout.addWidget(left_container, 2)
        layout.addWidget(right_container, 3)
        self.setLayout(layout)
        self.update_stats()

    def refresh_quiz_list(self):
        self.quiz_list.clear()
        sorted_quizzes = sorted(self.user.saved_quizzes, key=lambda q: q.date_taken, reverse=True)
        for idx, quiz in enumerate(sorted_quizzes):
            percent = round((sum(quiz.results) / len(quiz.results)) * 100) if quiz.results else 0
            quiz_date = quiz.date_taken.strftime("%d. %B %Y %H:%M") if hasattr(quiz, "date_taken") else "Unknown date"
            num_questions = len(quiz.results)
            item = QListWidgetItem(f"Quiz {idx + 1} ({percent}%, {quiz.grade}) - {quiz_date} ({num_questions} questions)")
            item.setSizeHint(item.sizeHint())  # sørger for tilstrekkelig plass
            item.setData(Qt.ItemDataRole.UserRole, idx)
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
        self.update_stats()

    def _save_and_quit(self):
        self.user_db.save()
        self.close()
        self.return_to_login()

    def update_stats(self):
        genre_stats = defaultdict(lambda: {"correct": 0, "total": 0})

        try:
            df = pd.read_csv("quiz/quiz_3310.csv", sep=';')
            pid_to_genre = dict(zip(df['_pid'], df['_genre'].astype(str)))
        except Exception as e:
            self.stats_display.setText("Error loading quiz file.")
            return

        for pid, stat in self.user.question_stats.items():
            genre = pid_to_genre.get(int(pid))
            if genre is None:
                continue
            genre_stats[genre]["correct"] += stat["correct"]
            genre_stats[genre]["total"] += stat["correct"] + stat["wrong"]

        results = []
        for genre, stat in genre_stats.items():
            if stat["total"] == 0:
                continue
            accuracy = round(100 * stat["correct"] / stat["total"])
            label = CATEGORY_NAMES.get(genre, f"{genre}")
            results.append((accuracy, label))

        results.sort(reverse=True)
        lines = [f"{label:<30}\t{acc:>3}% accuracy" for acc, label in results]

        html = "<table style='color:white; font-size:14pt;'>"
        for acc, label in results:
            html += f"<tr><td style='padding-right:30px;'>{label}</td><td>{acc}% accuracy</td></tr>"
        html += "</table>"
        self.stats_display.setText(html)

    def _reset_statistics(self):
        confirm = QMessageBox.question(
            self, "Reset Confirmation",
            "Are you sure you want to reset all your statistics?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.user.question_stats.clear()
            self.user_db.save()
            self.update_stats()
            QMessageBox.information(self, "Reset Complete", "All your statistics have been reset.")



