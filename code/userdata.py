import pickle
from pathlib import Path
from collections import defaultdict

def default_stat():
    return {'correct': 0, 'wrong': 0}

class User:
    def __init__(self, name, username, password_hash, saved_quizzes=None, question_stats=None):
        self.name = name
        self.username = username
        self.password_hash = password_hash
        self.saved_quizzes = saved_quizzes if saved_quizzes is not None else []

        # Bruk eksisterende stats hvis det finnes, ellers lag ny defaultdict
        self.question_stats = (
            defaultdict(default_stat, question_stats)
            if question_stats is not None
            else defaultdict(default_stat)
        )

    def add_quiz(self, quiz):
        self.saved_quizzes.append(quiz)



class UserDatabase:
    def __init__(self, filepath='userdata.pkl'):
        self.filepath = Path(filepath)
        self.users = self._load_users()

    def _load_users(self):
        if self.filepath.exists():
            with open(self.filepath, 'rb') as f:
                self.users = pickle.load(f)
            
            for user in self.users.values():
                if not isinstance(user.question_stats, defaultdict):
                    user.question_stats = defaultdict(default_stat, user.question_stats)
        else:
            self.users = {}
            
        return self.users
    
    def save(self):
        with open(self.filepath, 'wb') as f:
            pickle.dump(self.users, f)

    def add_user(self, user: User):
        self.users[user.username] = user
        self.save()

    def get_user(self, username):
        return self.users.get(username)
    
    def user_exists(self, username):
        return username in self.users
