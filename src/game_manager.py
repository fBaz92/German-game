# ==================== src/game_manager.py ====================
import random
from .data_loader import DataLoader
from .database import DatabaseManager


class GameManager:
    """Gestisce il flusso del gioco"""
    
    def __init__(self):
        self.loader = DataLoader()
        self.db = DatabaseManager()
        self.errors = []
        self.correct_count = 0
        self.total_count = 0
    
    def start(self):
        """Avvia il gioco"""
        self._print_welcome()
        
        # Scelta categoria
        game_type = self._choose_game_type()
        if not game_type:
            return
        
        # Carica i dati
        words = self._load_words(game_type)
        if not words:
            return
        
        print(f"\n✅ Caricati {len(words)} {game_type.lower()}")
        
        # Scelta modalità
        mode = self._choose_mode(game_type)
        if not mode:
            return
        
        # Avvia il gioco
        self._play(words, game_type, mode)
        
        # Mostra risultati
        self._show_results(game_type, mode)
    
    def _print_welcome(self):
        """Stampa il messaggio di benvenuto"""
        print("\n" + "="*50)
        print("🇩🇪  BENVENUTO AL GIOCO DI TEDESCO  🇩🇪")
        print("="*50)
    
    def _choose_game_type(self):
        """Chiede all'utente cosa vuole studiare"""
        print("\nCosa vuoi studiare?")
        print("1. Nomi (Sostantivi)")
        print("2. Verbi")
        print("3. Aggettivi")
        
        choice = input("\nScelta (1/2/3): ").strip()
        
        game_types = {
            '1': 'Nomi',
            '2': 'Verbi',
            '3': 'Aggettivi'
        }
        
        return game_types.get(choice)
    
    def _choose_mode(self, game_type):
        """Chiede la modalità di gioco"""
        print("\nScegli modalità:")
        print("1. Traduzione (Italiano → Tedesco)")
        
        if game_type == 'Nomi':
            print("2. Articoli (der/die/das)")
        
        choice = input("\nModalità (1/2): ").strip()
        
        if choice == '1':
            return 'Traduzione'
        elif choice == '2' and game_type == 'Nomi':
            return 'Articoli'
        
        return None
    
    def _load_words(self, game_type):
        """Carica le parole in base al tipo di gioco"""
        if game_type == 'Nomi':
            return self.loader.load_nouns()
        elif game_type == 'Verbi':
            return self.loader.load_verbs()
        elif game_type == 'Aggettivi':
            return self.loader.load_adjectives()
        return []
    
    def _play(self, words, game_type, mode):
        """Gestisce il loop principale del gioco"""
        # Mescola le parole
        random.shuffle(words)
        
        print("\n" + "="*50)
        print(f"🎮 MODALITÀ: {mode.upper()}")
        print("="*50)
        print("💡 Suggerimento: Puoi interrompere in qualsiasi momento rispondendo 'n'")
        
        for i, word in enumerate(words, 1):
            print(f"\n📝 Domanda {i}:")
            
            if mode == 'Traduzione':
                is_correct = self._ask_translation(word)
            elif mode == 'Articoli':
                is_correct = self._ask_article(word)
            
            # Chiedi se continuare
            if not self._ask_continue():
                break
        
        print("\n" + "="*50)
    
    def _ask_translation(self, word):
        """Chiede la traduzione di una parola"""
        print(f"Come si dice '{word.italian}' in tedesco?")
        user_answer = input("➤ La tua risposta: ").strip()
        
        is_correct, penalty, feedback = word.check_answer(user_answer)
        print(feedback)
        
        self.total_count += 1
        
        if is_correct:
            self.correct_count += 1
        else:
            self.errors.append({
                'word_german': word.german,
                'word_italian': word.italian,
                'user_answer': user_answer,
                'correct_answer': word.german,
                'penalty': penalty
            })
        
        return is_correct
    
    def _ask_article(self, word):
        """Chiede l'articolo di un sostantivo"""
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
        
        return is_correct
    
    def _ask_continue(self):
        """Chiede se continuare"""
        response = input("\nContinuare? (s/n): ").strip().lower()
        return response == 's'
    
    def _show_results(self, game_type, mode):
        """Mostra i risultati finali"""
        print("\n" + "="*50)
        print("📊 RISULTATI FINALI")
        print("="*50)
        
        if self.total_count == 0:
            print("\n❌ Nessuna domanda risposta.")
            return
        
        # Calcola punteggio effettivo (considerando penalità)
        total_errors = sum(err['penalty'] for err in self.errors)
        effective_score = self.total_count - total_errors
        success_rate = (effective_score / self.total_count * 100)
        
        print(f"\n✅ Risposte corrette: {self.correct_count}/{self.total_count}")
        print(f"❌ Errori totali: {len(self.errors)}")
        print(f"📈 Percentuale di successo: {success_rate:.1f}%")
        
        # Mostra errori
        if self.errors:
            print("\n" + "─"*50)
            print("Errori commessi:")
            print("─"*50)
            
            for i, error in enumerate(self.errors, 1):
                penalty_text = "mezzo errore" if error['penalty'] == 0.5 else "errore completo"
                print(f"{i}. {error['word_italian']} → {error['word_german']}")
                print(f"   Hai risposto: {error['user_answer']} ({penalty_text})")
        
        # Salva nel database
        self.db.save_game(
            game_type=game_type,
            mode=mode,
            total_questions=self.total_count,
            correct_answers=self.correct_count,
            errors=self.errors
        )
        
        print("\n💾 Partita salvata nel database!")
        print("="*50)
