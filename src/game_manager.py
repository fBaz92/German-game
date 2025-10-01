# ==================== src/game_manager.py ====================
import random
from .data_loader import DataLoader
from .database import DatabaseManager
from .review_mode import ReviewMode
from .statistics import StatisticsManager


class GameManager:
    """Gestisce il flusso del gioco"""
    
    def __init__(self):
        self.loader = DataLoader()
        self.db = DatabaseManager()
        self.review = ReviewMode()
        self.stats = StatisticsManager()
        self.errors = []
        self.correct_count = 0
        self.total_count = 0
    
    def start(self):
        """Avvia il gioco"""
        self._print_welcome()
        
        # Scelta modalità principale
        main_mode = self._choose_main_mode()
        
        if main_mode == 'statistiche':
            self.stats.show_dashboard()
            
            # Chiedi se esportare
            export = input("\n📥 Vuoi esportare le statistiche? (s/n): ").strip().lower()
            if export == 's':
                self.stats.export_statistics()
            return
        
        # Scelta categoria
        game_type = self._choose_game_type()
        if not game_type:
            return
        
        if main_mode == 'ripasso':
            # Modalità ripasso errori
            mode = self._choose_mode(game_type)
            if not mode:
                return
            self.review.start_review(game_type, mode)
            return
        
        # Modalità normale
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
    
    def _choose_main_mode(self):
        """Chiede la modalità principale"""
        print("\nCosa vuoi fare?")
        print("1. Partita normale")
        print("2. Ripasso errori")
        print("3. Visualizza statistiche")
        
        choice = input("\nScelta (1/2/3): ").strip()
        
        modes = {
            '1': 'normale',
            '2': 'ripasso',
            '3': 'statistiche'
        }
        
        return modes.get(choice, 'normale')
    
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
        elif game_type == 'Verbi':
            print("2. Coniugazioni (Präteritum/Participio)")
        
        choice = input("\nModalità (1/2): ").strip()
        
        if choice == '1':
            return 'Traduzione'
        elif choice == '2' and game_type == 'Nomi':
            return 'Articoli'
        elif choice == '2' and game_type == 'Verbi':
            return 'Coniugazioni'
        
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
        print("💡 Suggerimento: Digita 'n' per terminare in qualsiasi momento")
        
        for i, word in enumerate(words, 1):
            print(f"\n📝 Domanda {i}:")
            
            if mode == 'Traduzione':
                result = self._ask_translation(word)
            elif mode == 'Articoli':
                result = self._ask_article(word)
            elif mode == 'Coniugazioni':
                result = self._ask_conjugation(word)
            
            # Controlla se l'utente vuole terminare
            if result == 'quit':
                print("\n👋 Gioco terminato dall'utente.")
                break
            
            # Mostra suggerimento per continuare (solo se non è l'ultima domanda)
            if i < len(words):
                print("(digita n per terminare)")
        
        print("\n" + "="*50)
    
    def _ask_translation(self, word):
        """Chiede la traduzione di una parola"""
        print(f"Come si dice '{word.italian}' in tedesco?")
        user_answer = input("➤ La tua risposta: ").strip()
        
        # Controlla se l'utente vuole terminare
        if user_answer.lower() == 'n':
            return 'quit'
        
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
        
        # Controlla se l'utente vuole terminare
        if user_answer.lower() == 'n':
            return 'quit'
        
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
        
        # Controlla se l'utente vuole terminare
        if user_answer.lower() == 'n':
            return 'quit'
        
        self.total_count += 1
        
        if user_answer == correct_answer:
            print("✅ CORRETTO!")
            self.correct_count += 1
            return True
        else:
            print(f"❌ SBAGLIATO! Risposta corretta: {correct_answer}")
            self.errors.append({
                'word_german': verb.german,
                'word_italian': verb.italian,
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'penalty': 1.0
            })
            return False
    
    
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