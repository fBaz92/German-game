import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from src.data_loader import DataLoader
from src.database import DatabaseManager
from src.review_mode import ReviewMode
from src.statistics import StatisticsManager
import random
import streamlit.components.v1 as components

# Configurazione della pagina
st.set_page_config(
    page_title="Impara il Tedesco 🇩🇪",
    page_icon="🇩🇪",
    layout="centered"
)

# Inizializzazione dello stato della sessione
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.errors = []
    st.session_state.questions = []
    st.session_state.game_type = None
    st.session_state.mode = None
    st.session_state.feedback_by_q = {}
    st.session_state.graded_q = set()
    st.session_state.main_mode = None  # 'normal', 'study', 'review'
    st.session_state.study_words = []  # Words selected for study mode
    st.session_state.show_study_list = False
    st.session_state.deep_study_started = False
    st.session_state.deep_study = None

# Inizializza last_feedback se non esiste
if 'last_feedback' not in st.session_state:
    st.session_state.last_feedback = None


def reset_game():
    """Reset dello stato del gioco"""
    st.session_state.game_started = False
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.errors = []
    st.session_state.questions = []
    st.session_state.game_type = None
    st.session_state.mode = None
    st.session_state.feedback_by_q = {}
    st.session_state.graded_q = set()
    st.session_state.main_mode = None
    st.session_state.study_words = []
    st.session_state.show_study_list = False


def start_game(game_type, mode, num_questions=10, words_to_use=None):
    """Inizia una nuova partita"""
    if words_to_use is None:
        loader = DataLoader()
        
        # Carica i dati appropriati
        if game_type == "Nomi":
            words = loader.load_nouns()
        elif game_type == "Verbi":
            words = loader.load_verbs()
        else:
            words = loader.load_adjectives()
        
        # Seleziona domande casuali
        st.session_state.questions = random.sample(words, min(num_questions, len(words)))
    else:
        # Usa le parole specificate (per study mode)
        st.session_state.questions = words_to_use
    
    st.session_state.game_type = game_type
    st.session_state.mode = mode
    st.session_state.game_started = True
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.errors = []
    st.session_state.feedback_by_q = {}
    st.session_state.graded_q = set()


def get_words_for_study(game_type, num_words, difficulty_mode='casual', difficulty_level=None):
    """Ottiene le parole per la modalità studio con filtro per difficoltà"""
    loader = DataLoader()
    
    if game_type == "Nomi":
        words = loader.load_nouns()
    elif game_type == "Verbi":
        words = loader.load_verbs()
    else:
        words = loader.load_adjectives()
    
    # Filtra per difficoltà
    filtered_words = loader.get_words_by_difficulty(words, difficulty_mode, difficulty_level)
    
    # Mescola e seleziona le parole
    random.shuffle(filtered_words)
    return filtered_words[:num_words]


def get_review_words(game_type):
    """Ottiene le parole da ripassare"""
    review_mode = ReviewMode()
    words = review_mode.get_words_to_review(game_type, min_errors=1, limit=20)
    return words

def get_words_by_difficulty(words, difficulty_mode, difficulty_level):
    """Filtra le parole in base alla difficoltà"""
    from src.data_loader import DataLoader
    loader = DataLoader()
    return loader.get_words_by_difficulty(words, difficulty_mode, difficulty_level)


def play_deep_study_game(deep_study):
    """Gestisce il gioco dello studio approfondito"""
    st.header(f"🎯 Studio Approfondito - Round {deep_study['round_number']}")
    
    # Mostra progresso
    total_words = len(deep_study['words'])
    # Calcola le parole padroneggiate dal round_results
    mastered_in_round = sum(1 for mastered in deep_study['round_results'].values() if mastered)
    remaining_in_round = len(deep_study['current_round_words'])
    total_in_round = deep_study.get('total_round_words', len(deep_study['words_to_master']))
    
    # Progresso del round corrente
    round_progress = mastered_in_round / total_in_round if total_in_round > 0 else 0
    
    st.progress(round_progress)
    st.info(f"📊 Round {deep_study['round_number']}: {mastered_in_round}/{total_in_round} parole padroneggiate | {remaining_in_round} rimanenti")
    
    # Se il round è in corso, mostra la parola corrente
    if deep_study['round_in_progress'] and deep_study['current_round_words']:
        word_idx, word = deep_study['current_round_words'][0]
        
        # Determina la domanda in base alla modalità
        is_reverse_translation = deep_study['mode'] == 'Traduzione Inversa'
        
        if is_reverse_translation:
            question_text = f"Come si dice **{word.german}** in italiano?"
            correct_answer = word.italian
        else:
            if deep_study['mode'] == 'Traduzione':
                question_text = f"Come si dice **{word.italian}** in tedesco?"
                correct_answer = word.german
            elif deep_study['mode'] == 'Articoli':
                question_text = f"Qual è l'articolo di **{word.german}**?"
                correct_answer = word.article
            elif deep_study['mode'] == 'Coniugazioni':
                question_text = f"Coniuga **{word.italian}** al Präteritum:"
                correct_answer = word.prateritum
        
        st.markdown(f"### 📝 {question_text}")
        
        # Mostra feedback dell'ultima risposta se disponibile
        if st.session_state.last_feedback:
            if st.session_state.last_feedback['type'] == 'success':
                st.success(st.session_state.last_feedback['message'])
            elif st.session_state.last_feedback['type'] == 'warning':
                st.warning(st.session_state.last_feedback['message'])
            elif st.session_state.last_feedback['type'] == 'error':
                st.error(st.session_state.last_feedback['message'])
            elif st.session_state.last_feedback['type'] == 'info':
                st.info(st.session_state.last_feedback['message'])
        
        # Input dell'utente
        if deep_study['mode'] in ['Traduzione', 'Traduzione Inversa']:
            user_answer = st.text_input("La tua risposta:", key=f"deep_study_{word_idx}_{deep_study['round_number']}")
        elif deep_study['mode'] == 'Articoli':
            user_answer = st.radio("Articolo:", ["der", "die", "das"], key=f"deep_study_{word_idx}_{deep_study['round_number']}")
        elif deep_study['mode'] == 'Coniugazioni':
            user_answer = st.text_input("Präteritum:", key=f"deep_study_{word_idx}_{deep_study['round_number']}")
        
        # Controlla se l'utente ha premuto Invio (per text_input)
        enter_pressed = False
        if deep_study['mode'] in ['Traduzione', 'Traduzione Inversa', 'Coniugazioni']:
            # Usa session state per tracciare se è stata inserita una risposta
            input_key = f"deep_study_{word_idx}_{deep_study['round_number']}"
            if st.session_state.get(input_key, "") != "" and not st.session_state.get(f"processed_{input_key}", False):
                enter_pressed = True
                st.session_state[f"processed_{input_key}"] = True
        
        # Pulsanti di controllo
        col1, col2, col3 = st.columns(3)
        
        with col1:
            check_clicked = st.button("✅ Controlla Risposta", type="primary")
            
            if check_clicked or enter_pressed:
                if user_answer.strip():
                    # Controlla la risposta
                    is_correct, penalty = check_answer(user_answer, correct_answer, 
                                                      is_conjugation=(deep_study['mode'] == 'Coniugazioni'),
                                                      is_reverse_translation=is_reverse_translation)
                    
                    # Incrementa i tentativi per questa parola nel round corrente
                    if word_idx not in deep_study['round_attempts']:
                        deep_study['round_attempts'][word_idx] = 0
                    deep_study['round_attempts'][word_idx] += 1
                    deep_study['total_attempts'][word_idx] += 1
                    
                    # Aggiorna il punteggio e salva il risultato del round
                    if is_correct:
                        st.session_state.score += 1
                        
                        # Calcola il numero di tentativi per questa parola nel round corrente
                        attempts_for_word = deep_study['round_attempts'][word_idx]
                        
                        if penalty == 0.0:
                            if attempts_for_word == 1:
                                feedback_message = "🎉 PADRONEGGIATA! Al primo tentativo!"
                                # Traccia se è stata padroneggiata al primo tentativo
                                deep_study['first_try_mastered'].add(word_idx)
                            else:
                                feedback_message = f"🎉 PADRONEGGIATA! Al {attempts_for_word}° tentativo!"
                            feedback_type = 'success'
                        elif penalty == 0.5:
                            feedback_message = "⚠️ QUASI! Attenzione alle maiuscole o umlaut!"
                            feedback_type = 'warning'
                        deep_study['round_results'][word_idx] = True
                    else:
                        feedback_message = f"❌ Sbagliata! Da ripassare nel prossimo round.\n💡 Risposta corretta: **{correct_answer}**"
                        feedback_type = 'error'
                        deep_study['round_results'][word_idx] = False
                        # Incrementa la difficoltà solo se non padroneggiata
                        if word_idx not in deep_study['word_difficulty']:
                            deep_study['word_difficulty'][word_idx] = 0
                        deep_study['word_difficulty'][word_idx] += 1
                    
                    # Salva il feedback per la prossima visualizzazione
                    st.session_state.last_feedback = {
                        'type': feedback_type,
                        'message': feedback_message
                    }
                    
                    # Passa sempre alla parola successiva
                    deep_study['current_round_words'].pop(0)
                    
                    # Reset del flag processed per la prossima parola
                    if deep_study['mode'] in ['Traduzione', 'Traduzione Inversa', 'Coniugazioni']:
                        input_key = f"deep_study_{word_idx}_{deep_study['round_number']}"
                        if f"processed_{input_key}" in st.session_state:
                            del st.session_state[f"processed_{input_key}"]
                    
                    deep_study['total_questions'] += 1
                    st.session_state.deep_study = deep_study
                    st.rerun()
                else:
                    st.warning("⚠️ Inserisci una risposta!")
        
        with col2:
            if st.button("🔍 Vedi Risposta"):
                # Incrementa i tentativi per questa parola nel round corrente
                if word_idx not in deep_study['round_attempts']:
                    deep_study['round_attempts'][word_idx] = 0
                deep_study['round_attempts'][word_idx] += 1
                deep_study['total_attempts'][word_idx] += 1
                
                # Salva il feedback per la prossima visualizzazione
                st.session_state.last_feedback = {
                    'type': 'info',
                    'message': f"💡 Risposta corretta: **{correct_answer}**"
                }
                
                deep_study['round_results'][word_idx] = False
                # Incrementa la difficoltà solo se non padroneggiata
                if word_idx not in deep_study['word_difficulty']:
                    deep_study['word_difficulty'][word_idx] = 0
                deep_study['word_difficulty'][word_idx] += 1
                deep_study['total_questions'] += 1
                # Passa alla parola successiva
                deep_study['current_round_words'].pop(0)
                
                # Reset del flag processed per la prossima parola
                if deep_study['mode'] in ['Traduzione', 'Traduzione Inversa', 'Coniugazioni']:
                    input_key = f"deep_study_{word_idx}_{deep_study['round_number']}"
                    if f"processed_{input_key}" in st.session_state:
                        del st.session_state[f"processed_{input_key}"]
                
                st.session_state.deep_study = deep_study
                st.rerun()
        
        with col3:
            if st.button("⏹️ Termina Studio"):
                # Salva la cronologia del round corrente prima di terminare
                if deep_study['round_results']:
                    deep_study['round_history'][deep_study['round_number']] = {
                        'mastered_words': [word_idx for word_idx, mastered in deep_study['round_results'].items() if mastered],
                        'total_words': len(deep_study['words_to_master']),
                        'first_try_count': len([word_idx for word_idx in deep_study['round_results'].keys() 
                                              if deep_study['round_results'][word_idx] and word_idx in deep_study['first_try_mastered']])
                    }
                
                st.session_state.deep_study_started = False
                st.session_state.deep_study = None
                st.rerun()
    
    # Controlla se il round è completato
    elif not deep_study['round_in_progress'] or not deep_study['current_round_words']:
        # Round completato - mostra risultati e chiedi se continuare
        show_round_results(deep_study)

