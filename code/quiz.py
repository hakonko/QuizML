import pandas as pd
import random
import pickle
from code.problem import Problem
from datetime import datetime
import time
from collections import defaultdict

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

        current_time = time.time()
        ten_days_seconds = 10 * 24 * 3600

        def get_accuracy(pid):
            stats = self.user.question_stats.get(pid, {"correct": 0, "wrong": 0, "last_timestamp": 0})
            total = stats["correct"] + stats["wrong"]
            accuracy = (stats["correct"] / total) if total else 0.5
            last_timestamp = stats.get("last_timestamp", 0)
            return accuracy, last_timestamp

        # Kategoriser spørsmål basert på accuracy og tid siden sist sett
        prioritized, neutral, skipped = [], [], []

        for p in all_problems:
            accuracy, last_timestamp = get_accuracy(p.pid)
            time_since_last_seen = current_time - last_timestamp

            if accuracy > 0.8 and time_since_last_seen < ten_days_seconds:
                skipped.append(p)
            elif accuracy < 0.6:
                prioritized.append(p)
            else:
                neutral.append(p)

        # Sikre jevn kategorifordeling
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
        used_pids = set()

        # Først velg prioriterte
        for genre in self.genres:
            genre_problems = [p for p in prioritized if p.genre == genre and p.pid not in used_pids]
            n = min(len(genre_problems), genre_counts[genre])
            random.shuffle(genre_problems)
            selected = genre_problems[:n]
            used_pids.update(p.pid for p in selected)
            self.problems.extend(selected)
            genre_counts[genre] -= len(selected)

        # Så nøytrale spørsmål
        for genre in self.genres:
            remaining_slots = genre_counts[genre]
            if remaining_slots > 0:
                genre_problems = [p for p in neutral if p.genre == genre and p.pid not in used_pids]
                n = min(len(genre_problems), remaining_slots)
                random.shuffle(genre_problems)
                selected = genre_problems[:n]
                used_pids.update(p.pid for p in selected)
                self.problems.extend(selected)
                genre_counts[genre] -= len(selected)

        # Til slutt spørsmål som tidligere ble hoppet over
        for genre in self.genres:
            remaining_slots = genre_counts[genre]
            if remaining_slots > 0:
                genre_problems = [p for p in skipped if p.genre == genre and p.pid not in used_pids]
                n = min(len(genre_problems), remaining_slots)
                random.shuffle(genre_problems)
                selected = genre_problems[:n]
                used_pids.update(p.pid for p in selected)
                self.problems.extend(selected)
                genre_counts[genre] -= len(selected)

        # Hvis fortsatt ikke nok spørsmål, fyll tilfeldig
        if len(self.problems) < self.num_problems:
            remaining_problems = [p for p in all_problems if p.pid not in used_pids]
            random.shuffle(remaining_problems)
            self.problems.extend(remaining_problems[:self.num_problems - len(self.problems)])

    def __str__(self):
        return f'IN3310-Quiz. Number of questions: {len(self.problems)} - Number of genres: {len(self.genres)}'
    
    def get_problem(self, idx):
        return self.problems[idx]
    
    def save_quiz(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)