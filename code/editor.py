from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt
import pandas as pd

class QuestionEditor(QWidget):
    def __init__(self, quiz_file: str, return_callback):
        super().__init__()
        self.quiz_file = quiz_file
        self.return_callback = return_callback
        self.setWindowTitle("Edit Questions")
        self.setStyleSheet("background-color: black; color: white;")
        self.setMinimumSize(1100, 700)

        self.df = pd.read_csv(self.quiz_file, sep=';')
        self.selected_index = None

        layout = QHBoxLayout()

        # === Left side: list of questions ===
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

        #self.question_list.setStyleSheet("background-color: black; color: white; font-size: 12pt;")
        self.populate_question_list()
        self.question_list.itemClicked.connect(self.load_question_data)
        self.question_list.currentItemChanged.connect(self.load_question_data)


        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Questions:"))
        left_panel.addWidget(self.question_list)

        new_btn = QPushButton("Add new question")
        new_btn.clicked.connect(self.new_question)
        new_btn.setStyleSheet(self.button_style())
        left_panel.addWidget(new_btn)

        del_btn = QPushButton("Delete selected question")
        del_btn.clicked.connect(self.delete_question)
        del_btn.setStyleSheet(self.button_style())
        left_panel.addWidget(del_btn)

        # === Right side: edit form ===
        right_panel = QVBoxLayout()

        self.pid_label = QLabel("")
        self.pid_label.setStyleSheet("color: #8000c8; font-size: 12pt;")
        right_panel.addWidget(self.pid_label, alignment=Qt.AlignmentFlag.AlignRight)

        self.question_input = QTextEdit()
        self.formula_input = QLineEdit()
        self.alt_inputs = [QLineEdit() for _ in range(5)]
        self.alt_checks = [QCheckBox("Correct") for _ in range(5)]
        self.genre_dropdown = QComboBox()
        self.genre_dropdown.addItems([str(g) for g in sorted(self.df['_genre'].unique())])

        right_panel.addWidget(self.label_with_style("Question:"))
        right_panel.addWidget(self.styled_widget(self.question_input))

        right_panel.addWidget(self.label_with_style("Formula (optional):"))
        right_panel.addWidget(self.styled_widget(self.formula_input))

        for i in range(5):
            row = QHBoxLayout()
            row.addWidget(self.label_with_style(f"Alt {i+1}:"))
            row.addWidget(self.styled_widget(self.alt_inputs[i]))
            row.addWidget(self.alt_checks[i])
            right_panel.addLayout(row)

        right_panel.addWidget(self.label_with_style("Genre:"))
        right_panel.addWidget(self.genre_dropdown)

        save_btn = QPushButton("Save changes")
        save_btn.clicked.connect(self.save_question)
        save_btn.setStyleSheet(self.button_style())
        right_panel.addWidget(save_btn)

        back_btn = QPushButton("Return to Dashboard")
        back_btn.clicked.connect(self.return_callback)
        back_btn.setStyleSheet(self.button_style())
        right_panel.addWidget(back_btn)

        layout.addLayout(left_panel, 2)
        layout.addLayout(right_panel, 3)
        self.setLayout(layout)

    def button_style(self):
        return (
            "background-color: #8000c8; color: white; font-weight: bold; border-radius: 10px;"
            "padding: 8px 16px;"
        )

    def label_with_style(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 12pt; padding-bottom: 4px;")
        return label

    def styled_widget(self, widget):
        widget.setStyleSheet("border: 2px solid #bbbbbb; border-radius: 6px; padding: 4px;")
        return widget

    def populate_question_list(self):
        self.question_list.clear()
        for idx, row in self.df.iterrows():
            preview = row['_question'][:40] + ("..." if len(row['_question']) > 40 else "")
            item = QListWidgetItem(f"{row['_pid']} {row['_genre']}: \"{preview}\"")
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.question_list.addItem(item)

    def load_question_data(self, item, _=None):
        if item is None:
            return

        idx = item.data(Qt.ItemDataRole.UserRole)
        self.selected_index = idx
        row = self.df.loc[idx]

        self.question_input.setPlainText(row['_question'])
        self.formula_input.setText(str(row['_latex']) if pd.notna(row['_latex']) else "")
        for i in range(5):
            self.alt_inputs[i].setText(str(row[f'_alt{i+1}']))
            self.alt_checks[i].setChecked(row['_correct_alt'] == f'_alt{i+1}')
        self.genre_dropdown.setCurrentText(str(row['_genre']))
        self.pid_label.setText(f"Problem ID: {row['_pid']}")

    def new_question(self):
        self.selected_index = None
        self.question_input.clear()
        self.formula_input.clear()
        for i in range(5):
            self.alt_inputs[i].clear()
            self.alt_checks[i].setChecked(False)
        self.genre_dropdown.setCurrentIndex(0)
        self.pid_label.setText("")

    def delete_question(self):
        if self.selected_index is None:
            QMessageBox.warning(self, "No selection", "Select a question to delete.")
            return
        self.df = self.df.drop(index=self.selected_index).reset_index(drop=True)
        self.selected_index = None
        self.df.to_csv(self.quiz_file, sep=';', index=False)
        self.populate_question_list()
        self.new_question()

    def save_question(self):
        question = self.question_input.toPlainText()
        latex = self.formula_input.text().strip()
        alts = [alt.text() for alt in self.alt_inputs]
        correct_alt = None
        for i, chk in enumerate(self.alt_checks):
            if chk.isChecked():
                correct_alt = f'_alt{i+1}'

        if not question or not correct_alt or any(not alt for alt in alts):
            QMessageBox.warning(self, "Incomplete", "Please fill all alternatives and mark one as correct.")
            return

        genre = self.genre_dropdown.currentText()

        if self.selected_index is not None:
            pid = self.df.at[self.selected_index, '_pid']
        else:
            existing_ids = set(self.df['_pid'])
            pid = max(existing_ids) + 1 if existing_ids else 1

        row = {
            '_pid': pid,
            '_question': question,
            '_latex': latex if latex else "",
            '_alt1': alts[0],
            '_alt2': alts[1],
            '_alt3': alts[2],
            '_alt4': alts[3],
            '_alt5': alts[4],
            '_correct_alt': correct_alt,
            '_genre': genre
        }

        if self.selected_index is not None:
            for key, value in row.items():
                self.df.at[self.selected_index, key] = value
        else:
            self.df.loc[len(self.df)] = row

        self.df.to_csv(self.quiz_file, sep=';', index=False)
        self.populate_question_list()
        QMessageBox.information(self, "Saved", "Question saved successfully!")
