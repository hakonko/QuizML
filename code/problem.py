class Problem:
    
    def __init__(self, pid, question, latex, alternatives, correct_alt, genre, image=None):
        self.pid = pid
        self.question = question
        self.latex = latex
        self.alternatives = alternatives
        self.correct_alt = correct_alt
        self.genre = genre
        self.image = image

    def get_question(self):
        return self.question
    
    def get_latex(self):
        return self.latex
    
    def get_alts(self):
        return self.alternatives

    def get_correct_alt(self):
        return self.correct_alt
    
    def get_genre(self):
        return self.genre
    
    def get_image(self):
        return self.image