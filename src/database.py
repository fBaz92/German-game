# ==================== src/database.py ====================

import os
from datetime import datetime
from dotenv import load_dotenv

# Carica variabili d'ambiente da .env (se esiste)
load_dotenv()

# Determina quale database usare
DATABASE_URL = os.getenv('DATABASE_URL')

# Pulisci l'URL se contiene prefissi come 'psql'
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.strip()
    # Rimuovi 'psql' se presente all'inizio
    if DATABASE_URL.startswith('psql '):
        DATABASE_URL = DATABASE_URL[5:].strip("'\"")

if DATABASE_URL and DATABASE_URL.startswith('postgres'):
    # PostgreSQL
    import psycopg2
    from psycopg2.extras import RealDictCursor
    USE_POSTGRES = True
    print("🐘 Database: PostgreSQL")
    print(f"   Host: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'unknown'}")
else:
    # SQLite (default)
    import sqlite3
    USE_POSTGRES = False
    print("💾 Database: SQLite (locale)")


class DatabaseManager:
    """Gestisce il database (SQLite o PostgreSQL) per salvare partite ed errori"""
    
    def __init__(self):
        self.use_postgres = USE_POSTGRES
        
        if self.use_postgres:
            self.db_url = DATABASE_URL
            self._create_tables_postgres()
        else:
            self.db_path = 'game_history.db'
            self._create_tables_sqlite()
    
    # ==================== CREAZIONE TABELLE ====================
    
    def _create_tables_sqlite(self):
        """Crea le tabelle per SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                game_type TEXT NOT NULL,
                mode TEXT NOT NULL,
                total_questions INTEGER NOT NULL,
                correct_answers INTEGER NOT NULL,
                success_rate REAL NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                word_german TEXT NOT NULL,
                word_italian TEXT NOT NULL,
                user_answer TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                penalty REAL NOT NULL,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _create_tables_postgres(self):
        """Crea le tabelle per PostgreSQL"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                game_type VARCHAR(50) NOT NULL,
                mode VARCHAR(50) NOT NULL,
                total_questions INTEGER NOT NULL,
                correct_answers INTEGER NOT NULL,
                success_rate REAL NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id SERIAL PRIMARY KEY,
                game_id INTEGER NOT NULL,
                word_german VARCHAR(200) NOT NULL,
                word_italian VARCHAR(200) NOT NULL,
                user_answer VARCHAR(200) NOT NULL,
                correct_answer VARCHAR(200) NOT NULL,
                penalty REAL NOT NULL,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ==================== CONNESSIONE ====================
    
    def _get_connection(self):
        """Restituisce una connessione al database"""
        if self.use_postgres:
            return psycopg2.connect(self.db_url)
        else:
            return sqlite3.connect(self.db_path)
    
    # ==================== SALVATAGGIO ====================
    
    def save_game(self, game_type, mode, total_questions, correct_answers, errors):
        """
        Salva una partita nel database
        
        Args:
            game_type: str ('Nomi', 'Verbi', 'Aggettivi')
            mode: str ('Traduzione', 'Articoli', 'Coniugazioni')
            total_questions: int
            correct_answers: int
            errors: list di dict con chiavi:
                - word_german
                - word_italian
                - user_answer
                - correct_answer
                - penalty
        
        Returns:
            game_id: int (ID della partita salvata)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        success_rate = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        if self.use_postgres:
            # PostgreSQL usa TIMESTAMP e RETURNING
            cursor.execute("""
                INSERT INTO games (timestamp, game_type, mode, total_questions, 
                                 correct_answers, success_rate)
                VALUES (NOW(), %s, %s, %s, %s, %s)
                RETURNING id
            """, (game_type, mode, total_questions, correct_answers, success_rate))
            
            game_id = cursor.fetchone()[0]
            
            # Salva gli errori
            for error in errors:
                cursor.execute("""
                    INSERT INTO errors (game_id, word_german, word_italian, 
                                      user_answer, correct_answer, penalty)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (game_id, error['word_german'], error['word_italian'],
                      error['user_answer'], error['correct_answer'], error['penalty']))
        
        else:
            # SQLite
            timestamp = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO games (timestamp, game_type, mode, total_questions, 
                                 correct_answers, success_rate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, game_type, mode, total_questions, correct_answers, success_rate))
            
            game_id = cursor.lastrowid
            
            # Salva gli errori
            for error in errors:
                cursor.execute("""
                    INSERT INTO errors (game_id, word_german, word_italian, 
                                      user_answer, correct_answer, penalty)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (game_id, error['word_german'], error['word_italian'],
                      error['user_answer'], error['correct_answer'], error['penalty']))
        
        conn.commit()
        conn.close()
        
        return game_id
    
    # ==================== QUERY ====================
    
    def get_most_common_errors(self, limit=10):
        """Ottiene le parole più sbagliate"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.use_postgres:
            cursor.execute("""
                SELECT word_german, word_italian, COUNT(*) as error_count
                FROM errors
                GROUP BY word_german, word_italian
                ORDER BY error_count DESC
                LIMIT %s
            """, (limit,))
        else:
            cursor.execute("""
                SELECT word_german, word_italian, COUNT(*) as error_count
                FROM errors
                GROUP BY word_german, word_italian
                ORDER BY error_count DESC
                LIMIT ?
            """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_game_history(self, limit=10):
        """Ottiene lo storico delle ultime partite"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.use_postgres:
            cursor.execute("""
                SELECT id, timestamp, game_type, mode, total_questions, 
                       correct_answers, success_rate
                FROM games
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
        else:
            cursor.execute("""
                SELECT id, timestamp, game_type, mode, total_questions, 
                       correct_answers, success_rate
                FROM games
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_most_common_errors_by_type(self, game_type, min_errors=2):
        """
        Ottiene le parole più sbagliate per una specifica categoria
        
        Args:
            game_type: 'Nomi', 'Verbi', o 'Aggettivi'
            min_errors: numero minimo di errori
        
        Returns:
            list di tuple (word_german, word_italian, error_count)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.use_postgres:
            cursor.execute("""
                SELECT e.word_german, e.word_italian, COUNT(*) as error_count
                FROM errors e
                JOIN games g ON e.game_id = g.id
                WHERE g.game_type LIKE %s
                GROUP BY e.word_german, e.word_italian
                HAVING COUNT(*) >= %s
                ORDER BY error_count DESC
            """, (f"%{game_type}%", min_errors))
        else:
            cursor.execute("""
                SELECT e.word_german, e.word_italian, COUNT(*) as error_count
                FROM errors e
                JOIN games g ON e.game_id = g.id
                WHERE g.game_type LIKE ?
                GROUP BY e.word_german, e.word_italian
                HAVING error_count >= ?
                ORDER BY error_count DESC
            """, (f"%{game_type}%", min_errors))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_stats_by_type(self, game_type):
        """Ottiene statistiche per un tipo di gioco"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if self.use_postgres:
            cursor.execute("""
                SELECT 
                    COUNT(*) as games,
                    AVG(success_rate) as avg_success,
                    SUM(total_questions) as total_questions
                FROM games
                WHERE game_type LIKE %s
            """, (f"%{game_type}%",))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(*) as games,
                    AVG(success_rate) as avg_success,
                    SUM(total_questions) as total_questions
                FROM games
                WHERE game_type LIKE ?
            """, (f"%{game_type}%",))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] > 0:
            return {
                'games': result[0],
                'avg_success': result[1],
                'total_questions': result[2]
            }
        return None
    
    def get_all_games(self):
        """Ottiene tutte le partite (per Streamlit)"""
        return self.get_game_history(limit=10000)