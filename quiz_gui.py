import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from code.quiz import Quiz

from matplotlib import pyplot as plt
from PIL import Image, ImageTk
import io

class QuizApp:
    def __init__(self, master, quiz: Quiz):
        self.master = master
        self.quiz = quiz
        self.current_idx = 0
        self.selected_answer = tk.StringVar()
        self.results = []
        self.latex_image = None  # for å holde referansen til bildet

        self.master.title("IN3310 Pensum Quiz")
        self.master.geometry("800x600")


        # Upper frame
        top_frame = tk.Frame(master, bg="white")
        top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.question_frame = tk.Frame(top_frame, width=400, height=150, bg="white")
        self.question_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.formula_frame = tk.Frame(top_frame, width=200, height=150, bg="white")
        self.formula_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.question_label = tk.Label(self.question_frame, text="", wraplength=380,
                                       justify="left", bg="white", fg="black", font=("Helvetica", 16))
        self.question_label.pack(padx=10, pady=10, anchor="nw")

        self.formula_title = tk.Label(self.formula_frame, text="", font=("Helvetica", 16),
                              bg="white", fg="black", anchor="w", justify="left")
        
        self.formula_title.pack(padx=10, pady=(10, 0), anchor="nw")

        self.formula_label = tk.Label(self.formula_frame, bg="white")
        self.formula_label.pack(padx=10, pady=(5, 10), anchor="nw")



        # Lower frame
        bottom_frame = tk.Frame(master)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.options_frame = tk.Frame(bottom_frame)
        self.options_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.button_frame = tk.Frame(bottom_frame)
        self.button_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.radio_buttons = []

        for i in range(5):
            rb = tk.Radiobutton(self.options_frame, text="", variable=self.selected_answer,
                                value=str(i), font=("Helvetica", 16))
            rb.pack(anchor="w", padx=10, pady=2)
            self.radio_buttons.append(rb)

        self.submit_button = tk.Button(self.button_frame, text="Submit", command=self.submit_answer)
        self.submit_button.pack(pady=20)

        self.load_problem()

    def clean_latex_string(self, latex_str):
        if not latex_str:
            return ""

        latex_str = latex_str.strip()

        # Fjern alle ytre dollartegn
        while latex_str.startswith("$"):
            latex_str = latex_str[1:]
        while latex_str.endswith("$"):
            latex_str = latex_str[:-1]

        return latex_str


    def render_latex(self, latex_str):
        latex_str = self.clean_latex_string(latex_str)
        if not latex_str:
            return None

        plt.rc('mathtext', fontset='stix')  # <- Dette gir stilig serif-font
        plt.rc('font', family='serif', size=13)

        plt.clf()
        fig = plt.figure(figsize=(0.01, 0.01))
        text = fig.text(0, 0, f"${latex_str}$", fontsize=13)
        fig.canvas.draw()

        bbox = text.get_window_extent()
        width, height = bbox.size
        width = int(width)
        height = int(height)

        fig.set_size_inches(width / fig.dpi, height / fig.dpi)
        fig.canvas.draw()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=fig.dpi, bbox_inches='tight', transparent=True)
        plt.close(fig)

        buf.seek(0)
        img = Image.open(buf)
        return ImageTk.PhotoImage(img)

    def load_problem(self):
        problem = self.quiz.get_problem(self.current_idx)
        self.question_label.config(text=problem.question)
        self.selected_answer.set(None)

        for idx, alt in enumerate(problem.alts):
            self.radio_buttons[idx].config(text=alt, value=str(idx))

        # Render LaTeX if present
        if problem.latex:
            self.formula_title.config(text="Use this formula:")
            self.latex_image = self.render_latex(problem.latex)
            self.formula_label.config(image=self.latex_image)
        else:
            self.formula_title.config(text="")
            self.formula_label.config(image='')


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
      # sørg for at denne klassen er definert riktig
    NUM_PROBLEMS = 3
    BASE_DIR = Path.cwd().parent
    USER_FILE = BASE_DIR / 'users' / 'users.csv'
    QUIZ_FILE = BASE_DIR / 'quiz' / 'quiz_3310.csv'

    quiz1 = Quiz(NUM_PROBLEMS, USER_FILE, QUIZ_FILE)

    root = tk.Tk()
    app = QuizApp(root, quiz1)
    root.mainloop()

