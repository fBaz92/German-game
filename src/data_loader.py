

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
                        italian=row['Significato']
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
                        riflessivo=row['Riflessivo']
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
                        italian=row['Significato']
                    )
                    adjectives.append(adj)
        except FileNotFoundError:
            print(f"❌ Errore: File {filepath} non trovato!")
            return []
        except Exception as e:
            print(f"❌ Errore nel caricamento degli aggettivi: {e}")
            return []
        
        return adjectives