def show_round_results(deep_study):
    """Mostra i risultati del round e chiede se continuare"""
    st.header(f"📊 Risultati Round {deep_study['round_number']}")
    
    # Calcola statistiche del round
    total_round_words = len(deep_study['words_to_master'])
    mastered_this_round = sum(1 for mastered in deep_study['round_results'].values() if mastered)
    not_mastered_this_round = total_round_words - mastered_this_round
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Parole del Round", total_round_words)
    
    with col2:
        st.metric("✅ Padroneggiate", mastered_this_round)
    
    with col3:
        st.metric("❌ Da Ripassare", not_mastered_this_round)
    
    # Mostra dettagli delle parole
    st.subheader("📋 Dettaglio Parole")
    
    for word_idx, word in deep_study['words_to_master']:
        mastered = deep_study['round_results'].get(word_idx, False)
        attempts = deep_study['total_attempts'].get(word_idx, 0)
        
        if mastered:
            st.success(f"✅ **{word.italian}** → **{word.german}** (PADRONEGGIATA)")
        else:
            st.error(f"❌ **{word.italian}** → **{word.german}** ({attempts} tentativi)")
    
    # Aggiorna le parole da padroneggiare per il prossimo round
    new_words_to_master = [(word_idx, word) for word_idx, word in deep_study['words_to_master'] 
                          if not deep_study['round_results'].get(word_idx, False)]
    
    if new_words_to_master:
        st.info(f"🔄 **Round {deep_study['round_number'] + 1}**: Continuerai con {len(new_words_to_master)} parole")
        
        # Salva la cronologia del round corrente
        deep_study['round_history'][deep_study['round_number']] = {
            'mastered_words': [word_idx for word_idx, mastered in deep_study['round_results'].items() if mastered],
            'total_words': len(deep_study['words_to_master']),
            'first_try_count': len([word_idx for word_idx in deep_study['round_results'].keys() 
                                  if deep_study['round_results'][word_idx] and word_idx in deep_study['first_try_mastered']])
        }
        
        # Prepara automaticamente il prossimo round
        import random
        random.shuffle(new_words_to_master)
        
        deep_study['words_to_master'] = new_words_to_master
        deep_study['current_round_words'] = new_words_to_master.copy()
        deep_study['round_number'] += 1
        deep_study['round_results'] = {}
        deep_study['current_word_attempts'] = 0
        deep_study['round_in_progress'] = True
        deep_study['total_round_words'] = len(new_words_to_master)
        
        # Reset del feedback per il nuovo round
        st.session_state.last_feedback = None
        
        st.session_state.deep_study = deep_study
        st.rerun()
    else:
        st.success("🎉 **Complimenti!** Hai padroneggiato tutte le parole!")
        
        if st.button("🏆 Vedi Risultati Finali", type="primary"):
            # Salva la cronologia del round finale prima di mostrare i risultati
            deep_study['round_history'][deep_study['round_number']] = {
                'mastered_words': [word_idx for word_idx, mastered in deep_study['round_results'].items() if mastered],
                'total_words': len(deep_study['words_to_master']),
                'first_try_count': len([word_idx for word_idx in deep_study['round_results'].keys() 
                                      if deep_study['round_results'][word_idx] and word_idx in deep_study['first_try_mastered']])
            }
            show_deep_study_results(deep_study)

