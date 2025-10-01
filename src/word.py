# ==================== src/word.py ====================

# Classi Word, Noun, Verb, Adjective 

# ==================== src/word.py ====================


class Word:
    """Classe base per tutte le parole"""
    
    def __init__(self, german, italian):
        self.german = german
        self.italian = italian
    
    def check_answer(self, user_answer):
        """
        Verifica la risposta dell'utente
        Ritorna: (is_correct, penalty, feedback)
        - is_correct: bool
        - penalty: float (0 = corretto, 0.5 = mezzo errore, 1.0 = errore)
        - feedback: str (messaggio per l'utente)
        """
        correct = self.german
        
        # Rimuovi spazi extra
        user_answer = user_answer.strip()
        
        # Risposta esatta
        if user_answer == correct:
            return True, 0, "✅ CORRETTO!"
        
        # Errore di maiuscola (per sostantivi è grave)
        if user_answer.lower() == correct.lower():
            if user_answer[0].islower() and correct[0].isupper():
                return False, 1.0, f"❌ SBAGLIATO! In tedesco i sostantivi iniziano con la MAIUSCOLA: {correct}"
            return False, 0.5, f"⚠️ QUASI! Attenzione alle maiuscole: {correct}"
        
        # Errore di umlaut
        umlaut_map = {'ä': 'a', 'ö': 'o', 'ü': 'u', 'Ä': 'A', 'Ö': 'O', 'Ü': 'U', 'ß': 'ss'}
        
        def normalize_umlauts(text):
            for umlaut, replacement in umlaut_map.items():
                text = text.replace(umlaut, replacement)
            return text
        
        if normalize_umlauts(user_answer) == normalize_umlauts(correct):
            return False, 0.5, f"⚠️ QUASI! Attenzione alle umlaut: {correct}"
        
        # Errore completo
        return False, 1.0, f"❌ SBAGLIATO! Risposta corretta: {correct}"


class Noun(Word):
    """Sostantivo tedesco"""
    
    def __init__(self, german, article, plural, italian):
        super().__init__(german, italian)
        self.article = article  # der, die, das
        self.plural = plural
    
    def check_article(self, user_article):
        """
        Verifica l'articolo
        Ritorna: (is_correct, penalty, feedback)
        """
        user_article = user_article.strip().lower()
        correct = self.article.lower()
        
        if user_article == correct:
            return True, 0, "✅ CORRETTO!"
        
        return False, 1.0, f"❌ SBAGLIATO! Risposta corretta: {self.article}"
    
    def __str__(self):
        return f"{self.article} {self.german} ({self.plural})"


class Verb(Word):
    """Verbo tedesco"""
    
    def __init__(self, german, regular, italian, prateritum, participio, 
                 perfetto, caso, riflessivo):
        super().__init__(german, italian)
        self.regular = regular
        self.prateritum = prateritum
        self.participio = participio
        self.perfetto = perfetto
        self.caso = caso
        self.riflessivo = riflessivo
    
    def __str__(self):
        return f"{self.german} ({self.prateritum}, {self.participio})"


class Adjective(Word):
    """Aggettivo tedesco"""
    
    def __init__(self, german, comparative, superlative, italian):
        super().__init__(german, italian)
        self.comparative = comparative
        self.superlative = superlative
    
    def __str__(self):
        return f"{self.german} ({self.comparative}, {self.superlative})"
