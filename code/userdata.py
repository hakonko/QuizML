import pickle
from pathlib import Path

class User:
    def __init__(self, name, username, password_hash):
        self.name = name
        self.username = username
        self.password_hash = password_hash

        self.saved_quizzes = []
        
        self.total_score = 0.0

    def add_quiz(self, quiz):
        self.saved_quizzes.append(quiz)


class UserDatabase:
    def __init__(self, filepath='userdata.pkl'):
        self.filepath = Path(filepath)
        self.users = self._load_users()

    def _load_users(self):
        if self.filepath.exists():
            with open(self.filepath, 'rb') as f:
                return pickle.load(f)
            
        return {}
    
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