def show_deep_study_results(deep_study):
    """Mostra i risultati dello studio approfondito"""
    st.header("🎯 Risultati Studio Approfondito")
    
    # Statistiche generali
    total_words = len(deep_study['words'])
    total_questions = deep_study['total_questions']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Parole Totali", total_words)
    
    with col2:
        st.metric("Domande Totali", total_questions)
    
    with col3:
        # Conta le parole padroneggiate al primo tentativo in tutti i round
        mastered_first_try = len(deep_study['first_try_mastered'])
        
        st.metric("Padroneggiate al 1° tentativo", f"{mastered_first_try}/{total_words}")
    
    # Calcola tentativi medi
    average_attempts = sum(deep_study['total_attempts'].values()) / total_words if total_words > 0 else 0
    
    st.info(f"📊 **Tentativi medi per parola:** {average_attempts:.1f}")
    
    # Mostra cronologia dei round se disponibile
    if deep_study.get('round_history'):
        st.subheader("📈 Cronologia Round")
        
        round_data = []
        for round_num, round_info in deep_study['round_history'].items():
            round_data.append({
                'Round': round_num,
                'Parole Totali': round_info['total_words'],
                'Padroneggiate': len(round_info['mastered_words']),
                'Al 1° Tentativo': round_info['first_try_count'],
                'Successo %': f"{(len(round_info['mastered_words']) / round_info['total_words'] * 100):.1f}%" if round_info['total_words'] > 0 else "0%"
            })
        
        if round_data:
            import pandas as pd
            df_rounds = pd.DataFrame(round_data)
            st.dataframe(df_rounds, use_container_width=True)
    
    # Classifica delle parole più difficili
    st.subheader("🏆 Classifica Parole Più Difficili")
    
    # Ordina le parole per difficoltà
    sorted_words = sorted(enumerate(deep_study['words']), 
                         key=lambda x: deep_study['total_attempts'][x[0]], reverse=True)
    
    for i, (word_idx, word) in enumerate(sorted_words[:10], 1):
        attempts_needed = deep_study['total_attempts'][word_idx]
        difficulty_emoji = "🔥" if attempts_needed >= 3 else "⚡" if attempts_needed == 2 else "✅"
        
        if deep_study['mode'] in ['Traduzione', 'Traduzione Inversa']:
            st.write(f"{i:2d}. {difficulty_emoji} **{word.italian}** → **{word.german}** ({attempts_needed} tentativi)")
        elif deep_study['mode'] == 'Articoli':
            st.write(f"{i:2d}. {difficulty_emoji} **{word.german}** (articolo: {word.article}) ({attempts_needed} tentativi)")
        elif deep_study['mode'] == 'Coniugazioni':
            st.write(f"{i:2d}. {difficulty_emoji} **{word.italian}** ({attempts_needed} tentativi)")
    
    # Salva nel database
    if st.button("💾 Salva Risultati", type="primary"):
        # Salva nel database
        db = DatabaseManager()
        db.save_game(
            game_type=f"{deep_study['game_type']} (Studio Approfondito)",
            mode=deep_study['mode'],
            total_questions=total_questions,
            correct_answers=total_words,  # Tutte le parole sono state padroneggiate
            errors=[]  # Non usiamo il sistema di errori tradizionale
        )
        st.success("✅ Studio approfondito salvato nel database!")
    
    # Pulsante per nuovo studio
    if st.button("🔄 Nuovo Studio Approfondito"):
        st.session_state.deep_study_started = False
        st.session_state.deep_study = None
        st.rerun()

