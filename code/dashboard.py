import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QSlider, QSpacerItem, QSizePolicy, QFrame, QStyle, QCheckBox
)

from PyQt6.QtCore import Qt
from code.userdata import User, UserDatabase, UserSettingsPopup
from code.login_popup import LoginPopup
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
import pandas as pd
from collections import defaultdict
import pickle
from code import __version__

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

GRADE_LIMITS = {90: 'A', 72: 'B', 62: 'C', 48: 'D', 38: 'E', 29: 'F'}

class DashboardApp(QWidget):
    def __init__(self, user: User, user_db: UserDatabase, quiz_callback, retake_callback, edit_callback, summary_callback, return_to_login):
        super().__init__()
        self.user = user
        self.user_db = user_db
        self.quiz_callback = quiz_callback
        self.retake_callback = retake_callback
        self.edit_callback = edit_callback
        self.summary_callback = summary_callback
        self.return_to_login = return_to_login

        self.setWindowTitle("QuizML Dashboard")
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.95), int(screen.height() * 0.95))
        self.setStyleSheet("background-color: black;")

        main_layout = QVBoxLayout()
        layout = QHBoxLayout()

        # === Left Container ===
        left_container = QWidget()
        left_container.setStyleSheet("background-color: transparent;")
        left_panel = QVBoxLayout(left_container)
        left_panel.setContentsMargins(0, 0, 0, 0)
        left_panel.setSpacing(10)

        title = QLabel(f"QuizML v{__version__}")
        title.setStyleSheet("""
            color: white;
            font-size: 48pt;
            font-weight: bold;
            padding: 5px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
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
        self.num_problems_slider.setMinimum(len(CATEGORY_NAMES))
        self.num_problems_slider.setMaximum(50)
        self.num_problems_slider.setValue(34)
        self._update_slider_label(34)
        self.num_problems_slider.valueChanged.connect(self._update_slider_label)

        self.show_formulas_checkbox = QCheckBox("Show formulas")
        self.show_formulas_checkbox.setChecked(False)
        self.show_formulas_checkbox.setStyleSheet("color: white; font-size: 14pt;")

        slider_row = QHBoxLayout()
        slider_row.addWidget(self.num_problems_label)
        slider_row.addWidget(self.show_formulas_checkbox)
        left_panel.addLayout(slider_row)
        left_panel.addWidget(self.num_problems_slider)

        self.new_quiz_btn = QPushButton("Take new quiz")
        self.new_quiz_btn.clicked.connect(self._start_new_quiz_with_slider)

        self.retake_btn = QPushButton("Retake selected quiz")
        self.retake_btn.clicked.connect(self._retake_selected)

        self.delete_btn = QPushButton("Delete selected quiz")
        self.delete_btn.clicked.connect(self._delete_selected)

        self.edit_btn = QPushButton("Edit questions")
        self.edit_btn.clicked.connect(self.edit_callback)

        # --- Stylings ---
        purple_button_style = """
            font-size: 14pt; padding: 10px; background-color: #8000c8; color: white;
            border-radius: 10px; border: none; font-weight: bold;
        """
        outline_purple_style = """
            font-size: 14pt; padding: 10px; background-color: transparent; color: #8000c8;
            border-radius: 10px; border: 2px solid #8000c8; font-weight: bold;
        """
        outline_white_style = """
            font-size: 14pt; padding: 10px; background-color: transparent; color: white;
            border-radius: 10px; border: 2px solid white; font-weight: bold;
        """

        self.new_quiz_btn.setStyleSheet(purple_button_style)
        self.retake_btn.setStyleSheet(outline_purple_style)
        self.delete_btn.setStyleSheet(outline_purple_style)
        self.edit_btn.setStyleSheet(outline_white_style)

        # --- Layout ---
        row1 = QHBoxLayout()
        row1.addWidget(self.new_quiz_btn)
        row1.addWidget(self.retake_btn)
        left_panel.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(self.delete_btn)
        row2.addWidget(self.edit_btn)
        left_panel.addLayout(row2)

        # === Right Container ===
        right_container = QWidget()
        right_container.setStyleSheet("background-color: black; border-radius: 15px;")
        right_panel = QVBoxLayout(right_container)
        right_panel.setContentsMargins(20, 20, 20, 20)
        right_panel.setSpacing(10)

        stats_header_layout = QHBoxLayout()

        stats_label = QLabel("Category Stats")
        stats_label.setStyleSheet("font-size: 24pt; color: white; background-color: black;")
        stats_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        username_label = QLabel(self.user.username)
        username_label.setStyleSheet("font-size: 14pt; color: #8000c8;")
        username_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.user_icon = QLabel(self.user.name[0].upper() if self.user.name else "?")
        self.user_icon.setFixedSize(40, 40)
        self.user_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_icon.setStyleSheet("""
            background-color: #8000c8;
            color: white;
            font-weight: bold;
            font-size: 18pt;
            border-radius: 20px;
        """)
        self.user_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        self.user_icon.mousePressEvent = lambda event: self.open_user_settings()

        stats_header_layout.addWidget(username_label)
        stats_header_layout.addWidget(self.user_icon)


        right_panel.addLayout(stats_header_layout)

        self.figure = Figure(facecolor='black')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(200)
        right_panel.addWidget(self.canvas)

        stats_and_grade_layout = QHBoxLayout()

        self.stats_display = QLabel()
        self.stats_display.setStyleSheet("color: white; font-size: 14pt;")
        self.stats_display.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stats_display.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        stats_and_grade_layout.addWidget(self.stats_display, stretch=2)

        self.grade_box = QLabel()
        self.grade_box.setFixedSize(120, 120)
        self.grade_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grade_box.setStyleSheet("""
            border: 2px solid white;
            color: white;
            font-size: 12pt;
            font-weight: bold;
        """)
        stats_and_grade_layout.addWidget(self.grade_box, alignment=Qt.AlignmentFlag.AlignTop)

        right_panel.addLayout(stats_and_grade_layout, stretch=1)

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

        main_layout.addLayout(layout)
        self.setLayout(main_layout)
        self.update_stats()


    def refresh_quiz_list(self):
        self.quiz_list.clear()

        sorted_quizzes = sorted(self.user.saved_quizzes, key=lambda q: q.date_taken, reverse=True)
        for idx, quiz in enumerate(sorted_quizzes):
            percent = round((sum(quiz.results) / len(quiz.results)) * 100) if quiz.results else 0
            quiz_date = quiz.date_taken.strftime("%d. %B %Y %H:%M") if hasattr(quiz, "date_taken") else "Unknown date"
            num_questions = len(quiz.results)

            # Container-widget for row
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(4, 2, 4, 2)

            label = QLabel(f"Quiz {idx + 1} ({percent}%, {quiz.grade}) - {quiz_date} ({num_questions} questions)")
            label.setStyleSheet("color: white; font-size: 14pt;")

            info_button = QPushButton("ⓘ")
            info_button.setStyleSheet("""
                QPushButton {
                    font-size: 16pt;
                    color: white;
                    background-color: transparent;
                    border: none;
                    padding-top: 0px;
                    padding-bottom: 15px;  /* hever knappens innhold litt */
                }
                QPushButton:hover {
                    color: #8000c8;
                }
            """)

            info_button.setFixedSize(32, 32)
            info_button.clicked.connect(lambda _, q=quiz: self._open_summary(q))

            layout.addWidget(label, stretch=1)
            layout.addWidget(info_button)

            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.quiz_list.addItem(item)
            self.quiz_list.setItemWidget(item, widget)


    def _update_slider_label(self, value):
        self.num_problems_label.setText(f"Number of questions: {value}")

    def _start_new_quiz_with_slider(self):
        num_questions = self.num_problems_slider.value()
        show_formulas = self.show_formulas_checkbox.isChecked()
        self.quiz_callback(num_questions, show_formulas)

    def _retake_selected(self):
        selected_items = self.quiz_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Select Quiz", "Please select a quiz to retake.")
            return
        index = self.quiz_list.currentRow()
        quiz = self.user.saved_quizzes[index]
        show_formulas = self.show_formulas_checkbox.isChecked()
        self.retake_callback(quiz, show_formulas)

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
        QApplication.quit()


    def open_user_settings(self):
        popup = UserSettingsPopup(self.user, self.user_db, self)
        popup.exec()

    def update_stats(self):
        genre_stats = defaultdict(lambda: {"correct": 0, "total": 0})

        try:
            with open("data/quizdata.pkl", "rb") as f:
                problems = pickle.load(f)
            pid_to_genre = {int(p.pid): str(p.genre) for p in problems}
        except Exception as e:
            self.stats_display.setText("Error loading quiz data.")
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
        html = "<table style='color:white; font-size:14pt;'>"
        for acc, label in results:
            html += f"<tr><td style='padding-right:30px;'>{label}</td><td>{acc}% accuracy</td></tr>"
        html += "</table>"
        self.stats_display.setText(html)

        # === Update Grade Box ===
        all_accuracies = [round(100 * sum(q.results) / len(q.results)) for q in self.user.saved_quizzes if q.results]
        avg_acc = round(sum(all_accuracies) / len(all_accuracies)) if all_accuracies else 0
        grade = 'F'
        for limit, g in sorted(GRADE_LIMITS.items(), reverse=True):
            if avg_acc >= limit:
                grade = g
                break
        self.grade_box.setText(f"<div style='font-size: 12pt;'>Current grade:</div><div style='font-size: 96pt;'>{grade}</div>")

        # === Plot quiz accuracy over time ===
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("black")
        if all_accuracies:
            ax.plot(range(1, len(all_accuracies) + 1), all_accuracies, color="white", marker="o", linestyle="-", linewidth=2)
            ax.set_xticks(range(1, len(all_accuracies) + 1))
            ax.set_ylim(0, 100)
            ax.set_xlabel("Quiz #", color="white")
            ax.set_ylabel("Accuracy (%)", color="white")
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
        self.canvas.draw()

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

    def _open_summary(self, quiz):
        self.summary_callback(quiz)

    def _return_from_summary(self):
        self.summary_window.close()
        self.show()