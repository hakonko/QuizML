import pandas as pd
import random
import pickle
from code.problem import Problem
from datetime import datetime

class Quiz:
    def __init__(self, num_problems, user_file=None, quiz_file=None, user=None):
        self.num_problems = num_problems
        self.user_file = user_file
        self.quiz_file = quiz_file
        self.user = user
        self.genres = None
        self.problems = []
        self.results = []
        self.user_answers = []
        self.date_taken = datetime.now()
        self.grade = None

        self._create_quiz()

    def _create_quiz(self):
        try:
            with open("data/quizdata.pkl", "rb") as f:
                all_problems = pickle.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load quizdata.pkl: {e}")

        # Get all genres
        self.genres = list({p.genre for p in all_problems})
        random.shuffle(self.genres)

        genre_counts = {genre: 1 for genre in self.genres}
        remaining = self.num_problems - len(self.genres)

        while remaining > 0:
            for genre in self.genres:
                if remaining == 0:
                    break
                genre_counts[genre] += 1
                remaining -= 1

        self.problems = []

        def get_error_rate(pid):
            stats = self.user.question_stats.get(pid, {"correct": 0, "wrong": 0})
            total = stats["correct"] + stats["wrong"]
            return (stats["wrong"] / total) if total > 0 else 0.5

        used_pids = set()
        for genre in self.genres:
            genre_problems = [p for p in all_problems if p.genre == genre and p.pid not in used_pids]
            n = min(len(genre_problems), genre_counts[genre])
            genre_problems.sort(key=lambda p: get_error_rate(p.pid), reverse=True)
            selected = genre_problems[:n]
            used_pids.update(p.pid for p in selected)
            self.problems.extend(selected)

        # Fill up with more problems
        if len(self.problems) < self.num_problems:
            remaining_problems = [p for p in all_problems if p.pid not in used_pids]
            remaining_problems.sort(key=lambda p: get_error_rate(p.pid), reverse=True)
            self.problems.extend(remaining_problems[:self.num_problems - len(self.problems)])

    def __str__(self):
        return f'IN3310-Quiz. Number of questions: {len(self.problems)} - Number of genres: {len(self.genres)}'
    
    def get_problem(self, idx):
        return self.problems[idx]
    
    def save_quiz(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)