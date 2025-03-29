import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QRadioButton, QButtonGroup, QMessageBox, QFrame
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, pyqtSignal
from code.quiz import Quiz
from code.userdata import User

NUM_VERSION = "0.31"
LATIN_MODERN = "Latin Modern Roman"
SANS_SERIF = "Roboto"
GRADE_LIMITS = {90: 'A', 72: 'B', 62: 'C', 48: 'D', 38: 'E', 29: 'F'}

class QuizApp(QWidget):
    quiz_completed = pyqtSignal(object)

    def __init__(self, quiz: Quiz, user: User):
        super().__init__()
        self.quiz = quiz
        self.current_idx = 0
        self.username = user.username
        self.user = user

        self.setWindowTitle("QuizML")
        self.setGeometry(100, 100, 1100, 700)
        self.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        status_layout = QHBoxLayout()
        question_layout = QVBoxLayout()

        self.left_status = QLabel(f"QuizML {NUM_VERSION}      User: {self.username}")
        self.right_status = QLabel("")
        self.left_status.setStyleSheet("background-color: white; color: black;")
        self.right_status.setStyleSheet("background-color: white; color: black;")
        status_layout.addWidget(self.left_status)
        status_layout.addStretch()
        status_layout.addWidget(self.right_status)

        self.question_view = QWebEngineView()
        self.question_view.setMinimumHeight(120)
        question_layout.addWidget(self.question_view)

        self.formula_title = QLabel("Use the formula")
        self.formula_title.setStyleSheet("font-size: 14pt; color: black; padding-left: 10px;")
        self.formula_title.setVisible(False)
        question_layout.addWidget(self.formula_title)

        self.formula_view = QWebEngineView()
        self.formula_view.setMinimumHeight(100)
        question_layout.addWidget(self.formula_view)

        self.bottom_container = QWidget()
        self.bottom_container.setStyleSheet("background-color: white; border: 2px solid #8000c8; border-radius: 8px;")
        bottom_layout = QVBoxLayout(self.bottom_container)
        bottom_layout.setContentsMargins(20, 20, 20, 20)
        bottom_layout.setSpacing(10)

        self.button_group = QButtonGroup()
        self.radio_buttons = []
        self.option_views = []

        for i in range(5):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(5)

            rb = QRadioButton()
            rb.setStyleSheet("color: black;")
            self.radio_buttons.append(rb)
            self.button_group.addButton(rb, i)

            view = QWebEngineView()
            view.setMinimumHeight(30)
            self.option_views.append(view)

            row.addWidget(rb)
            row.addWidget(view, stretch=1)
            bottom_layout.addLayout(row)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_answer)
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #8000c8;
                font-weight: bold;
                border-radius: 10px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #f2f2f2;
            }
        """)

        submit_layout = QHBoxLayout()
        submit_layout.addStretch()
        submit_layout.addWidget(self.submit_button)
        bottom_layout.addLayout(submit_layout)

        main_layout.addLayout(status_layout)
        main_layout.addLayout(question_layout)
        main_layout.addWidget(self.bottom_container)
        self.setLayout(main_layout)

        self.load_problem()

    def render_mathjax_html(self, content):
        import html
        import re

        if not isinstance(content, str):
            content = str(content)

        parts = re.split(r"(\$.*?\$)", content)
        processed = ""
        for part in parts:
            if part.startswith("$") and part.endswith("$"):
                processed += part
            else:
                processed += html.escape(part)

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <script src='https://polyfill.io/v3/polyfill.min.js?features=es6'></script>
        <script>
            window.MathJax = {{
            tex: {{ inlineMath: [['$','$']] }},
            svg: {{ fontCache: 'global' }}
            }};
        </script>
        <script type='text/javascript' id='MathJax-script' async
            src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'>
        </script>
        </head>
        <body style='font-family:{LATIN_MODERN}; font-size: 16pt; color: black; background-color: white;'>
        {processed}
        </body>
        </html>
        """

    def load_problem(self):
        problem = self.quiz.get_problem(self.current_idx)
        question_html = self.render_mathjax_html(problem.question)
        self.question_view.setHtml(question_html)

        self.button_group.setExclusive(False)
        for rb in self.radio_buttons:
            rb.setChecked(False)
        self.button_group.setExclusive(True)

        for idx, alt in enumerate(problem.alts):
            alt_html = self.render_mathjax_html(alt)
            self.option_views[idx].setHtml(alt_html)

        if problem.latex:
            self.formula_title.setVisible(True)
            self.formula_view.setHtml(self.render_mathjax_html(f"$$ {problem.latex} $$"))
        else:
            self.formula_title.setVisible(False)
            self.formula_view.setHtml("")

        total = len(self.quiz.problems)
        current = self.current_idx + 1
        self.right_status.setText(f"Question {current} of {total}")

    def submit_answer(self):
        selected_id = self.button_group.checkedId()
        if selected_id == -1:
            QMessageBox.warning(self, "No selection", "Please select an answer.")
            return

        problem = self.quiz.get_problem(self.current_idx)
        correct_idx = int(problem.correct_alt.replace('_alt', '')) - 1

        self.quiz.results.append(selected_id == correct_idx)
        pid = problem.pid
        if pid not in self.user.question_stats:
            self.user.question_stats[pid] = {"correct": 0, "wrong": 0}

        if selected_id == correct_idx:
            self.user.question_stats[pid]['correct'] += 1
        else:
            self.user.question_stats[pid]['wrong'] += 1

        self.current_idx += 1
        if self.current_idx < len(self.quiz.problems):
            self.load_problem()
        else:
            self.show_final_result()

    def show_final_result(self):
        correct_answers = sum(self.quiz.results)
        total = len(self.quiz.results)
        percent = round((correct_answers / total) * 100)

        for limit, grade in sorted(GRADE_LIMITS.items(), reverse=True):
            if percent >= limit:
                self.quiz.grade = grade
                break

        msg = QMessageBox(self)
        msg.setWindowTitle("Quiz Complete")
        msg.setText(f"You got {correct_answers} out of {total} correct ({percent}%). Grade: {self.quiz.grade}")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)

        msg.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 14pt;
            }
            QMessageBox {
                background-color: white;
            }
            QPushButton {
                background-color: #8000c8;
                color: white;
                padding: 6px 12px;
                border-radius: 8px;
                font-weight: bold;
            }
        """)

        msg.exec()

        self.quiz_completed.emit(self.quiz)
        self.close()

    def keyPressEvent(self, event):
        key = event.key()

        if Qt.Key.Key_1 <= key <= Qt.Key.Key_5:
            idx = key - Qt.Key.Key_1
            if idx < len(self.radio_buttons):
                self.radio_buttons[idx].setChecked(True)

        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.submit_answer()

