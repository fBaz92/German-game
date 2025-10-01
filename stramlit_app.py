import streamlit as st
import pandas as pd
from datetime import datetime
from src.data_loader import DataLoader
from src.game_manager import GameManager
from src.database import DatabaseManager
import random

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

def reset_game():
    """Reset dello stato del gioco"""
    st.session_state.game_started = False
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.errors = []
    st.session_state.questions = []
    st.session_state.game_type = None
    st.session_state.mode = None

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

def check_answer(user_answer, correct_answer, word_obj):
    """Verifica la risposta e calcola il punteggio"""
    penalty = 0
    
    if user_answer.strip() == correct_answer.strip():
        return True, 0
    
    # Controlla errori di maiuscola nei sostantivi
    if st.session_state.game_type == "Nomi" and st.session_state.mode == "Traduzione":
        if user_answer.strip().lower() == correct_answer.strip().lower():
            penalty = 1.0  # Errore completo per maiuscola
            return False, penalty
    
    # Controlla errori umlaut
    umlaut_map = {'ä': 'a', 'ö': 'o', 'ü': 'u', 'Ä': 'A', 'Ö': 'O', 'Ü': 'U', 'ß': 'ss'}
    user_normalized = user_answer
    correct_normalized = correct_answer
    
    for umlaut, replacement in umlaut_map.items():
        user_normalized = user_normalized.replace(umlaut, replacement)
        correct_normalized = correct_normalized.replace(umlaut, replacement)
    
    if user_normalized.strip() == correct_normalized.strip():
        penalty = 0.5  # Mezzo errore per umlaut
        return False, penalty
    
    return False, 1.0  # Errore completo

def show_stats():
    """Mostra statistiche dal database"""
    st.header("📊 Statistiche")
    
    db = DatabaseManager()
    games = db.get_all_games()
    
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
st.markdown("---")

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
        
        num_questions = st.slider("Numero di domande", 5, 30, 10)
        
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
            
            # Mostra la domanda
            if st.session_state.mode == "Traduzione":
                if st.session_state.game_type == "Nomi":
                    question_text = word.meaning
                    correct_answer = word.word
                    st.info(f"**Traduci in tedesco:** {question_text}")
                elif st.session_state.game_type == "Verbi":
                    question_text = word.meaning
                    correct_answer = word.verb
                    st.info(f"**Traduci in tedesco:** {question_text}")
                else:  # Aggettivi
                    question_text = word.meaning
                    correct_answer = word.adjective
                    st.info(f"**Traduci in tedesco:** {question_text}")
            else:  # Articoli
                question_text = word.word
                correct_answer = word.article
                st.info(f"**Qual è l'articolo di:** {question_text}")
            
            # Input risposta
            if st.session_state.mode == "Articoli (der/die/das)":
                user_answer = st.radio(
                    "Seleziona l'articolo:",
                    ["der", "die", "das"],
                    key=f"answer_{current_idx}"
                )
            else:
                user_answer = st.text_input(
                    "La tua risposta:",
                    key=f"answer_{current_idx}",
                    placeholder="Scrivi qui..."
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Verifica", type="primary", use_container_width=True):
                    if user_answer:
                        is_correct, penalty = check_answer(user_answer, correct_answer, word)
                        
                        if is_correct:
                            st.success("✅ Corretto!")
                            st.session_state.score += 1
                        else:
                            st.error(f"❌ Sbagliato! Risposta corretta: **{correct_answer}**")
                            error_type = "maiuscola" if penalty == 1.0 and st.session_state.mode == "Traduzione" else "umlaut" if penalty == 0.5 else "completo"
                            st.session_state.errors.append({
                                'word_german': correct_answer,
                                'word_italian': question_text,
                                'user_answer': user_answer,
                                'penalty': penalty,
                                'error_type': error_type
                            })
                            st.session_state.score -= penalty
                        
                        st.session_state.current_question += 1
                        st.rerun()
                    else:
                        st.warning("⚠️ Inserisci una risposta!")
            
            with col2:
                if st.button("⏩ Salta", use_container_width=True):
                    st.session_state.errors.append({
                        'word_german': correct_answer,
                        'word_italian': question_text,
                        'user_answer': '(saltata)',
                        'penalty': 1.0,
                        'error_type': 'saltata'
                    })
                    st.session_state.score -= 1
                    st.session_state.current_question += 1
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
            game_id = db.save_game(
                game_type=st.session_state.game_type,
                mode=st.session_state.mode,
                total_questions=total_questions,
                correct_answers=int(current_score),
                success_rate=success_rate
            )
            
            for error in st.session_state.errors:
                db.save_error(
                    game_id=game_id,
                    word_german=error['word_german'],
                    word_italian=error['word_italian'],
                    user_answer=error['user_answer'],
                    correct_answer=error['word_german'],
                    penalty=error['penalty']
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
    
    st.markdown("""
    ### Come Giocare
    
    1. **Scegli la categoria**: Nomi, Verbi o Aggettivi
    2. **Seleziona la modalità**:
       - **Traduzione**: Traduci dall'italiano al tedesco
       - **Articoli** (solo per nomi): Indovina l'articolo corretto (der/die/das)
    3. **Rispondi alle domande** e verifica le tue risposte
    
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
    
    ### Consigli
    
    - 💡 Fai attenzione alle maiuscole nei sostantivi tedeschi
    - 💡 Ricorda le umlaut (ä, ö, ü, ß)
    - 💡 Ripassa le parole più sbagliate nella sezione Statistiche
    
    ---
    
    **Viel Erfolg beim Deutschlernen! 🎓**
    """)