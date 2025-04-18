from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from pathlib import Path
from code.problem import Problem
import shutil
import pickle
import os
import pandas as pd


class QuestionEditor(QWidget):
    def __init__(self, return_callback, user, user_db):
        super().__init__()
        self.return_callback = return_callback
        self.user = user
        self.user_db = user_db

        self.setWindowTitle("Edit Questions")
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.95), int(screen.height() * 0.95))
        self.setStyleSheet("background-color: black; color: white;")

        self.pkl_path = self.user.current_question_set
        self.load_questions()

        self.selected_index = None
        self.image_filename = None

        layout = QHBoxLayout()

        # === Left panel ===
        self.question_list = QListWidget()
        self.question_list.setStyleSheet("""
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
        self.populate_question_list()
        self.question_list.currentItemChanged.connect(self.load_question_data)

        left_panel = QVBoxLayout()

        # --- Top bar with Return button ---
        top_row = QHBoxLayout()
        return_btn = QPushButton("← Return to Dashboard")
        return_btn.clicked.connect(self.return_callback)
        return_btn.setStyleSheet(self.black_button_style())
        return_btn.setFixedWidth(220)
        self.filename_label = QLabel("")
        self.filename_label.setStyleSheet("color: gray; font-size: 10pt;")
        top_row.addWidget(self.filename_label, alignment=Qt.AlignmentFlag.AlignRight)
        self.update_filename_label()

        top_row.addWidget(return_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        top_row.addStretch()
        left_panel.addLayout(top_row)

        header_row = QHBoxLayout()
        questions_label = QLabel("Questions")
        questions_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: white;")
        accuracy_label = QLabel("User Accuracy")
        accuracy_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: white;")
        header_row.addWidget(questions_label)
        header_row.addStretch()
        header_row.addWidget(accuracy_label)
        left_panel.addLayout(header_row)
        left_panel.addWidget(self.question_list)

        del_btn = QPushButton("Delete Selected")
        del_btn.clicked.connect(self.delete_question)
        del_btn.setStyleSheet(self.black_button_style())
        del_btn.setFixedWidth(180)

        change_set_btn = QPushButton("Change Set")
        change_set_btn.clicked.connect(self.change_set)
        change_set_btn.setStyleSheet(self.black_button_style())
        change_set_btn.setFixedWidth(180)

        import_btn = QPushButton("Import from CSV")
        import_btn.clicked.connect(self.import_from_csv)
        import_btn.setStyleSheet("""
            background-color: white;
            color: black;
            font-weight: bold;
            border-radius: 10px;
            border: 2px solid black;
            padding: 8px 16px;
        """)
        import_btn.setFixedWidth(180)

        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_to_csv)
        export_btn.setStyleSheet("""
            background-color: white;
            color: black;
            font-weight: bold;
            border-radius: 10px;
            border: 2px solid black;
            padding: 8px 16px;
        """)
        export_btn.setFixedWidth(180)

        btn_row_left = QHBoxLayout()
        btn_row_left.addWidget(return_btn)
        btn_row_left.addWidget(change_set_btn)
        btn_row_left.addWidget(import_btn)
        btn_row_left.addWidget(export_btn)
        btn_row_left.addWidget(del_btn)
        left_panel.addLayout(btn_row_left)

        # === Right panel ===
        right_panel = QVBoxLayout()
        form_container = QWidget()
        form_container.setStyleSheet("""
            background-color: white;
            color: black;
            border-radius: 10px;

            QLineEdit, QTextEdit, QComboBox, QCheckBox {
                border: 1px solid gray;
                border-radius: 6px;
                padding: 6px;
                font-size: 12pt;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }

            QCheckBox {
                spacing: 8px;
            }
        """)

        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)

        self.pid_label = QLabel("")
        self.pid_label.setStyleSheet("color: #8000c8; font-size: 12pt;")
        form_layout.addWidget(self.pid_label, alignment=Qt.AlignmentFlag.AlignRight)

        self.question_input = QTextEdit()
        self.question_input.setStyleSheet("border: 1px solid gray; border-radius: 6px; padding: 6px; font-size: 12pt;")

        self.formula_input = QLineEdit()
        self.formula_input.setStyleSheet("border: 1px solid gray; border-radius: 6px; padding: 6px; font-size: 12pt;")

        self.alt_inputs = []
        self.alt_checks = []
        for _ in range(5):
            alt_input = QLineEdit()
            alt_input.setStyleSheet("border: 1px solid gray; border-radius: 6px; padding: 6px; font-size: 12pt;")

            alt_check = QCheckBox("Correct")

            self.alt_inputs.append(alt_input)
            self.alt_checks.append(alt_check)

        self.genre_dropdown = QComboBox()
        self.genre_dropdown.setStyleSheet("border: 1px solid gray; border-radius: 6px; padding: 6px; font-size: 12pt;")

        self.genre_dropdown.setEditable(True)
        self.genre_dropdown.lineEdit().setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.genre_dropdown.setEditable(False)

        genres = sorted(set(p.genre for p in self.problems))
        self.genre_dropdown.addItems(genres)

        form_layout.addWidget(self.label("Question:"))
        form_layout.addWidget(self.question_input)
        form_layout.addWidget(self.label("Formula (optional):"))
        form_layout.addWidget(self.formula_input)

        for i in range(5):
            row = QHBoxLayout()
            row.addWidget(self.label(f"Alt {i+1}:"))
            row.addWidget(self.alt_inputs[i])
            row.addWidget(self.alt_checks[i])
            form_layout.addLayout(row)

        genre_row = QHBoxLayout()
        genre_row.addWidget(self.label("Genre:"))
        genre_row.addWidget(self.genre_dropdown, stretch=1)

        add_image_btn = QPushButton("Add Image")
        add_image_btn.clicked.connect(self.select_image_file)
        add_image_btn.setFixedWidth(180)
        add_image_btn.setStyleSheet("""
            background-color: white;
            color: black;
            font-weight: bold;
            border-radius: 8px;
            border: 2px solid black;
            padding: 6px 12px;
        """)
        genre_row.addWidget(add_image_btn)
        form_layout.addLayout(genre_row)

        add_btn = QPushButton("Add New Problem")
        add_btn.clicked.connect(self.new_question)
        add_btn.setStyleSheet(self.button_style())
        add_btn.setFixedWidth(180)

        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_question)
        save_btn.setStyleSheet(self.button_style())
        save_btn.setFixedWidth(180)

        btn_row = QHBoxLayout()
        btn_row.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        btn_row.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)
        form_layout.addLayout(btn_row)

        right_panel.addWidget(form_container)
        layout.addLayout(left_panel, 2)
        layout.addLayout(right_panel, 3)
        self.setLayout(layout)

        QTimer.singleShot(0, self.select_first_item)

    def load_questions(self):
        try:
            with open(self.pkl_path, "rb") as f:
                data = pickle.load(f)

            # Sjekk at det er en liste av `Problem`-objekter
            if not isinstance(data, list) or not all(hasattr(p, "question") and hasattr(p, "alternatives") for p in data):
                raise ValueError("Wrong file type")

            self.problems = data

        except Exception as e:
            QMessageBox.critical(self, "Error loading file", f"Could not load file:\n{self.pkl_path}\n\nReason: {str(e)}")
            self.problems = []
            self.pkl_path = "data/quizdata.pkl"
            self.user.current_question_set = self.pkl_path
            self.user_db.save()

    def save_questions(self):
        with open(self.pkl_path, "wb") as f:
            pickle.dump(self.problems, f)

    def label(self, text):
        l = QLabel(text)
        l.setStyleSheet("font-size: 12pt; padding-bottom: 4px;")
        return l

    def button_style(self):
        return "background-color: #8000c8; color: white; font-weight: bold; border-radius: 10px; padding: 8px 16px;"

    def black_button_style(self):
        return "background-color: black; color: white; font-weight: bold; border-radius: 10px; border: 2px solid white; padding: 8px 16px;"

    def populate_question_list(self):
        self.question_list.clear()
        for i, p in enumerate(self.problems):
            preview = p.question[:40] + ("..." if len(p.question) > 40 else "")
            
            # Legg til accuracy
            stats = self.user.question_stats.get(p.pid, {"correct": 0, "wrong": 0})
            correct = stats.get("correct", 0)
            wrong = stats.get("wrong", 0)
            total = correct + wrong
            
            if total > 0:
                accuracy = correct / total
                accuracy_str = f"{accuracy:.0%}"  # viser accuracy som prosent
            else:
                accuracy_str = "N/A"
            
            item_text = f"{p.pid} {p.genre}: \"{preview}\" | Accuracy: {accuracy_str}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.question_list.addItem(item)


    def select_first_item(self):
        if self.question_list.count() > 0:
            item = self.question_list.item(0)
            self.question_list.setCurrentItem(item)

    def load_question_data(self, item):
        if item is None:
            return
        idx = item.data(Qt.ItemDataRole.UserRole)
        self.selected_index = idx
        p = self.problems[idx]
        self.question_input.setPlainText(p.question)
        self.formula_input.setText(str(p.latex) if isinstance(p.latex, str) else "")
        corrects = p.correct_alt if isinstance(p.correct_alt, list) else [p.correct_alt]
        for i in range(5):
            self.alt_inputs[i].setText(p.alternatives[i])
            self.alt_checks[i].setChecked(f"_alt{i+1}" in corrects)
        # for i in range(5):
        #     self.alt_inputs[i].setText(p.alternatives[i])
        #     self.alt_checks[i].setChecked(p.correct_alt == f"_alt{i+1}")
        self.genre_dropdown.setCurrentText(p.genre)
        self.pid_label.setText(f"Problem ID: {p.pid}")
        self.image_filename = p.image

    def new_question(self):
        self.selected_index = None
        self.question_input.clear()
        self.formula_input.clear()
        for i in range(5):
            self.alt_inputs[i].clear()
            self.alt_checks[i].setChecked(False)
        self.genre_dropdown.setCurrentIndex(0)
        self.image_filename = None
        self.pid_label.setText("")

    def delete_question(self):
        if self.selected_index is None:
            QMessageBox.warning(self, "No selection", "Select a question to delete.")
            return
        del self.problems[self.selected_index]
        self.save_questions()
        self.populate_question_list()
        self.new_question()

    def select_image_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            img_name = Path(file_path).name
            dest = Path("images") / img_name
            dest.parent.mkdir(exist_ok=True)
            shutil.copy(file_path, dest)
            self.image_filename = img_name

    def save_question(self):
        question = self.question_input.toPlainText().strip()
        latex = self.formula_input.text().strip()
        alts = [a.text().strip() for a in self.alt_inputs]
        correct_alt = [f"_alt{i+1}" for i, check in enumerate(self.alt_checks) if check.isChecked()]

        if not question or not correct_alt or any(not a for a in alts):
            QMessageBox.warning(self, "Incomplete", "Please fill all alternatives and mark one as correct.")
            return

        genre = self.genre_dropdown.currentText()
        is_new = self.selected_index is None
        pid = self.problems[self.selected_index].pid if not is_new else max((p.pid for p in self.problems), default=0) + 1

        new_problem = Problem(pid, question, latex, alts, correct_alt, genre, self.image_filename)

        if not is_new:
            self.problems[self.selected_index] = new_problem
        else:
            self.problems.append(new_problem)

        self.save_questions()
        self.populate_question_list()

        if is_new:
            self.selected_index = len(self.problems) - 1
            self.select_first_item()

        QMessageBox.information(self, "Saved", "Question saved successfully!")


    def import_from_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Questions", "", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            df = pd.read_csv(file_path, sep=';')
            imported = []
            for _, row in df.iterrows():
                alts = [row[f"_alt{i+1}"] for i in range(5)]
                correct_alt = row["_correct_alt"]
                if isinstance(correct_alt, str) and "," in correct_alt:
                    correct_alt = correct_alt.split(",")
                problem = Problem(
                    pid=row["_pid"],
                    question=row["_question"],
                    latex=row.get("_latex", ""),
                    alternatives=alts,
                    correct_alt=correct_alt,
                    genre=row["_genre"],
                    image=row.get("_image", None)
                )
                imported.append(problem)
            self.problems += imported
            self.save_questions()
            self.populate_question_list()
            QMessageBox.information(self, "Import complete", f"Imported {len(imported)} problems.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {e}")

    def export_to_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Questions", "", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            data = []
            for p in self.problems:
                correct_alt = p.correct_alt
                if isinstance(correct_alt, list):
                    correct_alt = ",".join(correct_alt)
                row = {
                    "_pid": p.pid,
                    "_question": p.question,
                    "_latex": p.latex,
                    "_correct_alt": correct_alt,
                    "_genre": p.genre,
                    "_image": p.image or ""
                }
                for i, alt in enumerate(p.alternatives):
                    row[f"_alt{i+1}"] = alt
                data.append(row)

            df = pd.DataFrame(data)
            df.to_csv(file_path, sep=';', index=False)
            QMessageBox.information(self, "Export complete", f"Exported {len(data)} problems to CSV.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {e}")

    def update_filename_label(self):
        if hasattr(self, "current_file_label"):
            self.current_file_label.setText(self.pkl_path)


    def change_set(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Change Question Set")
        msg_box.setText("Choose how to load a new set of questions:")
        load_btn = msg_box.addButton("Load Existing", QMessageBox.ButtonRole.AcceptRole)
        new_btn = msg_box.addButton("Start From Blank", QMessageBox.ButtonRole.DestructiveRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

        msg_box.exec()

        if msg_box.clickedButton() == load_btn:
            file_path, _ = QFileDialog.getOpenFileName(self, "Load Questions", "", "Pickle Files (*.pkl)")
            if file_path:
                self.pkl_path = file_path
                self.user.current_question_set = file_path
                self.user_db.save()
                self.update_filename_label()
                self.load_questions()
                self.populate_question_list()
                self.new_question()

        elif msg_box.clickedButton() == new_btn:
            file_path, _ = QFileDialog.getSaveFileName(self, "Create New Question Set", "", "Pickle Files (*.pkl)")
            if file_path:
                self.pkl_path = file_path
                self.user.current_question_set = file_path
                self.user_db.save()
                self.update_filename_label()
                self.problems = []
                self.save_questions()
                self.populate_question_list()
                self.new_question()


