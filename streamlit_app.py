import streamlit as st
import pandas as pd
from datetime import datetime
from src.data_loader import DataLoader
from src.database import DatabaseManager
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


def start_game(game_type, mode, num_questions=10):
    """Inizia una nuova partita"""
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
    st.session_state.game_type = game_type
    st.session_state.mode = mode
    st.session_state.game_started = True
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.errors = []
    st.session_state.feedback_by_q = {}
    st.session_state.graded_q = set()


def check_answer(user_answer, correct_answer, is_articles):
    """Verifica la risposta e calcola la penalità"""
    if user_answer.strip() == correct_answer.strip():
        return True, 0.0
    
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
    page = st.radio("Vai a:", ["🎮 Gioca", "📊 Statistiche", "ℹ️ Info"])
    
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
            else:
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
            
            # Determina se è modalità articoli
            is_articles = st.session_state.mode.startswith("Articoli")
            
            # Mostra la domanda
            if not is_articles:  # Traduzione
                question_text = word.italian
                correct_answer = word.german
                st.info(f"**Traduci in tedesco:** {question_text}")
            else:  # Articoli
                question_text = word.german
                correct_answer = word.article
                st.info(f"**Qual è l'articolo di:** {question_text}")
            
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
                            ok, penalty = check_answer(user_answer, correct_answer, is_articles)
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

# Pagina Statistiche
elif page == "📊 Statistiche":
    show_stats()

# Pagina Info
else:
    st.header("ℹ️ Informazioni")
    
    st.markdown(
        """
        ### Come Giocare
        
        1. **Scegli la categoria**: Nomi, Verbi o Aggettivi
        2. **Seleziona la modalità**:
           - **Traduzione**: Traduci dall'italiano al tedesco
           - **Articoli** (solo per nomi): Indovina l'articolo corretto (der/die/das)
        3. **Rispondi alle domande** e verifica le tue risposte (premi Invio per verificare)
        4. **👁️ Vedi risposta**: mostra la risposta corretta (Ctrl+V), conta come errore e puoi proseguire con "Prossima"
        
        ### Sistema di Punteggio
        
        - ✅ **Risposta corretta**: +1 punto
        - ❌ **Errore maiuscola** (nei nomi): -1 punto
        - ⚠️ **Errore umlaut** (ä, ö, ü, ß): -0.5 punti
        - ❌ **Errore completo**: -1 punto
        
        ### Statistiche
        
        Tutte le partite vengono salvate in un database locale. Puoi consultare:
        - Storico delle partite
        - Percentuale di successo
        - Parole più sbagliate
        
        ---
        
        **Viel Erfolg beim Deutschlernen! 🎓**
        """
    )