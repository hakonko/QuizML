from tkinter import messagebox
from pathlib import Path
from code.quiz import Quiz
from matplotlib import pyplot as plt
from PIL import Image, ImageTk
import customtkinter as ctk
import io

LATIN_MODERN = "Latin Modern Roman"
SANS_SERIF = "Roboto"

class QuizApp:
    def __init__(self, master, quiz: Quiz):
        self.master = master
        self.quiz = quiz
        self.current_idx = 0
        self.selected_answer = ctk.StringVar()
        self.results = []
        self.latex_image = None

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        self.master.geometry(f"{int(screen_width * 0.9)}x{int(screen_height * 0.9)}")
        self.master.title("QuizML")

        # Statusbar
        self.status_bar = ctk.CTkFrame(master, fg_color="#7F00FF", height=20)
        self.status_bar.pack(side="top", fill="x")

        self.left_status = ctk.CTkLabel(self.status_bar, text="QuizML 0.1      User: Test User",
                                        text_color="white", font=ctk.CTkFont(family=SANS_SERIF, size=16))
        self.left_status.pack(side="left", padx=10)

        self.right_status = ctk.CTkLabel(self.status_bar, text="",
                                         text_color="white", font=ctk.CTkFont(family=SANS_SERIF, size=16))
        self.right_status.pack(side="right", padx=10)

        # Top frame for question and formula
        top_frame = ctk.CTkFrame(master, fg_color="white")
        top_frame.pack(side="top", fill="both", expand=True)

        self.question_frame = ctk.CTkFrame(top_frame, fg_color="white", width=400, height=150)
        self.question_frame.pack(side="left", fill="both", expand=True)

        self.question_canvas = ctk.CTkCanvas(self.question_frame, bg="white", highlightthickness=0)
        self.scrollbar = ctk.CTkScrollbar(self.question_frame, command=self.question_canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(self.question_canvas, fg_color="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.question_canvas.configure(
                scrollregion=self.question_canvas.bbox("all")
            )
        )

        self.question_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.question_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.question_canvas.bind("<Configure>", lambda e: self._toggle_scrollbar())

        self.question_canvas.pack(side="left", fill="both", expand=True)
        # Only show scrollbar when needed
        if self.question_canvas.bbox("all")[3] > self.question_canvas.winfo_height():
            self.scrollbar.pack(side="right", fill="y")
        else:
            self.scrollbar.pack_forget()

        self.question_label = ctk.CTkLabel(self.scrollable_frame, text="", font=ctk.CTkFont(family=LATIN_MODERN, size=20),
                                           text_color="black", anchor="w", wraplength=380, justify="left")
        self.question_label.pack(padx=10, pady=10, anchor="nw")

        self.formula_frame = ctk.CTkFrame(top_frame, fg_color="white", width=200, height=150)
        self.formula_frame.pack(side="right", fill="both", expand=True)

        self.formula_title = ctk.CTkLabel(self.formula_frame, text="", font=ctk.CTkFont(family=LATIN_MODERN, size=20),
                                          text_color="black", anchor="w")
        self.formula_title.pack(padx=10, pady=(10, 0), anchor="nw")

        self.formula_label = ctk.CTkLabel(self.formula_frame, text="")
        self.formula_label.pack(padx=10, pady=(5, 10), anchor="nw")

        # Bottom frame for options and submit
        bottom_frame = ctk.CTkFrame(master, fg_color="black")
        bottom_frame.pack(side="bottom", fill="both", expand=True)

        self.options_frame = ctk.CTkFrame(bottom_frame, fg_color="black")
        self.options_frame.pack(side="left", fill="both", expand=True, pady=20)

        self.button_frame = ctk.CTkFrame(bottom_frame, fg_color="black")
        self.button_frame.pack(side="right", fill="both", expand=True, pady=20)

        self.radio_buttons = []
        for i in range(5):
            rb = ctk.CTkRadioButton(self.options_frame, text="", variable=self.selected_answer,
                                     font=ctk.CTkFont(family=LATIN_MODERN, size=16), text_color="white")
            rb._value = str(i)
            rb.pack(anchor="w", padx=10, pady=10)
            self.radio_buttons.append(rb)

        self.submit_button = ctk.CTkButton(self.button_frame, text="Submit",
                                           command=self.submit_answer,
                                           fg_color="black",
                                           text_color="white",
                                           hover_color="#8000c8",
                                           corner_radius=10,
                                           border_width=2,
                                           border_color="white",
                                           font=ctk.CTkFont(family=SANS_SERIF, size=16))
        self.submit_button.pack(padx=30, pady=30, anchor="e")

        self.load_problem()

    def _toggle_scrollbar(self):
        self.master.after(100, lambda: (
            self.scrollbar.pack(side="right", fill="y")
            if self.question_canvas.bbox("all")[3] > self.question_canvas.winfo_height()
            else self.scrollbar.pack_forget()
        ))

    def clean_latex_string(self, latex_str):
        if not latex_str:
            return ""
        latex_str = latex_str.strip()
        while latex_str.startswith("$"):
            latex_str = latex_str[1:]
        while latex_str.endswith("$"):
            latex_str = latex_str[:-1]
        return latex_str

    def render_latex(self, latex_str):
        latex_str = self.clean_latex_string(latex_str)
        if not latex_str:
            return None
        plt.rc('mathtext', fontset='stix')
        plt.rc('font', family='serif', size=13)
        plt.clf()
        fig = plt.figure(figsize=(0.01, 0.01))
        text = fig.text(0, 0, f"${latex_str}$", fontsize=13)
        fig.canvas.draw()
        bbox = text.get_window_extent()
        width, height = int(bbox.width), int(bbox.height)
        fig.set_size_inches(width / fig.dpi, height / fig.dpi)
        fig.canvas.draw()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=fig.dpi, bbox_inches='tight', transparent=True)
        plt.close(fig)
        buf.seek(0)
        img = Image.open(buf)
        return ctk.CTkImage(light_image=img, size=img.size)

    def load_problem(self):
        problem = self.quiz.get_problem(self.current_idx)
        self.question_label.configure(text=problem.question)
        self.selected_answer.set(None)
        for idx, alt in enumerate(problem.alts):
            self.radio_buttons[idx].configure(text=alt)
        if problem.latex:
            self.formula_title.configure(text="Use this formula:")
            self.latex_image = self.render_latex(problem.latex)
            self.formula_label.configure(image=self.latex_image, text="")
        else:
            self.formula_title.configure(text="")
            self.formula_label.configure(image=None, text="")
        total = len(self.quiz.problems)
        current = self.current_idx + 1
        self.right_status.configure(text=f"Question {current} of {total}")

    def submit_answer(self):
        selected = self.selected_answer.get()
        if selected == "":
            messagebox.showwarning("No selection", "Please select an answer.")
            return
        problem = self.quiz.get_problem(self.current_idx)
        correct_idx = int(problem.correct_alt.replace('_alt', '')) - 1
        self.results.append(int(selected) == correct_idx)
        self.current_idx += 1
        if self.current_idx < len(self.quiz.problems):
            self.load_problem()
        else:
            self.show_final_result()

    def show_final_result(self):
        correct_answers = sum(self.results)
        total = len(self.results)
        percent = round((correct_answers / total) * 100)
        messagebox.showinfo("Quiz Complete", f"You got {correct_answers} out of {total} correct ({percent}%).")
        self.master.quit()


if __name__ == "__main__":
    NUM_PROBLEMS = 20
    BASE_DIR = Path.cwd()
    USER_FILE = BASE_DIR / 'users' / 'users.csv'
    QUIZ_FILE = BASE_DIR / 'quiz' / 'quiz_3310.csv'

    quiz1 = Quiz(NUM_PROBLEMS, USER_FILE, QUIZ_FILE)
    app_root = ctk.CTk()
    app = QuizApp(app_root, quiz1)
    app_root.mainloop()
