# ==================== src/review_mode.py ====================

import random
from .database import DatabaseManager
from .data_loader import DataLoader


class ReviewMode:
    """Modalità di ripasso basata sugli errori più frequenti"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.loader = DataLoader()
        self.errors = []
        self.correct_count = 0
        self.total_count = 0
    
    def get_words_to_review(self, game_type, min_errors=2, limit=20):
        """
        Ottiene le parole da ripassare basate sugli errori
        
        Args:
            game_type: 'Nomi', 'Verbi', o 'Aggettivi'
            min_errors: numero minimo di errori per includere la parola
            limit: numero massimo di parole da ripassare
        
        Returns:
            list di oggetti Word (Noun/Verb/Adjective)
        """
        # Ottieni le parole più sbagliate dal database
        error_words = self.db.get_most_common_errors_by_type(game_type, min_errors)
        
        if not error_words:
            return None
        
        # Carica tutte le parole del tipo richiesto
        if game_type == 'Nomi':
            all_words = self.loader.load_nouns()
        elif game_type == 'Verbi':
            all_words = self.loader.load_verbs()
        else:
            all_words = self.loader.load_adjectives()
        
        # Filtra solo le parole con errori
        words_to_review = []
        error_dict = {word[0]: word[2] for word in error_words}  # {german: error_count}
        
        for word in all_words:
            word_german = word.german if hasattr(word, 'german') else word.verb if hasattr(word, 'verb') else word.adjective
            if word_german in error_dict:
                words_to_review.append(word)
        
        # Limita il numero e ordina per numero di errori (più errori = priorità)
        words_to_review = words_to_review[:limit]
        
        return words_to_review
    
    def start_review(self, game_type, mode='Traduzione'):
        """Avvia una sessione di ripasso"""
        print("\n" + "="*50)
        print("🔄 MODALITÀ RIPASSO ERRORI")
        print("="*50)
        
        # Ottieni le parole da ripassare
        words = self.get_words_to_review(game_type)
        
        if not words:
            print("\n✨ Complimenti! Non hai errori frequenti da ripassare!")
            print("   Prova a giocare una partita normale per accumulare dati.")
            return
        
        print(f"\n📚 Trovate {len(words)} parole da ripassare")
        print("   (Queste sono le parole che hai sbagliato più spesso)\n")
        
        # Mescola le parole
        random.shuffle(words)
        
        # Loop di ripasso
        for i, word in enumerate(words, 1):
            print(f"\n📝 Parola {i}/{len(words)}:")
            
            if mode == 'Traduzione':
                self._ask_translation(word)
            elif mode == 'Articoli' and game_type == 'Nomi':
                self._ask_article(word)
            elif mode == 'Coniugazioni' and game_type == 'Verbi':
                self._ask_conjugation(word)
            
            # Chiedi se continuare
            if not self._ask_continue():
                break
        
        # Mostra risultati
        self._show_results(game_type, mode)
    
    def _ask_translation(self, word):
        """Chiede la traduzione"""
        print(f"Come si dice '{word.italian}' in tedesco?")
        user_answer = input("➤ La tua risposta: ").strip()
        
        correct_word = word.german if hasattr(word, 'german') else word.verb if hasattr(word, 'verb') else word.adjective
        is_correct, penalty, feedback = word.check_answer(user_answer)
        print(feedback)
        
        self.total_count += 1
        
        if is_correct:
            self.correct_count += 1
        else:
            self.errors.append({
                'word_german': correct_word,
                'word_italian': word.italian,
                'user_answer': user_answer,
                'correct_answer': correct_word,
                'penalty': penalty
            })
    
    def _ask_article(self, word):
        """Chiede l'articolo"""
        print(f"Articolo di '{word.german}'? (der/die/das)")
        user_answer = input("➤ La tua risposta (der/die/das): ").strip()
        
        is_correct, penalty, feedback = word.check_article(user_answer)
        print(feedback)
        
        self.total_count += 1
        
        if is_correct:
            self.correct_count += 1
        else:
            self.errors.append({
                'word_german': word.german,
                'word_italian': word.italian,
                'user_answer': user_answer,
                'correct_answer': word.article,
                'penalty': penalty
            })
    
    def _ask_conjugation(self, verb):
        """Chiede una coniugazione verbale"""
        # Scegli casualmente tra Präteritum e Participio
        conj_type = random.choice(['präteritum', 'participio'])
        
        if conj_type == 'präteritum':
            print(f"Coniuga '{verb.german}' ({verb.italian}) al Präteritum")
            correct_answer = verb.prateritum
        else:
            print(f"Participio passato di '{verb.german}' ({verb.italian})")
            correct_answer = verb.participio
        
        user_answer = input("➤ La tua risposta: ").strip()
        
        self.total_count += 1
        
        if user_answer == correct_answer:
            print("✅ CORRETTO!")
            self.correct_count += 1
        else:
            print(f"❌ SBAGLIATO! Risposta corretta: {correct_answer}")
            self.errors.append({
                'word_german': verb.german,
                'word_italian': verb.italian,
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'penalty': 1.0
            })
    
    def _ask_continue(self):
        """Chiedi se continuare"""
        response = input("\nContinuare? (s/n): ").strip().lower()
        return response == 's'
    
    def _show_results(self, game_type, mode):
        """Mostra i risultati del ripasso"""
        print("\n" + "="*50)
        print("📊 RISULTATI RIPASSO")
        print("="*50)
        
        if self.total_count == 0:
            print("\n❌ Nessuna domanda risposta.")
            return
        
        total_errors = sum(err['penalty'] for err in self.errors)
        effective_score = self.total_count - total_errors
        success_rate = (effective_score / self.total_count * 100)
        
        print(f"\n✅ Risposte corrette: {self.correct_count}/{self.total_count}")
        print(f"❌ Errori totali: {len(self.errors)}")
        print(f"📈 Percentuale di successo: {success_rate:.1f}%")
        
        # Mostra errori
        if self.errors:
            print("\n" + "─"*50)
            print("Errori da ripassare ancora:")
            print("─"*50)
            
            for i, error in enumerate(self.errors, 1):
                penalty_text = "mezzo errore" if error['penalty'] == 0.5 else "errore completo"
                print(f"{i}. {error['word_italian']} → {error['word_german']}")
                print(f"   Hai risposto: {error['user_answer']} ({penalty_text})")
        
        # Salva nel database
        self.db.save_game(
            game_type=f"{game_type} (Ripasso)",
            mode=mode,
            total_questions=self.total_count,
            correct_answers=self.correct_count,
            errors=self.errors
        )
        
        print("\n💾 Sessione di ripasso salvata!")
        print("="*50)