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
        """Avvia il gioco con loop principale"""
        self._print_welcome()
        
        while True:
            try:
                # Scelta modalità principale
                main_mode = self._choose_main_mode()
                
                if main_mode == 'statistiche':
                    self.stats.show_dashboard()
                    
                    # Chiedi se esportare
                    export = input("\n📥 Vuoi esportare le statistiche? (s/n): ").strip().lower()
                    if export == 's':
                        self.stats.export_statistics()
                    continue
                
                if main_mode == 'esci':
                    print("\n👋 Grazie per aver giocato! Auf Wiedersehen!")
                    break
                
                # Scelta categoria
                game_type = self._choose_game_type()
                if not game_type:
                    continue
                
                if main_mode == 'ripasso':
                    # Modalità ripasso errori
                    mode = self._choose_mode(game_type)
                    if not mode:
                        continue
                    self.review.start_review(game_type, mode)
                    continue
                
                if main_mode == 'studio':
                    # Modalità studio
                    self._start_study_mode(game_type)
                    continue
                
                if main_mode == 'studio_approfondito':
                    # Modalità studio approfondito
                    self._start_deep_study_mode(game_type)
                    continue
                
                # Modalità normale
                # Carica i dati
                words = self._load_words(game_type)
                if not words:
                    continue
                
                print(f"\n✅ Caricati {len(words)} {game_type.lower()}")
                
                # Scelta modalità
                mode = self._choose_mode(game_type)
                if not mode:
                    continue
                
                # Scelta difficoltà
                difficulty_mode, difficulty_level = self._choose_difficulty(words)
                filtered_words = self.loader.get_words_by_difficulty(words, difficulty_mode, difficulty_level)
                
                if not filtered_words:
                    print("❌ Nessuna parola disponibile per i criteri selezionati.")
                    continue
                
                print(f"✅ Selezionate {len(filtered_words)} parole per il gioco")
                
                # Avvia il gioco
                self._play(filtered_words, game_type, mode)
                
                # Mostra risultati
                self._show_results(game_type, mode)
                
            except KeyboardInterrupt:
                print("\n\n👋 Gioco interrotto. Vuoi continuare? (s/n): ", end="")
                try:
                    response = input().strip().lower()
                    if response != 's':
                        break
                except:
                    break
            except Exception as e:
                print(f"\n❌ Errore imprevisto: {e}")
                print("Vuoi continuare? (s/n): ", end="")
                try:
                    response = input().strip().lower()
                    if response != 's':
                        break
                except:
                    break
    
    def _print_welcome(self):
        """Stampa il messaggio di benvenuto"""
        print("\n" + "="*50)
        print("🇩🇪  BENVENUTO AL GIOCO DI TEDESCO  🇩🇪")
        print("="*50)
    
    def _choose_main_mode(self):
        """Chiede la modalità principale"""
        while True:
            print("\nCosa vuoi fare?")
            print("1. Partita normale")
            print("2. Modalità studio")
            print("3. Studio approfondito")
            print("4. Ripasso errori")
            print("5. Visualizza statistiche")
            print("6. Esci")
            
            choice = input("\nScelta (1/2/3/4/5/6): ").strip()
            
            modes = {
                '1': 'normale',
                '2': 'studio',
                '3': 'studio_approfondito',
                '4': 'ripasso',
                '5': 'statistiche',
                '6': 'esci'
            }
            
            if choice in modes:
                return modes[choice]
            else:
                print("❌ Comando non valido! Scegli tra 1, 2, 3, 4, 5 o 6.")
    
    def _start_study_mode(self, game_type):
        """Avvia la modalità studio"""
        print("\n" + "="*50)
        print("📚 MODALITÀ STUDIO")
        print("="*50)
        
        # Carica i dati
        words = self._load_words(game_type)
        if not words:
            return
        
        print(f"\n✅ Caricati {len(words)} {game_type.lower()}")
        
        # Chiedi quanti ne vuole studiare
        max_words = len(words)
        while True:
            try:
                study_count = input(f"\n📖 Quanti {game_type.lower()} vuoi studiare? (1-{max_words}): ").strip()
                study_count = int(study_count)
                if 1 <= study_count <= max_words:
                    break
                else:
                    print(f"❌ Comando non valido! Inserisci un numero tra 1 e {max_words}")
            except ValueError:
                print("❌ Comando non valido! Inserisci un numero valido (es. 5)")
        
        # Scelta difficoltà per lo studio
        difficulty_mode, difficulty_level = self._choose_difficulty(words)
        filtered_words = self.loader.get_words_by_difficulty(words, difficulty_mode, difficulty_level)
        
        if not filtered_words:
            print("❌ Nessuna parola disponibile per i criteri selezionati.")
            return
        
        # Mescola e seleziona le parole
        random.shuffle(filtered_words)
        study_words = filtered_words[:study_count]
        
        # Mostra l'elenco di studio
        self._show_study_list(study_words, game_type)
        
        # Chiedi se è pronto per la partita
        ready = input("\n🎮 Sei pronto per la partita? (s/n): ").strip().lower()
        if ready == 's':
            # Scelta modalità di gioco
            mode = self._choose_mode(game_type)
            if mode:
                # Avvia la partita con le parole studiate
                self._play(study_words, game_type, mode)
                # Mostra risultati
                self._show_results(game_type, mode)
        else:
            print("\n👋 Studio completato. Alla prossima!")
    
    def _start_deep_study_mode(self, game_type):
        """Avvia la modalità studio approfondito"""
        print("\n" + "="*50)
        print("🎯 MODALITÀ STUDIO APPROFONDITO")
        print("="*50)
        print("💡 Continuerai fino a quando non padroneggi TUTTE le parole!")
        
        # Carica i dati
        words = self._load_words(game_type)
        if not words:
            return
        
        print(f"\n✅ Caricati {len(words)} {game_type.lower()}")
        
        # Scelta numero di parole da studiare
        max_words = min(len(words), 50)  # Limite massimo di 50 parole per lo studio approfondito
        print(f"\nQuante parole vuoi studiare? (max {max_words})")
        
        while True:
            try:
                study_count = int(input(f"Numero di parole (1-{max_words}): ").strip())
                if 1 <= study_count <= max_words:
                    break
                else:
                    print(f"❌ Comando non valido! Inserisci un numero tra 1 e {max_words}")
            except ValueError:
                print("❌ Comando non valido! Inserisci un numero valido (es. 10)")
        
        # Scelta difficoltà per lo studio approfondito
        difficulty_mode, difficulty_level = self._choose_difficulty(words)
        filtered_words = self.loader.get_words_by_difficulty(words, difficulty_mode, difficulty_level)
        
        if not filtered_words:
            print("❌ Nessuna parola disponibile per i criteri selezionati.")
            return
        
        # Mescola e seleziona le parole
        random.shuffle(filtered_words)
        study_words = filtered_words[:study_count]
        
        # Scelta modalità di gioco
        mode = self._choose_mode(game_type)
        if not mode:
            return
        
        # Avvia lo studio approfondito
        self._play_deep_study(study_words, game_type, mode)
    
    def _play_deep_study(self, words, game_type, mode):
        """Gioca in modalità studio approfondito fino a padroneggiare tutte le parole"""
        print("\n" + "="*50)
        print(f"🎯 STUDIO APPROFONDITO: {mode.upper()}")
        print("="*50)
        print("💡 Continuerai fino a padroneggiare TUTTE le parole!")
        print("💡 Suggerimento: Digita 'n' per terminare in qualsiasi momento")
        
        # Dizionario per tracciare quante volte ogni parola è stata sbagliata
        word_difficulty = {i: 0 for i, word in enumerate(words)}
        
        # Lista delle parole ancora da padroneggiare
        words_to_master = list(enumerate(words))
        
        round_number = 1
        total_questions = 0
        
        while words_to_master:
            print(f"\n🔄 ROUND {round_number} - Parole da studiare: {len(words_to_master)}")
            print("="*50)
            
            # Mescola le parole per questo round
            random.shuffle(words_to_master)
            
            # Gioca questo round completo
            round_results = self._play_round_deep_study(words_to_master, mode, round_number)
            total_questions += round_results['total_questions']
            
            # Aggiorna la difficoltà delle parole
            for word_idx, attempts in round_results['word_attempts'].items():
                if not round_results['mastered_words'].get(word_idx, False):
                    # Se non è stata padroneggiata, incrementa la difficoltà
                    word_difficulty[word_idx] += 1
            
            # Mostra risultati del round
            print(f"\n📊 RISULTATI ROUND {round_number}:")
            print("="*30)
            
            mastered_this_round = 0
            not_mastered_this_round = 0
            
            for word_idx, word in words_to_master:
                if round_results['mastered_words'].get(word_idx, False):
                    mastered_this_round += 1
                    print(f"✅ {word.italian} → {word.german} (PADRONEGGIATA)")
                else:
                    not_mastered_this_round += 1
                    attempts = round_results['word_attempts'].get(word_idx, 1)
                    print(f"❌ {word.italian} → {word.german} ({attempts} tentativi)")
            
            print(f"\n📈 Round {round_number} completato:")
            print(f"   ✅ Padroneggiate: {mastered_this_round}")
            print(f"   ❌ Da ripassare: {not_mastered_this_round}")
            
            # Rimuovi le parole padroneggiate per il prossimo round
            words_to_master = [(word_idx, word) for word_idx, word in words_to_master 
                             if not round_results['mastered_words'].get(word_idx, False)]
            
            round_number += 1
            
            # Mostra progresso generale
            mastered_count = len(words) - len(words_to_master)
            print(f"\n🎯 PROGRESSO GENERALE: {mastered_count}/{len(words)} parole padroneggiate")
            
            # Se ci sono ancora parole da padroneggiare, chiedi se continuare
            if words_to_master:
                continue_game = input(f"\n🔄 Vuoi continuare con il Round {round_number}? (s/n): ").strip().lower()
                if continue_game != 's':
                    print("\n👋 Studio approfondito terminato dall'utente.")
                    break
        
        # Mostra risultati finali
        self._show_deep_study_results(words, word_difficulty, total_questions, game_type, mode)
    
    def _play_round_deep_study(self, words_for_round, mode, round_number):
        """Gioca un round dello studio approfondito - una sola domanda per parola"""
        round_results = {
            'total_questions': 0,
            'word_attempts': {},
            'mastered_words': {}
        }
        
        for i, (word_idx, word) in enumerate(words_for_round, 1):
            print(f"\n📝 Parola {i}/{len(words_for_round)} (Round {round_number}):")
            
            if mode in ['Traduzione', 'Traduzione Inversa']:
                result = self._ask_translation(word, mode)
            elif mode == 'Articoli':
                result = self._ask_article(word)
            elif mode == 'Coniugazioni':
                result = self._ask_conjugation(word)
            
            # Controlla se l'utente vuole terminare
            if result == 'quit':
                print("\n👋 Studio approfondito terminato dall'utente.")
                return round_results
            
            round_results['total_questions'] += 1
            
            if result:  # Risposta corretta
                print("🎉 PADRONEGGIATA! Al primo tentativo!")
                round_results['mastered_words'][word_idx] = True
                round_results['word_attempts'][word_idx] = 1
            else:
                # Risposta sbagliata - da ripassare
                print("❌ Sbagliata! Da ripassare nel prossimo round.")
                round_results['mastered_words'][word_idx] = False
                round_results['word_attempts'][word_idx] = 1
        
        return round_results
    
    def _show_deep_study_results(self, words, word_difficulty, total_questions, game_type, mode):
        """Mostra i risultati dello studio approfondito"""
        print("\n" + "="*60)
        print("🎯 RISULTATI STUDIO APPROFONDITO")
        print("="*60)
        
        print(f"\n📊 Statistiche Generali:")
        print(f"   Parole totali: {len(words)}")
        print(f"   Domande totali: {total_questions}")
        print(f"   Modalità: {mode}")
        
        # Calcola statistiche
        mastered_first_try = sum(1 for attempts in word_difficulty.values() if attempts == 1)
        average_attempts = sum(word_difficulty.values()) / len(words) if words else 0
        
        print(f"\n📈 Risultati:")
        print(f"   Padroneggiate al primo tentativo: {mastered_first_try}/{len(words)} ({mastered_first_try/len(words)*100:.1f}%)")
        print(f"   Tentativi medi per parola: {average_attempts:.1f}")
        
        # Classifica delle parole più difficili
        print(f"\n🏆 CLASSIFICA PAROLE PIÙ DIFFICILI:")
        print("="*40)
        
        # Ordina le parole per difficoltà (tentativi necessari)
        sorted_words = sorted(enumerate(words), key=lambda x: word_difficulty[x[0]], reverse=True)
        
        for i, (word_idx, word) in enumerate(sorted_words[:10], 1):  # Top 10
            attempts = word_difficulty[word_idx]
            difficulty_emoji = "🔥" if attempts >= 3 else "⚡" if attempts == 2 else "✅"
            
            if mode in ['Traduzione', 'Traduzione Inversa']:
                print(f"{i:2d}. {difficulty_emoji} {word.italian} → {word.german} ({attempts} tentativi)")
            elif mode == 'Articoli':
                print(f"{i:2d}. {difficulty_emoji} {word.german} (articolo: {word.article}) ({attempts} tentativi)")
            elif mode == 'Coniugazioni':
                print(f"{i:2d}. {difficulty_emoji} {word.italian} ({attempts} tentativi)")
        
        # Salva nel database
        self.db.save_game(
            game_type=f"{game_type} (Studio Approfondito)",
            mode=mode,
            total_questions=total_questions,
            correct_answers=len(words),  # Tutte le parole sono state padroneggiate
            errors=[]  # Non usiamo il sistema di errori tradizionale
        )
        
        print(f"\n💾 Studio approfondito salvato nel database!")
        print("="*60)
        
        # Reset dello stato per la prossima partita
        self._reset_game_state()
    
    def _show_study_list(self, words, game_type):
        """Mostra l'elenco di studio"""
        print("\n" + "="*50)
        print("📋 ELENCO DI STUDIO")
        print("="*50)
        
        for i, word in enumerate(words, 1):
            print(f"\n{i:2d}. {word.italian} → {word.german} (Livello {word.frequency})")
            
            if game_type == 'Nomi' and hasattr(word, 'article'):
                print(f"    Articolo: {word.article}")
            elif game_type == 'Verbi':
                if hasattr(word, 'prateritum') and word.prateritum:
                    print(f"    Präteritum: {word.prateritum}")
                if hasattr(word, 'participio') and word.participio:
                    print(f"    Participio: {word.participio}")
        
        print("\n" + "="*50)
        print("💡 Studia bene queste parole, poi inizierà la partita!")
        print("="*50)
    
    def _choose_game_type(self):
        """Chiede all'utente cosa vuole studiare"""
        while True:
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
            
            if choice in game_types:
                return game_types[choice]
            else:
                print("❌ Comando non valido! Scegli tra 1, 2 o 3.")
    
    def _choose_mode(self, game_type):
        """Chiede la modalità di gioco"""
        while True:
            print("\nScegli modalità:")
            print("1. Traduzione (Italiano → Tedesco)")
            print("2. Traduzione Inversa (Tedesco → Italiano)")
            
            if game_type == 'Nomi':
                print("3. Articoli (der/die/das)")
                valid_choices = ['1', '2', '3']
            elif game_type == 'Verbi':
                print("3. Coniugazioni (Präteritum/Participio)")
                valid_choices = ['1', '2', '3']
            else:  # Aggettivi
                valid_choices = ['1', '2']
            
            choice = input(f"\nModalità ({'/'.join(valid_choices)}): ").strip()
            
            if choice not in valid_choices:
                if game_type == 'Aggettivi':
                    print("❌ Comando non valido! Scegli tra 1 o 2.")
                else:
                    print("❌ Comando non valido! Scegli tra 1, 2 o 3.")
                continue
            
            if choice == '1':
                return 'Traduzione'
            elif choice == '2':
                return 'Traduzione Inversa'
            elif choice == '3' and game_type == 'Nomi':
                return 'Articoli'
            elif choice == '3' and game_type == 'Verbi':
                return 'Coniugazioni'
    
    def _choose_difficulty(self, words):
        """Chiede la modalità di difficoltà"""
        print("\nScegli modalità difficoltà:")
        print("1. Casuale (tutte le parole)")
        print("2. Difficoltà Fissa (frequenza ≤ livello)")
        print("3. Focus (solo livello specifico)")
        
        while True:
            choice = input("\nModalità difficoltà (1/2/3): ").strip()
            
            if choice == '1':
                return 'casual', None
            elif choice == '2':
                return self._choose_fixed_difficulty(words)
            elif choice == '3':
                return self._choose_focus_difficulty(words)
            else:
                print("❌ Comando non valido! Scegli tra 1, 2 o 3.")
    
    def _choose_fixed_difficulty(self, words):
        """Chiede il livello per difficoltà fissa"""
        # Mostra statistiche sulla distribuzione
        stats = self.loader.get_difficulty_stats(words)
        print(f"\n📊 Distribuzione difficoltà:")
        for level in sorted(stats.keys()):
            print(f"   Livello {level}: {stats[level]} parole")
        
        while True:
            try:
                level = int(input("\nLivello massimo di difficoltà (1-5): ").strip())
                if 1 <= level <= 5:
                    filtered_words = self.loader.get_words_by_difficulty(words, 'fixed', level)
                    print(f"✅ Selezionate {len(filtered_words)} parole con frequenza ≤ {level}")
                    return 'fixed', level
                else:
                    print("❌ Livello deve essere tra 1 e 5.")
            except ValueError:
                print("❌ Inserisci un numero valido.")
    
    def _choose_focus_difficulty(self, words):
        """Chiede il livello per modalità focus"""
        # Mostra statistiche sulla distribuzione
        stats = self.loader.get_difficulty_stats(words)
        print(f"\n📊 Distribuzione difficoltà:")
        for level in sorted(stats.keys()):
            print(f"   Livello {level}: {stats[level]} parole")
        
        while True:
            try:
                level = int(input("\nLivello di focus (1-5): ").strip())
                if 1 <= level <= 5:
                    filtered_words = self.loader.get_words_by_difficulty(words, 'focus', level)
                    if filtered_words:
                        print(f"✅ Selezionate {len(filtered_words)} parole di livello {level}")
                        return 'focus', level
                    else:
                        print(f"❌ Nessuna parola trovata per il livello {level}.")
                else:
                    print("❌ Livello deve essere tra 1 e 5.")
            except ValueError:
                print("❌ Inserisci un numero valido.")
    
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
            
            if mode in ['Traduzione', 'Traduzione Inversa']:
                result = self._ask_translation(word, mode)
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
    
    def _ask_translation(self, word, mode='Traduzione'):
        """Chiede la traduzione di una parola"""
        if mode == 'Traduzione Inversa':
            print(f"Come si dice '{word.german}' in italiano?")
            correct_answer = word.italian
        else:
            print(f"Come si dice '{word.italian}' in tedesco?")
            correct_answer = word.german
        
        user_answer = input("➤ La tua risposta: ").strip()
        
        # Controlla se l'utente vuole terminare
        if user_answer.lower() == 'n':
            return 'quit'
        
        # Usa sempre il sistema di controllo delle parole per gestire umlaut e ß
        if mode == 'Traduzione Inversa':
            # Per traduzione inversa, crea una parola temporanea per il controllo
            from .word import Word
            temp_word = Word(correct_answer, word.italian)
            is_correct, penalty, feedback = temp_word.check_answer(user_answer)
        else:
            # Per traduzione normale, usa la parola originale
            is_correct, penalty, feedback = word.check_answer(user_answer)
        
        print(feedback)
        
        if is_correct:
            self.total_count += 1
            self.correct_count += 1
            return True
        else:
            self.total_count += 1
            
            self.errors.append({
                'word_german': word.german,
                'word_italian': word.italian,
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'penalty': penalty
            })
            
            return False
    
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
        
        # Calcola punteggio cumulativo (sistema corretto)
        total_penalties = sum(err['penalty'] for err in self.errors)
        effective_score = self.total_count - total_penalties
        success_rate = (effective_score / self.total_count * 100)
        
        print(f"\n✅ Risposte corrette: {self.correct_count}/{self.total_count}")
        print(f"❌ Errori totali: {len(self.errors)}")
        print(f"📈 Punteggio finale: {effective_score:.1f}/{self.total_count}")
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
        
        # Reset dello stato per la prossima partita
        self._reset_game_state()
    
    def _reset_game_state(self):
        """Resetta lo stato del gioco per una nuova partita"""
        self.errors = []
        self.correct_count = 0
        self.total_count = 0