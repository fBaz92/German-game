# ==================== src/database.py ====================

import sqlite3
from datetime import datetime


class DatabaseManager:
    """Gestisce il database SQLite per salvare partite ed errori"""
    
    def __init__(self, db_path='game_history.db'):
        self.db_path = db_path
        self.connection = None
        self._create_tables()
    
    def _create_tables(self):
        """Crea le tabelle se non esistono"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabella per le partite
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
        
        # Tabella per gli errori
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        success_rate = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Salva la partita
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
    
    def get_most_common_errors(self, limit=10):
        """Ottiene le parole più sbagliate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
    
    def save_error(self, game_id, word_german, word_italian, user_answer, correct_answer, penalty):
        """Salva un singolo errore (per Streamlit)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO errors (game_id, word_german, word_italian, 
                              user_answer, correct_answer, penalty)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (game_id, word_german, word_italian, user_answer, correct_answer, penalty))
        
        conn.commit()
        conn.close()