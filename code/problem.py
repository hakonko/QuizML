class Problem:
    
    def __init__(self, question, latex, alts, correct_alt, genre, pid=None):
        self.question = question
        self.latex = latex
        self.alts = alts
        self.correct_alt = correct_alt
        self.genre = genre
        self.pid = pid

    def get_question(self):
        return self.question
    
    def get_latex(self):
        return self.latex
    
    def get_alts(self):
        return self.alts

    def get_correct_alt(self):
        return self.correct_alt
    
    def get_genre(self):
        return self.genre