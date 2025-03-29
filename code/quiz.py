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
        self.date_taken = datetime.now()
        self.grade = None

        self._create_quiz()


    def _create_quiz(self):
        df = pd.read_csv(self.quiz_file, sep=';')
        self.genres = df['_genre'].unique()
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
        used_indices = set()

        def get_error_rate(pid):
            stats = self.user.question_stats.get(pid, {"correct": 0, "wrong": 0})
            total = stats["correct"] + stats["wrong"]
            return (stats["wrong"] / total) if total > 0 else 0.5  # ukjente får middels prioritet

        for genre in self.genres:
            df_genre = df[df['_genre'] == genre].copy()
            n = min(len(df_genre), genre_counts[genre])

            # Sorter etter feilrate
            df_genre["_error_rate"] = df_genre['_pid'].apply(get_error_rate)
            chosen = df_genre.sort_values(by="_error_rate", ascending=False).head(n)
            used_indices.update(chosen.index)

            for _, row in chosen.iterrows():
                alts = [row['_alt1'], row['_alt2'], row['_alt3'], row['_alt4'], row['_alt5']]
                problem = Problem(
                    question=row['_question'],
                    latex=row['_latex'] if pd.notna(row['_latex']) else None,
                    alts=alts,
                    correct_alt=row['_correct_alt'],
                    genre=row['_genre'],
                    pid=row['_pid']
                )
                self.problems.append(problem)

        while len(self.problems) < self.num_problems:
            df_remaining = df[~df.index.isin(used_indices)].copy()  # <- dette er viktig!   
            if df_remaining.empty:
                break

            df_remaining.loc[:, "_error_rate"] = df_remaining['_pid'].apply(get_error_rate)
            row = df_remaining.sort_values(by="_error_rate", ascending=False).iloc[0]
            used_indices.add(row.name)

            alts = [row['_alt1'], row['_alt2'], row['_alt3'], row['_alt4'], row['_alt5']]
            problem = Problem(
                question=row['_question'],
                latex=row['_latex'] if pd.notna(row['_latex']) else None,
                alts=alts,
                correct_alt=row['_correct_alt'],
                genre=row['_genre'],
                pid=row['_pid']
            )
            self.problems.append(problem)
    
    def _create_quiz_old(self):
        df = pd.read_csv(self.quiz_file, sep=';')
        self.genres = df['_genre'].unique()
        random.shuffle(self.genres)

        # Fordel antall oppgaver jevnt mellom kategoriene
        genre_counts = {genre: 1 for genre in self.genres}
        remaining = self.num_problems - len(self.genres)

        # Fordel resterende spørsmål jevnt
        while remaining > 0:
            for genre in self.genres:
                if remaining == 0:
                    break
                genre_counts[genre] += 1
                remaining -= 1

        self.problems = []
        used_indices = set()

        for genre in self.genres:
            df_genre = df[df['_genre'] == genre]
            n = min(len(df_genre), genre_counts[genre])

            # Tilfeldig trekning uten gjenbruk
            chosen = df_genre.sample(n, random_state=random.randint(0, 99999))
            used_indices.update(chosen.index)

            for _, row in chosen.iterrows():
                alts = [row['_alt1'], row['_alt2'], row['_alt3'], row['_alt4'], row['_alt5']]
                problem = Problem(
                    question=row['_question'],
                    latex=row['_latex'] if pd.notna(row['_latex']) else None,
                    alts=alts,
                    correct_alt=row['_correct_alt'],
                    genre=row['_genre']
                )
                self.problems.append(problem)

        # Hvis det fortsatt mangler spørsmål (f.eks. hvis noen sjangre var for små)
        while len(self.problems) < self.num_problems:
            df_remaining = df[~df.index.isin(used_indices)]
            if df_remaining.empty:
                break  # ikke mer å hente

            row = df_remaining.sample(1, random_state=random.randint(0, 99999)).iloc[0]
            used_indices.add(row.name)

            alts = [row['_alt1'], row['_alt2'], row['_alt3'], row['_alt4'], row['_alt5']]
            problem = Problem(
                question=row['_question'],
                latex=row['_latex'] if pd.notna(row['_latex']) else None,
                alts=alts,
                correct_alt=row['_correct_alt'],
                genre=row['_genre']
            )
            self.problems.append(problem)


    def __str__(self):
        return f'IN3310-Quiz. Number of questions: {len(self.problems)} - Number of genres: {len(self.genres)}'
    
    def get_problem(self, idx):
        return self.problems[idx]
    
    def save_quiz(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)