def show_enhanced_stats():
    """Mostra statistiche avanzate"""
    st.header("📊 Statistiche Avanzate")
    
    db = DatabaseManager()
    stats_manager = StatisticsManager()
    games = db.get_game_history(limit=1000)
    
    if not games:
        st.info("Nessuna partita giocata ancora. Inizia a giocare!")
        return
    
    # Statistiche generali
    st.subheader("🎯 Panoramica Generale")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_games = len(games)
    total_questions = sum(game[4] for game in games)
    total_correct = sum(game[5] for game in games)
    avg_success = sum(game[6] for game in games) / total_games
    
    with col1:
        st.metric("Partite Totali", total_games)
    with col2:
        st.metric("Domande Totali", total_questions)
    with col3:
        st.metric("Risposte Corrette", f"{total_correct}/{total_questions}")
    with col4:
        st.metric("Media Successo", f"{avg_success:.1f}%")
    
    # Miglior partita
    best_game = max(games, key=lambda x: x[6])
    st.info(f"🏆 **Miglior partita**: {best_game[6]:.1f}% di successo ({best_game[2]} - {best_game[3]})")
    
    # Progresso nel tempo
    st.subheader("📈 Progresso nel Tempo")
    
    # Raggruppa per settimana
    weekly_stats = defaultdict(lambda: {'games': 0, 'total_success': 0})
    
    for game in games:
        try:
            # Gestisce diversi formati di timestamp
            if isinstance(game[1], str):
                timestamp = datetime.fromisoformat(game[1])
            elif isinstance(game[1], datetime):
                timestamp = game[1]
            else:
                # Se non è né stringa né datetime, salta questo record
                continue
                
            week_start = timestamp - timedelta(days=timestamp.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            
            weekly_stats[week_key]['games'] += 1
            weekly_stats[week_key]['total_success'] += game[6]
        except (ValueError, TypeError) as e:
            # Salta record con timestamp non validi
            continue
    
    # Mostra ultime 4 settimane
    sorted_weeks = sorted(weekly_stats.items(), reverse=True)[:4]
    
    if sorted_weeks:
        weekly_data = []
        for week, stats in sorted_weeks:
            avg = stats['total_success'] / stats['games']
            weekly_data.append({
                'Settimana': week,
                'Partite': stats['games'],
                'Media Successo (%)': round(avg, 1)
            })
        
        df_weekly = pd.DataFrame(weekly_data)
        st.dataframe(df_weekly, use_container_width=True)
    
    # Analisi per categoria
    st.subheader("📚 Analisi per Categoria")
    
    categories = ['Nomi', 'Verbi', 'Aggettivi']
    category_stats = []
    
    for game_type in categories:
        stats = db.get_stats_by_type(game_type)
        if stats:
            category_stats.append({
                'Categoria': game_type,
                'Partite': stats['games'],
                'Media Successo (%)': round(stats['avg_success'], 1),
                'Parole Studiate': stats['total_questions']
            })
    
    if category_stats:
        df_categories = pd.DataFrame(category_stats)
        st.dataframe(df_categories, use_container_width=True)
    
    # Parole più difficili
    st.subheader("❌ Parole Più Difficili")
    
    errors = db.get_most_common_errors(limit=15)
    if errors:
        error_data = []
        for german, italian, count in errors:
            error_data.append({
                'Tedesco': german,
                'Italiano': italian,
                'Errori': count
            })
        
        df_errors = pd.DataFrame(error_data)
        st.dataframe(df_errors, use_container_width=True)
    else:
        st.success("✨ Nessun errore registrato! Continua così!")
    
    # Streak e record
    st.subheader("🔥 Streak e Record")
    
    # Calcola streak corrente
    dates = []
    for game in games:
        try:
            if isinstance(game[1], str):
                timestamp = datetime.fromisoformat(game[1])
            elif isinstance(game[1], datetime):
                timestamp = game[1]
            else:
                continue
            dates.append(timestamp.date())
        except (ValueError, TypeError):
            continue
    dates = sorted(set(dates), reverse=True)
    
    current_streak = 0
    if dates:
        today = datetime.now().date()
        if dates[0] == today or dates[0] == today - timedelta(days=1):
            current_streak = 1
            for i in range(len(dates) - 1):
                if (dates[i] - dates[i+1]).days == 1:
                    current_streak += 1
                else:
                    break
    
    # Trova la longest streak
    longest_streak = 1
    temp_streak = 1
    for i in range(len(dates) - 1):
        if (dates[i] - dates[i+1]).days == 1:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 1
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Streak Corrente", f"{current_streak} giorni")
    with col2:
        st.metric("Miglior Streak", f"{longest_streak} giorni")
    with col3:
        week_ago = datetime.now() - timedelta(days=7)
        recent_games = []
        for g in games:
            try:
                if isinstance(g[1], str):
                    timestamp = datetime.fromisoformat(g[1])
                elif isinstance(g[1], datetime):
                    timestamp = g[1]
                else:
                    continue
                if timestamp > week_ago:
                    recent_games.append(g)
            except (ValueError, TypeError):
                continue
        st.metric("Partite Questa Settimana", len(recent_games))
    
    # Storico partite
    st.subheader("📋 Storico Partite Recenti")
    df = pd.DataFrame(games, columns=['ID', 'Data', 'Tipo', 'Modalità', 'Domande', 'Corrette', 'Successo%'])
    
    # Gestisce diversi formati di timestamp per la visualizzazione
    try:
        df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        # Se la conversione fallisce, mostra i timestamp come sono
        pass
    
    st.dataframe(df.head(20), use_container_width=True)
    
    # Pulsante per esportare
    if st.button("📥 Esporta Statistiche"):
        filename = f"stats_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        stats_manager.export_statistics(filename)
        st.success(f"Statistiche esportate in {filename}!")


def check_answer(user_answer, correct_answer, is_articles=False, is_conjugation=False, is_reverse_translation=False):
    """Verifica la risposta e calcola la penalità usando il sistema di normalizzazione"""
    from src.word import Word
    from src.normalization import compare_german_words
    
    # Per articoli, confronto semplice
    if is_articles:
        if user_answer.strip().lower() == correct_answer.strip().lower():
            return True, 0.0
        return False, 1.0
    
    # Per coniugazioni verbali, usa il sistema di normalizzazione
    if is_conjugation:
        # Crea una parola temporanea per il controllo
        temp_word = Word(correct_answer, "temp")
        is_correct, penalty, feedback = temp_word.check_answer(user_answer)
        return is_correct, penalty
    
    # Per traduzione inversa (tedesco → italiano), confronto semplice
    if is_reverse_translation:
        if user_answer.strip() == correct_answer.strip():
            return True, 0.0
        elif user_answer.strip().lower() == correct_answer.strip().lower():
            return False, 0.5  # Mezzo errore per maiuscola
        return False, 1.0
    
    # Per traduzione normale (italiano → tedesco), usa il sistema di normalizzazione
    # Crea una parola temporanea per il controllo
    temp_word = Word(correct_answer, "temp")
    is_correct, penalty, feedback = temp_word.check_answer(user_answer)
    return is_correct, penalty


def show_stats():
    """Mostra statistiche dal database"""
    st.header("📊 Statistiche")
    
    db = DatabaseManager()
    games = db.get_game_history(limit=100)
    
    if games:
        df = pd.DataFrame(games, columns=['ID', 'Data', 'Tipo', 'Modalità', 'Domande', 'Corrette', 'Successo%'])
        
        # Statistiche generali
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Partite Totali", len(df))
        with col2:
            st.metric("Media Successo", f"{df['Successo%'].mean():.1f}%")
        with col3:
            total_questions = df['Domande'].sum()
            total_correct = df['Corrette'].sum()
            st.metric("Risposte Corrette", f"{total_correct}/{total_questions}")
        
        # Tabella delle partite
        st.subheader("Storico Partite")
        st.dataframe(df, use_container_width=True)
        
        # Errori più frequenti
        errors = db.get_most_common_errors(limit=10)
        if errors:
            st.subheader("🎯 Parole Più Sbagliate")
            error_df = pd.DataFrame(errors, columns=['Tedesco', 'Italiano', 'N° Errori'])
            st.dataframe(error_df, use_container_width=True)
    else:
        st.info("Nessuna partita giocata ancora. Inizia a giocare!")

# Header principale
st.title("🇩🇪 Impara il Tedesco")
st.caption("Suggerimenti: Premi Invio per verificare. Usa Ctrl+V per 'Vedi risposta'.")
st.markdown("---")

# Inject keyboard shortcut for Ctrl+V to click 'Vedi risposta'
components.html(
    """
    <script>
    document.addEventListener('keydown', function(e) {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC')>=0;
      const ctrl = isMac ? e.metaKey : e.ctrlKey;
      if (ctrl && (e.key === 'v' || e.key === 'V')) {
        const buttons = Array.from(parent.document.querySelectorAll('button'));
        const target = buttons.find(b => b.innerText && b.innerText.includes('Vedi risposta'));
        if (target) { e.preventDefault(); target.click(); }
      }
    });
    </script>
    """,
    height=0,
)

# Sidebar per navigazione
with st.sidebar:
    st.header("Menu")
    page = st.radio("Vai a:", ["🎮 Gioca", "📚 Studio", "🎯 Studio Approfondito", "🔄 Ripasso", "📊 Statistiche", "ℹ️ Info"])
    
    if st.session_state.game_started:
        st.markdown("---")
        st.info(f"**Partita in corso**\n\nTipo: {st.session_state.game_type}\n\nModalità: {st.session_state.mode}\n\nDomanda: {st.session_state.current_question + 1}/{len(st.session_state.questions)}")
        
        if st.button("🔄 Ricomincia", use_container_width=True):
            reset_game()
            st.rerun()

# Pagina Gioca
if page == "🎮 Gioca":
    if not st.session_state.game_started:
        st.header("Inizia una Nuova Partita")
        
        col1, col2 = st.columns(2)
        
        with col1:
            game_type = st.selectbox(
                "Cosa vuoi studiare?",
                ["Nomi", "Verbi", "Aggettivi"]
            )
        
        with col2:
            if game_type == "Nomi":
                mode = st.selectbox(
                    "Modalità",
                    ["Traduzione", "Traduzione Inversa", "Articoli (der/die/das)"]
                )
            elif game_type == "Verbi":
                mode = st.selectbox(
                    "Modalità",
                    ["Traduzione", "Traduzione Inversa", "Coniugazioni (Präteritum/Participio)"]
                )
            else:  # Aggettivi
                mode = st.selectbox(
                    "Modalità",
                    ["Traduzione", "Traduzione Inversa"]
                )
        
        num_questions = st.slider("Numero di domande", 5, 100, 10)
        
        if st.button("▶️ Inizia Partita", type="primary", use_container_width=True):
            start_game(game_type, mode, num_questions)
            st.rerun()
    
    else:
        # Partita in corso
        current_idx = st.session_state.current_question
        
        if current_idx < len(st.session_state.questions):
            word = st.session_state.questions[current_idx]
            
            st.header(f"Domanda {current_idx + 1} di {len(st.session_state.questions)}")
            
            # Progress bar
            progress = current_idx / len(st.session_state.questions)
            st.progress(progress)
            
            # Determina il tipo di modalità
            is_articles = st.session_state.mode.startswith("Articoli")
            is_conjugations = st.session_state.mode.startswith("Coniugazioni")
            is_reverse_translation = st.session_state.mode == "Traduzione Inversa"
            
            # Mostra la domanda
            if is_articles:  # Articoli
                question_text = word.german
                correct_answer = word.article
                st.info(f"**Qual è l'articolo di:** {question_text}")
            elif is_conjugations:  # Coniugazioni verbali
                # Scegli casualmente tra Präteritum e Participio
                conj_type = random.choice(['präteritum', 'participio'])
                if conj_type == 'präteritum':
                    question_text = f"{word.german} ({word.italian})"
                    correct_answer = word.prateritum
                    st.info(f"**Coniuga al Präteritum:** {question_text}")
                else:
                    question_text = f"{word.german} ({word.italian})"
                    correct_answer = word.participio
                    st.info(f"**Participio passato di:** {question_text}")
            elif is_reverse_translation:  # Traduzione Inversa (tedesco → italiano)
                question_text = word.german
                correct_answer = word.italian
                st.info(f"**Traduci in italiano:** {question_text}")
            else:  # Traduzione normale (italiano → tedesco)
                question_text = word.italian
                correct_answer = word.german
                st.info(f"**Traduci in tedesco:** {question_text}")
            
            # Se esiste feedback già mostrato per questa domanda, visualizzalo e mostra solo Avanti/Ricomincia
            feedback = st.session_state.feedback_by_q.get(current_idx)
            if feedback is not None:
                if feedback['ok']:
                    st.success(feedback['message'])
                else:
                    st.error(feedback['message'])
                st.divider()
                cols = st.columns([1, 1])
                with cols[0]:
                    if st.button("⏭️ Prossima", key=f"next_after_feedback_{current_idx}", use_container_width=True):
                        st.session_state.current_question += 1
                        st.rerun()
                with cols[1]:
                    if st.button("🔁 Ricomincia", key=f"restart_after_feedback_{current_idx}", use_container_width=True):
                        reset_game()
                        st.rerun()
            else:
                # Input e azioni
                if not is_articles:
                    with st.form(key=f"form_{current_idx}"):
                        user_answer = st.text_input(
                            "La tua risposta:",
                            key=f"answer_{current_idx}",
                            placeholder="Scrivi qui..."
                        )
                        submitted = st.form_submit_button("✅ Verifica (Invio)")
                        if submitted:
                            ok, penalty = check_answer(user_answer, correct_answer, is_articles, is_conjugations, is_reverse_translation)
                            if ok:
                                st.session_state.score += 1
                                st.session_state.feedback_by_q[current_idx] = {
                                    'ok': True,
                                    'message': "✅ Corretto!"
                                }
                            else:
                                error_type = "maiuscola" if penalty == 1.0 else "umlaut" if penalty == 0.5 else "completo"
                                st.session_state.errors.append({
                                    'word_german': word.german,
                                    'word_italian': word.italian,
                                    'user_answer': user_answer,
                                    'correct_answer': correct_answer,
                                    'penalty': penalty,
                                    'error_type': error_type
                                })
                                # Sistema di punteggio cumulativo: 0.5 punti per mezzo errore, 0 per errore completo
                                if penalty == 0.5:
                                    st.session_state.score += 0.5
                                # 0 punti per errore completo (penalty == 1.0)
                                st.session_state.feedback_by_q[current_idx] = {
                                    'ok': False,
                                    'message': f"❌ Sbagliato! Risposta corretta: {correct_answer}"
                                }
                            st.rerun()
                else:
                    user_answer = st.radio(
                        "Seleziona l'articolo:",
                        ["der", "die", "das"],
                        key=f"answer_{current_idx}"
                    )
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Verifica", key=f"check_{current_idx}", use_container_width=True):
                            ok, penalty = check_answer(user_answer, correct_answer, is_articles)
                            if ok:
                                st.session_state.score += 1
                                st.session_state.feedback_by_q[current_idx] = {
                                    'ok': True,
                                    'message': "✅ Corretto!"
                                }
                            else:
                                error_type = "completo" if penalty == 1.0 else "umlaut"
                                st.session_state.errors.append({
                                    'word_german': word.german,
                                    'word_italian': word.italian,
                                    'user_answer': user_answer,
                                    'correct_answer': correct_answer,
                                    'penalty': penalty,
                                    'error_type': error_type
                                })
                                # Sistema di punteggio cumulativo: 0.5 punti per mezzo errore, 0 per errore completo
                                if penalty == 0.5:
                                    st.session_state.score += 0.5
                                # 0 punti per errore completo (penalty == 1.0)
                                st.session_state.feedback_by_q[current_idx] = {
                                    'ok': False,
                                    'message': f"❌ Sbagliato! Risposta corretta: {correct_answer}"
                                }
                            st.rerun()
                    with col_b:
                        if st.button("👁️ Vedi risposta (Ctrl+V)", key=f"reveal_{current_idx}", use_container_width=True):
                            # Conta come errore completo e mostra la risposta
                            st.session_state.errors.append({
                                'word_german': word.german,
                                'word_italian': word.italian,
                                'user_answer': '(vedi risposta)',
                                'correct_answer': correct_answer,
                                'penalty': 1.0,
                                'error_type': 'rivelata'
                            })
                            # "Vedi risposta" = 0 punti
                            st.session_state.feedback_by_q[current_idx] = {
                                'ok': False,
                                'message': f"👁️ Risposta: {correct_answer} (contata come errore)"
                            }
                            st.rerun()
                # Per la modalità Traduzione aggiungiamo anche il pulsante "Vedi risposta"
                if not is_articles:
                    if st.button("👁️ Vedi risposta (Ctrl+V)", key=f"reveal_txt_{current_idx}", use_container_width=True):
                        st.session_state.errors.append({
                            'word_german': word.german,
                            'word_italian': word.italian,
                            'user_answer': '(vedi risposta)',
                            'correct_answer': correct_answer,
                            'penalty': 1.0,
                            'error_type': 'rivelata'
                        })
                        st.session_state.score -= 1.0
                        st.session_state.feedback_by_q[current_idx] = {
                            'ok': False,
                            'message': f"👁️ Risposta: {correct_answer} (contata come errore)"
                        }
                        st.rerun()
        
        else:
            # Fine partita
            st.header("🎉 Partita Completata!")
            
            total_questions = len(st.session_state.questions)
            max_score = total_questions
            # Punteggio cumulativo: 1 punto per risposta corretta, 0.5 per mezzo errore, 0 per errore completo
            current_score = st.session_state.score
            success_rate = (current_score / max_score * 100) if max_score > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Punteggio", f"{current_score:.1f}/{max_score}")
            with col2:
                st.metric("Errori", len(st.session_state.errors))
            with col3:
                st.metric("Successo", f"{success_rate:.1f}%")
            
            if st.session_state.errors:
                st.subheader("❌ Errori Commessi")
                for i, error in enumerate(st.session_state.errors, 1):
                    with st.expander(f"{i}. {error['word_italian']} → {error['word_german']}"):
                        st.write(f"**Tua risposta:** {error['user_answer']}")
                        st.write(f"**Tipo errore:** {error['error_type']}")
                        st.write(f"**Penalità:** -{error['penalty']}")
            
            # Salva nel database
            db = DatabaseManager()
            db.save_game(
                game_type=st.session_state.game_type,
                mode=st.session_state.mode,
                total_questions=total_questions,
                correct_answers=int(current_score),
                errors=st.session_state.errors,
            )
            
            st.success("💾 Partita salvata nel database!")
            
            if st.button("🔄 Nuova Partita", type="primary", use_container_width=True):
                reset_game()
                st.rerun()

# Pagina Studio
elif page == "📚 Studio":
    if not st.session_state.game_started:
        st.header("📚 Modalità Studio")
        st.markdown("Studia una lista di parole prima di giocare!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            game_type = st.selectbox(
                "Cosa vuoi studiare?",
                ["Nomi", "Verbi", "Aggettivi"],
                key="study_game_type"
            )
        
        with col2:
            if game_type == "Nomi":
                mode = st.selectbox(
                    "Modalità di gioco",
                    ["Traduzione", "Traduzione Inversa", "Articoli (der/die/das)"],
                    key="study_mode"
                )
            elif game_type == "Verbi":
                mode = st.selectbox(
                    "Modalità di gioco",
                    ["Traduzione", "Traduzione Inversa", "Coniugazioni (Präteritum/Participio)"],
                    key="study_mode"
                )
            else:  # Aggettivi
                mode = st.selectbox(
                    "Modalità di gioco",
                    ["Traduzione", "Traduzione Inversa"],
                    key="study_mode"
                )
        
        # Selezione modalità difficoltà
        st.subheader("🎯 Modalità Difficoltà")
        
        difficulty_mode = st.radio(
            "Scegli come selezionare le parole:",
            ["🎲 Casuale", "📊 Difficoltà Fissa", "🎯 Focus"],
            help="Casuale: parole completamente casuali\nDifficoltà Fissa: parole con frequenza ≤ al livello\nFocus: solo parole del livello selezionato"
        )
        
        difficulty_level = None
        if difficulty_mode == "📊 Difficoltà Fissa":
            difficulty_level = st.selectbox(
                "Livello massimo di difficoltà:",
                [1, 2, 3, 4, 5],
                format_func=lambda x: f"Livello {x} (frequenza ≤ {x})",
                help="Include tutte le parole con frequenza ≤ al livello selezionato"
            )
            difficulty_mode = 'fixed'
        elif difficulty_mode == "🎯 Focus":
            difficulty_level = st.selectbox(
                "Livello di focus:",
                [1, 2, 3, 4, 5],
                format_func=lambda x: f"Livello {x} (frequenza = {x})",
                help="Solo parole con frequenza = al livello selezionato"
            )
            difficulty_mode = 'focus'
        else:
            difficulty_mode = 'casual'
        
        # Mostra statistiche sulla distribuzione delle difficoltà
        if game_type:
            loader = DataLoader()
            if game_type == "Nomi":
                all_words = loader.load_nouns()
            elif game_type == "Verbi":
                all_words = loader.load_verbs()
            else:
                all_words = loader.load_adjectives()
            
            stats = loader.get_difficulty_stats(all_words)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Totale Parole", len(all_words))
            with col2:
                st.metric("Livelli Disponibili", len(stats))
            with col3:
                if difficulty_mode == 'fixed' and difficulty_level:
                    filtered = loader.get_words_by_difficulty(all_words, 'fixed', difficulty_level)
                    st.metric("Parole Disponibili", len(filtered))
                elif difficulty_mode == 'focus' and difficulty_level:
                    filtered = loader.get_words_by_difficulty(all_words, 'focus', difficulty_level)
                    st.metric("Parole Disponibili", len(filtered))
                else:
                    st.metric("Modalità", "Casuale")
        
        num_words = st.slider("Numero di parole da studiare", 5, 50, 10)
        
        if st.button("📖 Genera Lista di Studio", type="primary", use_container_width=True):
            st.session_state.study_words = get_words_for_study(game_type, num_words, difficulty_mode, difficulty_level)
            st.session_state.show_study_list = True
            st.rerun()
        
        # Mostra lista di studio se generata
        if st.session_state.show_study_list and st.session_state.study_words:
            st.subheader("📋 Lista di Studio")
            st.markdown("Studia bene queste parole, poi potrai giocare con esse!")
            
            # Mostra le parole in una tabella
            study_data = []
            for i, word in enumerate(st.session_state.study_words, 1):
                row = {
                    'N°': i,
                    'Italiano': word.italian,
                    'Tedesco': word.german,
                    'Frequenza': f"Livello {word.frequency}"
                }
                
                if game_type == 'Nomi' and hasattr(word, 'article'):
                    row['Articolo'] = word.article
                elif game_type == 'Verbi':
                    if hasattr(word, 'prateritum') and word.prateritum:
                        row['Präteritum'] = word.prateritum
                    if hasattr(word, 'participio') and word.participio:
                        row['Participio'] = word.participio
                
                study_data.append(row)
            
            df_study = pd.DataFrame(study_data)
            st.dataframe(df_study, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎮 Inizia Partita", type="primary", use_container_width=True):
                    start_game(game_type, mode, len(st.session_state.study_words), st.session_state.study_words)
                    st.rerun()
            
            with col2:
                if st.button("🔄 Nuova Lista", use_container_width=True):
                    st.session_state.show_study_list = False
                    st.session_state.study_words = []
                    st.rerun()
    
    else:
        # Mostra il gioco in corso (stesso codice della pagina principale)
        current_idx = st.session_state.current_question
        
        if current_idx < len(st.session_state.questions):
            word = st.session_state.questions[current_idx]
            
            st.header(f"Domanda {current_idx + 1} di {len(st.session_state.questions)}")
            
            # Progress bar
            progress = current_idx / len(st.session_state.questions)
            st.progress(progress)
            
            # Determina il tipo di modalità
            is_articles = st.session_state.mode.startswith("Articoli")
            is_conjugations = st.session_state.mode.startswith("Coniugazioni")
            is_reverse_translation = st.session_state.mode == "Traduzione Inversa"
            
            # Mostra la domanda
            if is_articles:  # Articoli
                question_text = word.german
                correct_answer = word.article
                st.info(f"**Qual è l'articolo di:** {question_text}")
            elif is_conjugations:  # Coniugazioni verbali
                # Scegli casualmente tra Präteritum e Participio
                conj_type = random.choice(['präteritum', 'participio'])
                if conj_type == 'präteritum':
                    question_text = f"{word.german} ({word.italian})"
                    correct_answer = word.prateritum
                    st.info(f"**Coniuga al Präteritum:** {question_text}")
                else:
                    question_text = f"{word.german} ({word.italian})"
                    correct_answer = word.participio
                    st.info(f"**Participio passato di:** {question_text}")
            elif is_reverse_translation:  # Traduzione Inversa (tedesco → italiano)
                question_text = word.german
                correct_answer = word.italian
                st.info(f"**Traduci in italiano:** {question_text}")
            else:  # Traduzione normale (italiano → tedesco)
                question_text = word.italian
                correct_answer = word.german
                st.info(f"**Traduci in tedesco:** {question_text}")
            
            # Se esiste feedback già mostrato per questa domanda, visualizzalo e mostra solo Avanti/Ricomincia
            feedback = st.session_state.feedback_by_q.get(current_idx)
            if feedback is not None:
                if feedback['ok']:
                    st.success(feedback['message'])
                else:
                    st.error(feedback['message'])
                st.divider()
                cols = st.columns([1, 1])
                with cols[0]:
                    if st.button("⏭️ Prossima", key=f"next_after_feedback_{current_idx}", use_container_width=True):
                        st.session_state.current_question += 1
                        st.rerun()
                with cols[1]:
                    if st.button("🔁 Ricomincia", key=f"restart_after_feedback_{current_idx}", use_container_width=True):
                        reset_game()
                        st.rerun()
            else:
                # Input e azioni (stesso codice della pagina principale)
                if not is_articles:
                    with st.form(key=f"form_{current_idx}"):
                        user_answer = st.text_input(
                            "La tua risposta:",
                            key=f"answer_{current_idx}",
                            placeholder="Scrivi qui..."
                        )
                        submitted = st.form_submit_button("✅ Verifica (Invio)")
                        if submitted:
                            ok, penalty = check_answer(user_answer, correct_answer, is_articles, is_conjugations, is_reverse_translation)
                            if ok:
                                st.session_state.score += 1
                                st.session_state.feedback_by_q[current_idx] = {
                                    'ok': True,
                                    'message': "✅ Corretto!"
                                }
                            else:
                                error_type = "maiuscola" if penalty == 1.0 else "umlaut" if penalty == 0.5 else "completo"
                                st.session_state.errors.append({
                                    'word_german': word.german,
                                    'word_italian': word.italian,
                                    'user_answer': user_answer,
                                    'correct_answer': correct_answer,
                                    'penalty': penalty,
                                    'error_type': error_type
                                })
                                # Sistema di punteggio cumulativo: 0.5 punti per mezzo errore, 0 per errore completo
                                if penalty == 0.5:
                                    st.session_state.score += 0.5
                                # 0 punti per errore completo (penalty == 1.0)
                                st.session_state.feedback_by_q[current_idx] = {
                                    'ok': False,
                                    'message': f"❌ Sbagliato! Risposta corretta: {correct_answer}"
                                }
                            st.rerun()
                else:
                    user_answer = st.radio(
                        "Seleziona l'articolo:",
                        ["der", "die", "das"],
                        key=f"answer_{current_idx}"
                    )
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Verifica", key=f"check_{current_idx}", use_container_width=True):
                            ok, penalty = check_answer(user_answer, correct_answer, is_articles, is_conjugations, is_reverse_translation)
                            if ok:
                                st.session_state.score += 1
                                st.session_state.feedback_by_q[current_idx] = {
                                    'ok': True,
                                    'message': "✅ Corretto!"
                                }
                            else:
                                error_type = "completo" if penalty == 1.0 else "umlaut"
                                st.session_state.errors.append({
                                    'word_german': word.german,
                                    'word_italian': word.italian,
                                    'user_answer': user_answer,
                                    'correct_answer': correct_answer,
                                    'penalty': penalty,
                                    'error_type': error_type
                                })
                                # Sistema di punteggio cumulativo: 0.5 punti per mezzo errore, 0 per errore completo
                                if penalty == 0.5:
                                    st.session_state.score += 0.5
                                # 0 punti per errore completo (penalty == 1.0)
                                st.session_state.feedback_by_q[current_idx] = {
                                    'ok': False,
                                    'message': f"❌ Sbagliato! Risposta corretta: {correct_answer}"
                                }
                            st.rerun()
                    with col_b:
                        if st.button("👁️ Vedi risposta (Ctrl+V)", key=f"reveal_{current_idx}", use_container_width=True):
                            # Conta come errore completo e mostra la risposta
                            st.session_state.errors.append({
                                'word_german': word.german,
                                'word_italian': word.italian,
                                'user_answer': '(vedi risposta)',
                                'correct_answer': correct_answer,
                                'penalty': 1.0,
                                'error_type': 'rivelata'
                            })
                            # "Vedi risposta" = 0 punti
                            st.session_state.feedback_by_q[current_idx] = {
                                'ok': False,
                                'message': f"👁️ Risposta: {correct_answer} (contata come errore)"
                            }
                            st.rerun()
                
                # Per la modalità Traduzione aggiungiamo anche il pulsante "Vedi risposta"
                if not is_articles:
                    if st.button("👁️ Vedi risposta (Ctrl+V)", key=f"reveal_txt_{current_idx}", use_container_width=True):
                        st.session_state.errors.append({
                            'word_german': word.german,
                            'word_italian': word.italian,
                            'user_answer': '(vedi risposta)',
                            'correct_answer': correct_answer,
                            'penalty': 1.0,
                            'error_type': 'rivelata'
                        })
                        st.session_state.score -= 1.0
                        st.session_state.feedback_by_q[current_idx] = {
                            'ok': False,
                            'message': f"👁️ Risposta: {correct_answer} (contata come errore)"
                        }
                        st.rerun()
        
        else:
            # Fine partita (stesso codice della pagina principale)
            st.header("🎉 Partita Completata!")
            
            total_questions = len(st.session_state.questions)
            max_score = total_questions
            # Punteggio cumulativo: 1 punto per risposta corretta, 0.5 per mezzo errore, 0 per errore completo
            current_score = st.session_state.score
            success_rate = (current_score / max_score * 100) if max_score > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Punteggio", f"{current_score:.1f}/{max_score}")
            with col2:
                st.metric("Errori", len(st.session_state.errors))
            with col3:
                st.metric("Successo", f"{success_rate:.1f}%")
            
            if st.session_state.errors:
                st.subheader("❌ Errori Commessi")
                for i, error in enumerate(st.session_state.errors, 1):
                    with st.expander(f"{i}. {error['word_italian']} → {error['word_german']}"):
                        st.write(f"**Tua risposta:** {error['user_answer']}")
                        st.write(f"**Tipo errore:** {error['error_type']}")
                        st.write(f"**Penalità:** -{error['penalty']}")
            
            # Salva nel database
            db = DatabaseManager()
            db.save_game(
                game_type=f"{st.session_state.game_type} (Studio)",
                mode=st.session_state.mode,
                total_questions=total_questions,
                correct_answers=int(current_score),
                errors=st.session_state.errors,
            )
            
            st.success("💾 Partita salvata nel database!")
            
            if st.button("🔄 Nuova Partita", type="primary", use_container_width=True):
                reset_game()
                st.rerun()

# Pagina Ripasso
elif page == "🎯 Studio Approfondito":
    st.header("🎯 Studio Approfondito")
    st.info("💡 Continuerai fino a quando non padroneggi TUTTE le parole!")
    
    # Selezione tipo di gioco
    game_type = st.selectbox("Scegli cosa studiare:", ["Nomi", "Verbi", "Aggettivi"])
    
    # Carica le parole (usiamo un numero alto per ottenere tutte le parole disponibili)
    words = get_words_for_study(game_type, 1000)
    
    if words:
        # Selezione modalità di gioco
        mode = st.selectbox(
            "Modalità di gioco:",
            ["Traduzione", "Traduzione Inversa", "Articoli", "Coniugazioni"] if game_type == "Nomi" 
            else ["Traduzione", "Traduzione Inversa", "Coniugazioni"] if game_type == "Verbi"
            else ["Traduzione", "Traduzione Inversa"]
        )
        
        # Selezione difficoltà
        difficulty_mode = st.radio(
            "Modalità difficoltà:",
            ["Casuale", "Difficoltà Fissa", "Focus"]
        )
        
        difficulty_level = None
        if difficulty_mode != "Casuale":
            difficulty_level = st.selectbox("Livello di difficoltà:", [1, 2, 3, 4, 5])
        
        # Filtra le parole
        filtered_words = get_words_by_difficulty(words, 
                                               "casual" if difficulty_mode == "Casuale" else "fixed" if difficulty_mode == "Difficoltà Fissa" else "focus", 
                                               difficulty_level)
        
        if filtered_words:
            # Selezione numero di parole - ora mostra tutte le parole disponibili
            max_words = len(filtered_words)  # Usa tutte le parole disponibili nel filtro
            study_count = st.slider("Quante parole studiare:", 1, max_words, min(10, max_words))
            
            st.info(f"📊 Parole disponibili: {len(filtered_words)} | Selezionate: {study_count}")
            
            if st.button("🎯 Inizia Studio Approfondito", type="primary"):
                # Mescola e seleziona le parole
                import random
                random.shuffle(filtered_words)
                selected_words = filtered_words[:study_count]
                
                # Inizializza stato per studio approfondito
                st.session_state.deep_study = {
                    'words': selected_words,
                    'game_type': game_type,
                    'mode': mode,
                    'word_difficulty': {i: 0 for i, word in enumerate(selected_words)},
                    'words_to_master': list(enumerate(selected_words)),
                    'round_number': 1,
                    'total_questions': 0,
                    'current_word_idx': 0,
                    'current_word_attempts': 0,
                    'mastered_words': set(),
                    'round_in_progress': True,
                    'round_results': {},
                    'current_round_words': list(enumerate(selected_words)),
                    'total_round_words': len(selected_words),  # Traccia il numero totale di parole nel round
                    'round_attempts': {},  # Traccia i tentativi per parola nel round corrente
                    'total_attempts': {i: 0 for i, word in enumerate(selected_words)},  # Traccia i tentativi totali per parola
                    'first_try_mastered': set(),  # Traccia le parole padroneggiate al primo tentativo
                    'round_history': {}  # Traccia i risultati per ogni round
                }
                st.session_state.deep_study_started = True
                st.session_state.last_feedback = None  # Reset del feedback
                st.rerun()
        
        else:
            st.warning("❌ Nessuna parola disponibile per i criteri selezionati.")
    
    else:
        st.error("❌ Errore nel caricamento delle parole.")

# Gestione gioco studio approfondito
if st.session_state.deep_study_started and st.session_state.deep_study:
    deep_study = st.session_state.deep_study
    
    # Controlla se ci sono ancora parole da padroneggiare
    if not deep_study['words_to_master']:
        # Tutte le parole sono state padroneggiate - mostra risultati
        show_deep_study_results(deep_study)
    else:
        # Continua il gioco
        play_deep_study_game(deep_study)

elif page == "🔄 Ripasso":
    if not st.session_state.game_started:
        st.header("🔄 Modalità Ripasso")
        st.markdown("Ripassa le parole che hai sbagliato più spesso!")
        
        game_type = st.selectbox(
            "Cosa vuoi ripassare?",
            ["Nomi", "Verbi", "Aggettivi"],
            key="review_game_type"
        )
        
        if game_type == "Nomi":
            mode = st.selectbox(
                "Modalità di ripasso",
                ["Traduzione", "Traduzione Inversa", "Articoli (der/die/das)"],
                key="review_mode"
            )
        elif game_type == "Verbi":
            mode = st.selectbox(
                "Modalità di ripasso",
                ["Traduzione", "Traduzione Inversa", "Coniugazioni (Präteritum/Participio)"],
                key="review_mode"
            )
        else:  # Aggettivi
            mode = st.selectbox(
                "Modalità di ripasso",
                ["Traduzione", "Traduzione Inversa"],
                key="review_mode"
            )
        
        if st.button("🔍 Trova Parole da Ripassare", type="primary", use_container_width=True):
            review_words = get_review_words(game_type)
            
            if review_words:
                st.session_state.questions = review_words
                st.session_state.game_type = game_type
                st.session_state.mode = mode
                st.session_state.game_started = True
                st.session_state.current_question = 0
                st.session_state.score = 0
                st.session_state.errors = []
                st.session_state.feedback_by_q = {}
                st.session_state.graded_q = set()
                st.session_state.main_mode = 'review'
                st.rerun()
            else:
                st.info("✨ Complimenti! Non hai errori da ripassare per questa categoria. Prova a giocare più partite per accumulare dati.")
    
    else:
        # Mostra il gioco in corso (stesso codice della pagina principale)
        current_idx = st.session_state.current_question
        
        if current_idx < len(st.session_state.questions):
            word = st.session_state.questions[current_idx]
            
            st.header(f"Ripasso {current_idx + 1} di {len(st.session_state.questions)}")
            st.caption("Queste sono le parole che hai sbagliato più spesso")
            
            # Progress bar
            progress = current_idx / len(st.session_state.questions)
            st.progress(progress)
            
            # Determina il tipo di modalità
            is_articles = st.session_state.mode.startswith("Articoli")
            is_conjugations = st.session_state.mode.startswith("Coniugazioni")
            is_reverse_translation = st.session_state.mode == "Traduzione Inversa"
            
            # Mostra la domanda
            if is_articles:  # Articoli
                question_text = word.german
                correct_answer = word.article
                st.info(f"**Qual è l'articolo di:** {question_text}")
            elif is_conjugations:  # Coniugazioni verbali
                # Scegli casualmente tra Präteritum e Participio
                conj_type = random.choice(['präteritum', 'participio'])
                if conj_type == 'präteritum':
                    question_text = f"{word.german} ({word.italian})"
                    correct_answer = word.prateritum
                    st.info(f"**Coniuga al Präteritum:** {question_text}")
                else:
                    question_text = f"{word.german} ({word.italian})"
                    correct_answer = word.participio
                    st.info(f"**Participio passato di:** {question_text}")
            elif is_reverse_translation:  # Traduzione Inversa (tedesco → italiano)
                question_text = word.german
                correct_answer = word.italian
                st.info(f"**Traduci in italiano:** {question_text}")
            else:  # Traduzione normale (italiano → tedesco)
                question_text = word.italian
                correct_answer = word.german
                st.info(f"**Traduci in tedesco:** {question_text}")
            
            # Se esiste feedback già mostrato per questa domanda, visualizzalo e mostra solo Avanti/Ricomincia
            feedback = st.session_state.feedback_by_q.get(current_idx)
            if feedback is not None:
                if feedback['ok']:
                    st.success(feedback['message'])
                else:
                    st.error(feedback['message'])
                st.divider()
                cols = st.columns([1, 1])
                with cols[0]:
                    if st.button("⏭️ Prossima", key=f"next_after_feedback_{current_idx}", use_container_width=True):
                        st.session_state.current_question += 1
                        st.rerun()
                with cols[1]:
                    if st.button("🔁 Ricomincia", key=f"restart_after_feedback_{current_idx}", use_container_width=True):
                        reset_game()
                        st.rerun()
            else:
                # Input e azioni (stesso codice della pagina principale)
                if not is_articles:
                    with st.form(key=f"form_{current_idx}"):
                        user_answer = st.text_input(
                            "La tua risposta:",
                            key=f"answer_{current_idx}",
                            placeholder="Scrivi qui..."
                        )
                        submitted = st.form_submit_button("✅ Verifica (Invio)")
                        if submitted:
                            ok, penalty = check_answer(user_answer, correct_answer, is_articles, is_conjugations, is_reverse_translation)
                            if ok:
                                st.session_state.score += 1
                                st.session_state.feedback_by_q[current_idx] = {
                                    'ok': True,
                                    'message': "✅ Corretto!"
                                }
                            else:
                                error_type = "maiuscola" if penalty == 1.0 else "umlaut" if penalty == 0.5 else "completo"
                                st.session_state.errors.append({
                                    'word_german': word.german,
                                    'word_italian': word.italian,
                                    'user_answer': user_answer,
                                    'correct_answer': correct_answer,
                                    'penalty': penalty,
                                    'error_type': error_type
                                })
                                # Sistema di punteggio cumulativo: 0.5 punti per mezzo errore, 0 per errore completo
                                if penalty == 0.5:
                                    st.session_state.score += 0.5
                                # 0 punti per errore completo (penalty == 1.0)
                                st.session_state.feedback_by_q[current_idx] = {
                                    'ok': False,
                                    'message': f"❌ Sbagliato! Risposta corretta: {correct_answer}"
                                }
                            st.rerun()
                else:
                    user_answer = st.radio(
                        "Seleziona l'articolo:",
                        ["der", "die", "das"],
                        key=f"answer_{current_idx}"
                    )
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Verifica", key=f"check_{current_idx}", use_container_width=True):
                            ok, penalty = check_answer(user_answer, correct_answer, is_articles, is_conjugations, is_reverse_translation)
                            if ok:
                                st.session_state.score += 1
                                st.session_state.feedback_by_q[current_idx] = {
                                    'ok': True,
                                    'message': "✅ Corretto!"
                                }
                            else:
                                error_type = "completo" if penalty == 1.0 else "umlaut"
                                st.session_state.errors.append({
                                    'word_german': word.german,
                                    'word_italian': word.italian,
                                    'user_answer': user_answer,
                                    'correct_answer': correct_answer,
                                    'penalty': penalty,
                                    'error_type': error_type
                                })
                                # Sistema di punteggio cumulativo: 0.5 punti per mezzo errore, 0 per errore completo
                                if penalty == 0.5:
                                    st.session_state.score += 0.5
                                # 0 punti per errore completo (penalty == 1.0)
                                st.session_state.feedback_by_q[current_idx] = {
                                    'ok': False,
                                    'message': f"❌ Sbagliato! Risposta corretta: {correct_answer}"
                                }
                            st.rerun()
                    with col_b:
                        if st.button("👁️ Vedi risposta (Ctrl+V)", key=f"reveal_{current_idx}", use_container_width=True):
                            # Conta come errore completo e mostra la risposta
                            st.session_state.errors.append({
                                'word_german': word.german,
                                'word_italian': word.italian,
                                'user_answer': '(vedi risposta)',
                                'correct_answer': correct_answer,
                                'penalty': 1.0,
                                'error_type': 'rivelata'
                            })
                            # "Vedi risposta" = 0 punti
                            st.session_state.feedback_by_q[current_idx] = {
                                'ok': False,
                                'message': f"👁️ Risposta: {correct_answer} (contata come errore)"
                            }
                            st.rerun()
                
                # Per la modalità Traduzione aggiungiamo anche il pulsante "Vedi risposta"
                if not is_articles:
                    if st.button("👁️ Vedi risposta (Ctrl+V)", key=f"reveal_txt_{current_idx}", use_container_width=True):
                        st.session_state.errors.append({
                            'word_german': word.german,
                            'word_italian': word.italian,
                            'user_answer': '(vedi risposta)',
                            'correct_answer': correct_answer,
                            'penalty': 1.0,
                            'error_type': 'rivelata'
                        })
                        st.session_state.score -= 1.0
                        st.session_state.feedback_by_q[current_idx] = {
                            'ok': False,
                            'message': f"👁️ Risposta: {correct_answer} (contata come errore)"
                        }
                        st.rerun()
        
        else:
            # Fine partita (stesso codice della pagina principale)
            st.header("🎉 Ripasso Completato!")
            
            total_questions = len(st.session_state.questions)
            max_score = total_questions
            # Punteggio cumulativo: 1 punto per risposta corretta, 0.5 per mezzo errore, 0 per errore completo
            current_score = st.session_state.score
            success_rate = (current_score / max_score * 100) if max_score > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Punteggio", f"{current_score:.1f}/{max_score}")
            with col2:
                st.metric("Errori", len(st.session_state.errors))
            with col3:
                st.metric("Successo", f"{success_rate:.1f}%")
            
            if st.session_state.errors:
                st.subheader("❌ Errori da Ripassare Ancora")
                for i, error in enumerate(st.session_state.errors, 1):
                    with st.expander(f"{i}. {error['word_italian']} → {error['word_german']}"):
                        st.write(f"**Tua risposta:** {error['user_answer']}")
                        st.write(f"**Tipo errore:** {error['error_type']}")
                        st.write(f"**Penalità:** -{error['penalty']}")
            
            # Salva nel database
            db = DatabaseManager()
            db.save_game(
                game_type=f"{st.session_state.game_type} (Ripasso)",
                mode=st.session_state.mode,
                total_questions=total_questions,
                correct_answers=int(current_score),
                errors=st.session_state.errors,
            )
            
            st.success("💾 Sessione di ripasso salvata!")
            
            if st.button("🔄 Nuovo Ripasso", type="primary", use_container_width=True):
                reset_game()
                st.rerun()

# Pagina Statistiche
elif page == "📊 Statistiche":
    show_enhanced_stats()

# Pagina Info
else:
    st.header("ℹ️ Informazioni")
    
    st.markdown(
        """
        ### 🎮 Modalità di Gioco
        
        **1. Partita Normale**
        - Scegli categoria e modalità
        - Gioca con parole casuali
        - Ideale per sessioni veloci
        
        **2. 📚 Modalità Studio**
        - Genera una lista di parole da studiare
        - **🎲 Casuale**: parole completamente casuali
        - **📊 Difficoltà Fissa**: parole con frequenza ≤ al livello selezionato
        - **🎯 Focus**: solo parole del livello di frequenza selezionato
        - Studia prima di giocare con le parole selezionate
        
        **3. 🔄 Modalità Ripasso**
        - Ripassa le parole che hai sbagliato più spesso
        - Basata sui tuoi errori precedenti
        - Ideale per consolidare l'apprendimento
        
        ### 🎯 Modalità Disponibili
        
        **Traduzione**: Traduci dall'italiano al tedesco
        **Traduzione Inversa**: Traduci dal tedesco all'italiano
        **Articoli** (solo nomi): Indovina l'articolo corretto (der/die/das)
        **Coniugazioni** (solo verbi): Präteritum e Participio passato
        
        ### ⚡ Controlli Rapidi
        
        - **Invio**: Verifica la risposta
        - **Ctrl+V**: Vedi risposta (conta come errore)
        
        ### 📊 Sistema di Punteggio
        
        - ✅ **Risposta corretta**: +1 punto
        - ❌ **Errore maiuscola** (nomi, traduzione normale): -1 punto
        - ⚠️ **Errore maiuscola** (traduzione inversa, coniugazioni): -0.5 punti
        - ⚠️ **Errore umlaut** (ä, ö, ü, ß): -0.5 punti
        - ❌ **Errore completo**: -1 punto
        - 👁️ **Vedi risposta**: -1 punto
        
        ### 🎯 Sistema di Difficoltà
        
        Le parole sono classificate per frequenza d'uso (1-5):
        - **Livello 1**: Parole molto comuni (essere, avere, tempo, etc.)
        - **Livello 2**: Parole comuni
        - **Livello 3**: Parole di uso medio
        - **Livello 4**: Parole meno comuni
        - **Livello 5**: Parole rare/specialistiche
        
        ### 📈 Statistiche Avanzate
        
        - Panoramica generale delle prestazioni
        - Progresso nel tempo (settimanale)
        - Analisi per categoria
        - Parole più difficili
        - Streak di gioco e record
        - Esportazione dati
        
        ---
        
        **Viel Erfolg beim Deutschlernen! 🎓**
        """
    )