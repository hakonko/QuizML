import pandas as pd
import random
from problem import Problem

class Quiz:
    def __init__(self, num_problems, user_file, quiz_file):
        self.num_problems = num_problems
        self.user_file = user_file
        self.quiz_file = quiz_file
        self.genres = None
        self.problems = []

        self._create_quiz()
    
    def _create_quiz(self):
        df = pd.read_csv(self.quiz_file, sep=';')
        self.genres = df['_genre'].unique()

        used_indices = set()

        for genre in self.genres:
            df_genre = df[df['_genre'] == genre]
            chosen = df_genre.sample(1, random_state=random.randint(0, 9999))
            used_indices.update(chosen.index)

            row = chosen.iloc[0]
            alts = [row['_alt1'], row['_alt2'], row['_alt3'], row['_alt4'], row['_alt5']]
            problem = Problem(question=row['_question'],
                              latex=row['_latex'] if pd.notna(row['_latex']) else None,
                              alts=alts,
                              correct_alt=row['_correct_alt'],
                              genre=row['_genre']
                              )
            self.problems.append(problem)
            
        remaining_num = self.num_problems - len(self.problems)

        if remaining_num > 0:
            df_remaining = df[~df.index.isin(used_indices)].sample(remaining_num, random_state=42)

            for _, row in df_remaining.iterrows():
                alts = [row['_alt1'], row['_alt2'], row['_alt3'], row['_alt4'], row['_alt5']]
                problem = Problem(question=row['_question'],
                                latex=row['_latex'] if pd.notna(row['_latex']) else None,
                                alts=alts,
                                correct_alt=row['_correct_alt'],
                                genre=row['_genre'])
                
                self.problems.append(problem)

    def __str__(self):
        return f'IN3310-Quiz. Number of questions: {len(self.problems)} - Number of genres: {len(self.genres)}'
    
    def get_problem(self, idx):
        return self.problems[idx]

