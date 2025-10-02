

import csv
import os
from src.word import Noun, Verb, Adjective


class DataLoader:
    """Carica i dati dai file CSV"""
    
    def __init__(self, assets_dir='assets'):
        self.assets_dir = assets_dir
    
    def load_nouns(self):
        """Carica i sostantivi da nomi.csv"""
        filepath = os.path.join(self.assets_dir, 'nomi.csv')
        nouns = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    noun = Noun(
                        german=row['Sostantivo'],
                        article=row['Articolo'],
                        plural=row['Plurale'],
                        italian=row['Significato'],
                        frequency=row['Frequenza']
                    )
                    nouns.append(noun)
        except FileNotFoundError:
            print(f"❌ Errore: File {filepath} non trovato!")
            return []
        except Exception as e:
            print(f"❌ Errore nel caricamento dei sostantivi: {e}")
            return []
        
        return nouns
    
    def load_verbs(self):
        """Carica i verbi da verbi.csv"""
        filepath = os.path.join(self.assets_dir, 'verbi.csv')
        verbs = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    verb = Verb(
                        german=row['Verbo'],
                        regular=row['Regolare'],
                        italian=row['Significato'],
                        prateritum=row['Präteritum'],
                        participio=row['Participio passato'],
                        perfetto=row['Perfetto'],
                        caso=row['Caso'],
                        riflessivo=row['Riflessivo'],
                        frequency=row['Frequenza']
                    )
                    verbs.append(verb)
        except FileNotFoundError:
            print(f"❌ Errore: File {filepath} non trovato!")
            return []
        except Exception as e:
            print(f"❌ Errore nel caricamento dei verbi: {e}")
            return []
        
        return verbs
    
    def load_adjectives(self):
        """Carica gli aggettivi da aggettivi.csv"""
        filepath = os.path.join(self.assets_dir, 'aggettivi.csv')
        adjectives = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    adj = Adjective(
                        german=row['Aggettivo'],
                        comparative=row['Comparativo'],
                        superlative=row['Superlativo'],
                        italian=row['Significato'],
                        frequency=row['Frequenza']
                    )
                    adjectives.append(adj)
        except FileNotFoundError:
            print(f"❌ Errore: File {filepath} non trovato!")
            return []
        except Exception as e:
            print(f"❌ Errore nel caricamento degli aggettivi: {e}")
            return []
        
        return adjectives
    
    def get_words_by_difficulty(self, words, difficulty_mode, difficulty_level=None):
        """
        Filtra le parole in base alla modalità di difficoltà
        
        Args:
            words: lista di parole (Noun/Verb/Adjective)
            difficulty_mode: 'casual', 'fixed', 'focus'
            difficulty_level: livello di difficoltà (1-5) per modalità 'fixed' e 'focus'
        
        Returns:
            lista di parole filtrate
        """
        if difficulty_mode == 'casual':
            return words
        
        elif difficulty_mode == 'fixed':
            if difficulty_level is None:
                return words
            # Tutte le parole con frequenza <= al livello selezionato
            return [word for word in words if word.frequency <= difficulty_level]
        
        elif difficulty_mode == 'focus':
            if difficulty_level is None:
                return words
            # Solo parole con frequenza = al livello selezionato
            return [word for word in words if word.frequency == difficulty_level]
        
        return words
    
    def get_difficulty_stats(self, words):
        """
        Restituisce statistiche sulla distribuzione delle difficoltà
        
        Returns:
            dict con conteggi per ogni livello di difficoltà
        """
        stats = {}
        for word in words:
            freq = word.frequency
            stats[freq] = stats.get(freq, 0) + 1
        return stats
