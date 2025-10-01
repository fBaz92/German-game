# ==================== src/statistics.py ====================

from .database import DatabaseManager
from datetime import datetime, timedelta
from collections import defaultdict


class StatisticsManager:
    """Gestisce statistiche avanzate sull'apprendimento"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def show_dashboard(self):
        """Mostra una dashboard completa delle statistiche"""
        print("\n" + "="*60)
        print("📊 DASHBOARD STATISTICHE DETTAGLIATE")
        print("="*60)
        
        # Statistiche generali
        self._show_general_stats()
        
        # Progressi nel tempo
        self._show_progress_over_time()
        
        # Analisi per categoria
        self._show_category_breakdown()
        
        # Parole più difficili
        self._show_difficult_words()
        
        # Streak e record
        self._show_streaks()
        
        print("="*60)
    
    def _show_general_stats(self):
        """Statistiche generali"""
        print("\n🎯 STATISTICHE GENERALI")
        print("─"*60)
        
        games = self.db.get_game_history(limit=1000)
        
        if not games:
            print("   Nessuna partita giocata ancora.")
            return
        
        total_games = len(games)
        total_questions = sum(game[4] for game in games)
        total_correct = sum(game[5] for game in games)
        avg_success = sum(game[6] for game in games) / total_games
        
        print(f"   📈 Partite giocate: {total_games}")
        print(f"   ❓ Domande totali: {total_questions}")
        print(f"   ✅ Risposte corrette: {total_correct}")
        print(f"   📊 Media successo: {avg_success:.1f}%")
        
        # Trova la migliore partita
        best_game = max(games, key=lambda x: x[6])
        print(f"\n   🏆 Miglior partita: {best_game[6]:.1f}% ({best_game[2]} - {best_game[3]})")
    
    def _show_progress_over_time(self):
        """Mostra il progresso nel tempo"""
        print("\n📈 PROGRESSO NEL TEMPO")
        print("─"*60)
        
        games = self.db.get_game_history(limit=1000)
        
        if not games:
            return
        
        # Raggruppa per settimana
        weekly_stats = defaultdict(lambda: {'games': 0, 'total_success': 0})
        
        for game in games:
            # Parse timestamp
            timestamp = datetime.fromisoformat(game[1])
            week_start = timestamp - timedelta(days=timestamp.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            
            weekly_stats[week_key]['games'] += 1
            weekly_stats[week_key]['total_success'] += game[6]
        
        # Mostra ultime 4 settimane
        sorted_weeks = sorted(weekly_stats.items(), reverse=True)[:4]
        
        print("   Ultime 4 settimane:")
        for week, stats in sorted_weeks:
            avg = stats['total_success'] / stats['games']
            print(f"   • Settimana del {week}: {stats['games']} partite, media {avg:.1f}%")
    
    def _show_category_breakdown(self):
        """Analisi per categoria"""
        print("\n📚 ANALISI PER CATEGORIA")
        print("─"*60)
        
        for game_type in ['Nomi', 'Verbi', 'Aggettivi']:
            stats = self.db.get_stats_by_type(game_type)
            
            if stats:
                print(f"\n   {game_type}:")
                print(f"      • Partite: {stats['games']}")
                print(f"      • Media successo: {stats['avg_success']:.1f}%")
                print(f"      • Parole studiate: {stats['total_questions']}")
    
    def _show_difficult_words(self):
        """Mostra le parole più difficili"""
        print("\n❌ PAROLE PIÙ DIFFICILI")
        print("─"*60)
        
        errors = self.db.get_most_common_errors(limit=10)
        
        if errors:
            print("   Top 10 parole più sbagliate:")
            for i, (german, italian, count) in enumerate(errors, 1):
                print(f"   {i:2d}. {german:20s} ({italian}) - {count} errori")
        else:
            print("   Nessun errore registrato!")
    
    def _show_streaks(self):
        """Mostra streak e record"""
        print("\n🔥 STREAK E RECORD")
        print("─"*60)
        
        games = self.db.get_game_history(limit=1000)
        
        if not games:
            return
        
        # Calcola streak corrente (giorni consecutivi di gioco)
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
        
        print(f"   🔥 Streak corrente: {current_streak} giorni")
        print(f"   🏅 Miglior streak: {longest_streak} giorni")
        
        # Partite questa settimana
        week_ago = datetime.now() - timedelta(days=7)
        recent_games = [g for g in games if datetime.fromisoformat(g[1]) > week_ago]
        print(f"   📅 Partite questa settimana: {len(recent_games)}")
    
    def export_statistics(self, filename='stats_export.txt'):
        """Esporta statistiche in un file di testo"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("STATISTICHE APPRENDIMENTO TEDESCO\n")
            f.write(f"Generato il: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write("="*60 + "\n\n")
            
            # Statistiche generali
            games = self.db.get_game_history(limit=1000)
            
            if games:
                total_games = len(games)
                total_questions = sum(game[4] for game in games)
                total_correct = sum(game[5] for game in games)
                avg_success = sum(game[6] for game in games) / total_games
                
                f.write("STATISTICHE GENERALI\n")
                f.write(f"Partite giocate: {total_games}\n")
                f.write(f"Domande totali: {total_questions}\n")
                f.write(f"Risposte corrette: {total_correct}\n")
                f.write(f"Media successo: {avg_success:.1f}%\n\n")
                
                # Parole più difficili
                f.write("PAROLE PIÙ DIFFICILI\n")
                errors = self.db.get_most_common_errors(limit=20)
                for i, (german, italian, count) in enumerate(errors, 1):
                    f.write(f"{i}. {german} ({italian}) - {count} errori\n")
        
        print(f"\n✅ Statistiche esportate in '{filename}'")