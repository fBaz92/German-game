# ==================== main.py ====================

from src.game_manager import GameManager


def main():
    """Funzione principale"""
    try:
        game = GameManager()
        game.start()
    except KeyboardInterrupt:
        print("\\n\\n👋 Gioco interrotto. Auf Wiedersehen!")
    except Exception as e:
        print(f"\\n❌ Errore imprevisto: {e}")


if __name__ == "__main__":
    main()
