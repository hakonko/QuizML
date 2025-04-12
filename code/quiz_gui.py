from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QRadioButton, QButtonGroup, QMessageBox, QCheckBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
from code.quiz import Quiz
from code.userdata import User
from code import __version__
import random 
import time

LATIN_MODERN = "Latin Modern Roman"
GRADE_LIMITS = {90: 'A', 72: 'B', 62: 'C', 48: 'D', 38: 'E', 29: 'F'}

class QuizApp(QWidget):
    quiz_completed = pyqtSignal(object)

    def __init__(self, quiz: Quiz, user: User, show_formulas=True):
        super().__init__()

        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.95), int(screen.height() * 0.95))

        self.quiz = quiz
        self.current_idx = 0
        self.username = user.username
        self.user = user
        self.show_formulas = show_formulas

        self.current_shuffled_map = []  # indeks: posisjon på skjermen → opprinnelig indeks

        self.setWindowTitle("QuizML")
        self.setStyleSheet("background-color: white;")

        # === Layout setup ===
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # === Top status bar ===
        status_layout = QHBoxLayout()
        self.left_status = QLabel(f"QuizML {__version__}      User: {self.username}")
        self.right_status = QLabel("")
        self.left_status.setStyleSheet("color: #8000c8;")
        self.right_status.setStyleSheet("color: #8000c8;")
        status_layout.addWidget(self.left_status)
        status_layout.addStretch()
        status_layout.addWidget(self.right_status)
        main_layout.addLayout(status_layout)

        # === Main question area ===
        self.question_area = QVBoxLayout()
        self.question_view = QWebEngineView()
        self.formula_title = QLabel("Use the formula")
        self.formula_title.setStyleSheet("font-size: 14pt; color: #8000c8;")
        self.formula_title.setVisible(False)
        self.formula_view = QWebEngineView()
        self.image_view = QLabel()
        self.image_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_view.setStyleSheet("background-color: white;")

        self.question_area.addWidget(self.question_view)
        self.question_area.addWidget(self.formula_title)
        self.question_area.addWidget(self.formula_view)
        main_layout.addLayout(self.question_area, stretch=2)

        # === Answer section ===
        self.bottom_container = QWidget()
        self.bottom_container.setStyleSheet("background-color: white; border: 2px solid #8000c8; border-radius: 8px;")
        bottom_layout = QVBoxLayout(self.bottom_container)
        bottom_layout.setContentsMargins(20, 20, 20, 20)

        self.button_group = QButtonGroup()
        #self.radio_buttons = []
        #self.option_views = []

        # for i in range(5):
        #     row = QHBoxLayout()
        #     rb = QRadioButton()
        #     rb.setStyleSheet("color: black;")
        #     self.radio_buttons.append(rb)
        #     self.button_group.addButton(rb, i)

        #     view = QWebEngineView()
        #     view.setMinimumHeight(30)
        #     self.option_views.append(view)

        #     row.addWidget(rb)
        #     row.addWidget(view, stretch=1)
        #     bottom_layout.addLayout(row)
        self.answer_widgets = []

        for _ in range(5):
            row = QHBoxLayout()
            placeholder = QLabel()  # Dynamisk bytte senere
            view = QWebEngineView()
            view.setMinimumHeight(30)
            self.answer_widgets.append((placeholder, view, row))
            row.addWidget(placeholder)
            row.addWidget(view, stretch=1)
            bottom_layout.addLayout(row)

        self.submit_button = QPushButton("Submit Answer")
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

        self.problem_id_label = QLabel()
        self.problem_id_label.setStyleSheet("""
            QLabel {
                color: gray;
                font-size: 10pt;
                background-color: transparent;
                border: none;
            }
        """)

        # Leave button
        self.leave_button = QPushButton("← Dashboard")
        self.leave_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #cccccc;
                border: 2px solid #cccccc;
                font-weight: bold;
                border-radius: 10px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #f2f2f2;
            }
        """)
        self.leave_button.clicked.connect(self.leave_quiz)


        submit_layout = QHBoxLayout()
        submit_layout.addWidget(self.problem_id_label)
        submit_layout.addStretch()
        submit_layout.addWidget(self.leave_button)
        submit_layout.addWidget(self.submit_button)
        bottom_layout.addLayout(submit_layout)


        main_layout.addWidget(self.bottom_container, stretch=1)
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
                processed += part.replace("\n", "<br>")

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <style>
        html, body {{
            font-family: '{LATIN_MODERN}';
            font-size: 16pt;
            color: black;
            background-color: white;
            margin: 0;
            padding: 0;
            min-height: 100%;
            height: auto;
            box-sizing: border-box;
            display: block;
        }}
        mjx-container[jax="SVG"] {{
            vertical-align: middle !important;
            display: block !important;
            overflow: visible !important;
        }}
        </style>
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
        <body>
        {processed}
        </body>
        </html>
        """


    def load_problem(self):
        problem = self.quiz.get_problem(self.current_idx)
        is_multi = isinstance(problem.correct_alt, list)
        question_html = self.render_mathjax_html(problem.question)
        self.question_view.setHtml(question_html)

        # === Rydd opp i tidligere widgets/layouts ===
        for i in reversed(range(self.question_area.count())):
            item = self.question_area.itemAt(i)
            if item.widget() and item.widget() not in [self.question_view, self.formula_view, self.formula_title]:
                widget = item.widget()
                self.question_area.removeWidget(widget)
                widget.setParent(None)
            elif item.layout():
                layout = item.layout()
                while layout.count():
                    inner_item = layout.takeAt(0)
                    if inner_item.widget():
                        inner_item.widget().setParent(None)
                self.question_area.removeItem(layout)

        # === Shuffle alternativene ===
        original_alternatives = problem.alternatives
        indexed_alts = list(enumerate(original_alternatives))  # (original_index, text)
        random.shuffle(indexed_alts)
        self.current_shuffled_map = [idx for idx, _ in indexed_alts]  # ny rekkefølge

        # Fjern gamle knapper og views
        for i in reversed(range(self.bottom_container.layout().count() - 1)):
            item = self.bottom_container.layout().takeAt(i)
            if item.layout():
                while item.layout().count():
                    subitem = item.layout().takeAt(0)
                    if subitem.widget():
                        subitem.widget().deleteLater()
                item.layout().deleteLater()

        self.option_buttons = []
        self.option_views = []

        for idx, (original_idx, alt_text) in enumerate(indexed_alts):
            row = QHBoxLayout()

            if is_multi:
                btn = QCheckBox()
            else:
                btn = QRadioButton()
                btn.setAutoExclusive(True)

            btn.setStyleSheet("color: black;")
            self.option_buttons.append(btn)

            view = QWebEngineView()
            view.setMinimumHeight(40)
            view.setHtml(self.render_mathjax_html(alt_text))
            self.option_views.append(view)

            row.addWidget(btn)
            row.addWidget(view, stretch=1)
            self.bottom_container.layout().insertLayout(idx, row)


        # === Vis formel og bilde hvis det finnes ===
        show_formula = self.show_formulas and bool(problem.latex)
        self.formula_title.setVisible(show_formula)
        self.formula_view.setVisible(show_formula)
        if show_formula:
            self.formula_view.setHtml(self.render_mathjax_html(f"$$ {problem.latex} $$"))
        else:
            self.formula_view.setHtml("")


        if problem.image:
            image_path = Path("images") / problem.image
            if image_path.exists():
                pixmap = QPixmap(str(image_path)).scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
                image_label = QLabel()
                image_label.setPixmap(pixmap)
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                row_layout = QHBoxLayout()
                row_layout.addWidget(self.question_view, stretch=3)

                img_container = QWidget()
                img_layout = QVBoxLayout(img_container)
                img_layout.setContentsMargins(0, 0, 0, 0)
                img_layout.addWidget(image_label, alignment=Qt.AlignmentFlag.AlignTop)

                row_layout.addWidget(img_container, stretch=2)
                self.question_area.insertLayout(0, row_layout)
            else:
                self.formula_title.setVisible(bool(problem.latex))
        else:
            if not any(self.question_area.itemAt(i).widget() == self.question_view for i in range(self.question_area.count())):
                self.question_area.insertWidget(0, self.question_view)

        # === Oppdater statuslinje ===
        self.right_status.setText(f"Question {self.current_idx + 1} of {len(self.quiz.problems)}")
        self.problem_id_label.setText(f"pid: {problem.pid}")


    def submit_answer(self):
        problem = self.quiz.get_problem(self.current_idx)
        is_multi = isinstance(problem.correct_alt, list)

        # === Hent brukerens valgte svar ===
        selected_indices = [i for i, btn in enumerate(self.option_buttons) if btn.isChecked()]
        if not selected_indices:
            QMessageBox.warning(self, "No selection", "Please select at least one answer.")
            return

        correct_indices = []
        if is_multi:
            correct_indices = [
                self.current_shuffled_map.index(int(alt.replace("_alt", "")) - 1)
                for alt in problem.correct_alt
            ]
            # Poeng: +1 for hvert riktig, -1 for hvert feil, min 0
            correct_selected = len([i for i in selected_indices if i in correct_indices])
            incorrect_selected = len([i for i in selected_indices if i not in correct_indices])
            score = max(correct_selected - incorrect_selected, 0)
            was_correct = score > 0
        else:
            correct_index = int(problem.correct_alt.replace('_alt', '')) - 1
            correct_after_shuffle = self.current_shuffled_map.index(correct_index)
            score = 1 if selected_indices[0] == correct_after_shuffle else 0
            was_correct = score == 1

        # === Lagre resultat og brukerens svar ===
        self.quiz.results.append(was_correct)
        self.quiz.user_answers.append(selected_indices if is_multi else selected_indices[0])

        # === Lagre shufflet rekkefølge for senere oppsummering ===
        if not hasattr(self.quiz, "shuffled_maps"):
            self.quiz.shuffled_maps = []
        self.quiz.shuffled_maps.append(self.current_shuffled_map)

        # === Oppdater brukerstatistikk per spørsmål ===
        pid = problem.pid
        stats = self.user.question_stats.setdefault(pid, {"correct": 0, "wrong": 0, "last_timestamp": 0})
        if was_correct:
            stats['correct'] += 1
        else:
            stats['wrong'] += 1

        # === Neste spørsmål eller avslutt ===
        self.current_idx += 1
        if self.current_idx < len(self.quiz.problems):
            self.load_problem()
        else:
            self.quiz_completed.emit(self.quiz)
            self.close()
        stats['last_timestamp'] = time.time()

    def leave_quiz(self):  
        self.close()
        self.quiz_completed.emit(None)  # Signal til MainApp for å vise dashboard igjen


    def keyPressEvent(self, event):
        key = event.key()
        if Qt.Key.Key_1 <= key <= Qt.Key.Key_5:
            idx = key - Qt.Key.Key_1
            if idx < len(self.option_buttons):
                self.option_buttons[idx].setChecked(True)
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.submit_answer()
        elif key == Qt.Key.Key_Escape:
            self.leave_quiz()


