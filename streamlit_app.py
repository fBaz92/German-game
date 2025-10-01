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


def get_words_for_study(game_type, num_words):
    """Ottiene le parole per la modalità studio"""
    loader = DataLoader()
    
    if game_type == "Nomi":
        words = loader.load_nouns()
    elif game_type == "Verbi":
        words = loader.load_verbs()
    else:
        words = loader.load_adjectives()
    
    # Mescola e seleziona le parole
    random.shuffle(words)
    return words[:num_words]


def get_review_words(game_type):
    """Ottiene le parole da ripassare"""
    review_mode = ReviewMode()
    words = review_mode.get_words_to_review(game_type, min_errors=1, limit=20)
    return words


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
        timestamp = datetime.fromisoformat(game[1])
        week_start = timestamp - timedelta(days=timestamp.weekday())
        week_key = week_start.strftime("%Y-%m-%d")
        
        weekly_stats[week_key]['games'] += 1
        weekly_stats[week_key]['total_success'] += game[6]
    
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
    dates = [datetime.fromisoformat(game[1]).date() for game in games]
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
        recent_games = [g for g in games if datetime.fromisoformat(g[1]) > week_ago]
        st.metric("Partite Questa Settimana", len(recent_games))
    
    # Storico partite
    st.subheader("📋 Storico Partite Recenti")
    df = pd.DataFrame(games, columns=['ID', 'Data', 'Tipo', 'Modalità', 'Domande', 'Corrette', 'Successo%'])
    df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%Y-%m-%d %H:%M')
    st.dataframe(df.head(20), use_container_width=True)
    
    # Pulsante per esportare
    if st.button("📥 Esporta Statistiche"):
        filename = f"stats_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        stats_manager.export_statistics(filename)
        st.success(f"Statistiche esportate in {filename}!")


def check_answer(user_answer, correct_answer, is_articles=False, is_conjugation=False):
    """Verifica la risposta e calcola la penalità"""
    if user_answer.strip() == correct_answer.strip():
        return True, 0.0
    
    # Per coniugazioni verbali, confronto più flessibile
    if is_conjugation:
        if user_answer.strip().lower() == correct_answer.strip().lower():
            return False, 0.5  # Mezzo errore per maiuscola nelle coniugazioni
        return False, 1.0  # Errore completo per coniugazioni
    
    # Controlla errori di maiuscola nei sostantivi (solo traduzione)
    if st.session_state.game_type == "Nomi" and not is_articles:
        if user_answer.strip().lower() == correct_answer.strip().lower():
            return False, 1.0  # Errore completo per maiuscola
    
    # Controlla errori umlaut
    umlaut_map = {'ä': 'a', 'ö': 'o', 'ü': 'u', 'Ä': 'A', 'Ö': 'O', 'Ü': 'U', 'ß': 'ss'}
    user_normalized = user_answer
    correct_normalized = correct_answer
    for umlaut, replacement in umlaut_map.items():
        user_normalized = user_normalized.replace(umlaut, replacement)
        correct_normalized = correct_normalized.replace(umlaut, replacement)
    if user_normalized.strip() == correct_normalized.strip():
        return False, 0.5  # Mezzo errore per umlaut
    
    return False, 1.0  # Errore completo


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
    page = st.radio("Vai a:", ["🎮 Gioca", "📚 Studio", "🔄 Ripasso", "📊 Statistiche", "ℹ️ Info"])
    
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
                    ["Traduzione", "Articoli (der/die/das)"]
                )
            elif game_type == "Verbi":
                mode = st.selectbox(
                    "Modalità",
                    ["Traduzione", "Coniugazioni (Präteritum/Participio)"]
                )
            else:  # Aggettivi
                mode = "Traduzione"
                st.selectbox("Modalità", ["Traduzione"], disabled=True)
        
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
            else:  # Traduzione
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
                            ok, penalty = check_answer(user_answer, correct_answer, is_articles, is_conjugations)
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
                                st.session_state.score -= penalty
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
                                st.session_state.score -= penalty
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
                            st.session_state.score -= 1.0
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
            current_score = max(0, st.session_state.score)
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
                    ["Traduzione", "Articoli (der/die/das)"],
                    key="study_mode"
                )
            elif game_type == "Verbi":
                mode = st.selectbox(
                    "Modalità di gioco",
                    ["Traduzione", "Coniugazioni (Präteritum/Participio)"],
                    key="study_mode"
                )
            else:  # Aggettivi
                mode = "Traduzione"
                st.selectbox("Modalità di gioco", ["Traduzione"], disabled=True, key="study_mode")
        
        num_words = st.slider("Numero di parole da studiare", 5, 50, 10)
        
        if st.button("📖 Genera Lista di Studio", type="primary", use_container_width=True):
            st.session_state.study_words = get_words_for_study(game_type, num_words)
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
                    'Tedesco': word.german
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
            else:  # Traduzione
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
                            ok, penalty = check_answer(user_answer, correct_answer, is_articles, is_conjugations)
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
                                st.session_state.score -= penalty
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
                            ok, penalty = check_answer(user_answer, correct_answer, is_articles, is_conjugations)
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
                                st.session_state.score -= penalty
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
                            st.session_state.score -= 1.0
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
            current_score = max(0, st.session_state.score)
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
                ["Traduzione", "Articoli (der/die/das)"],
                key="review_mode"
            )
        elif game_type == "Verbi":
            mode = st.selectbox(
                "Modalità di ripasso",
                ["Traduzione", "Coniugazioni (Präteritum/Participio)"],
                key="review_mode"
            )
        else:  # Aggettivi
            mode = "Traduzione"
            st.selectbox("Modalità di ripasso", ["Traduzione"], disabled=True, key="review_mode")
        
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
            else:  # Traduzione
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
                            ok, penalty = check_answer(user_answer, correct_answer, is_articles, is_conjugations)
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
                                st.session_state.score -= penalty
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
                            ok, penalty = check_answer(user_answer, correct_answer, is_articles, is_conjugations)
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
                                st.session_state.score -= penalty
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
                            st.session_state.score -= 1.0
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
            current_score = max(0, st.session_state.score)
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
        - Studia prima di giocare
        - Perfetta per apprendimento mirato
        
        **3. 🔄 Modalità Ripasso**
        - Ripassa le parole che hai sbagliato più spesso
        - Basata sui tuoi errori precedenti
        - Ideale per consolidare l'apprendimento
        
        ### 🎯 Modalità Disponibili
        
        **Traduzione**: Traduci dall'italiano al tedesco
        **Articoli** (solo nomi): Indovina l'articolo corretto (der/die/das)
        **Coniugazioni** (solo verbi): Präteritum e Participio passato
        
        ### ⚡ Controlli Rapidi
        
        - **Invio**: Verifica la risposta
        - **Ctrl+V**: Vedi risposta (conta come errore)
        
        ### 📊 Sistema di Punteggio
        
        - ✅ **Risposta corretta**: +1 punto
        - ❌ **Errore maiuscola** (nei nomi): -1 punto
        - ⚠️ **Errore umlaut** (ä, ö, ü, ß): -0.5 punti
        - ❌ **Errore completo**: -1 punto
        - 👁️ **Vedi risposta**: -1 punto
        
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