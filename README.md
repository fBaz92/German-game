# German Learning Game 🇩🇪

Un gioco interattivo da linea di comando per imparare il tedesco attraverso la pratica di sostantivi, verbi e aggettivi.

## 📁 Struttura del Progetto

```
german-game/
├── main.py                 # Entry point del gioco (CLI)
├── streamlit_app.py        # Interfaccia grafica Streamlit per giocare
├── README.md               # Questo file
├── game_history.db         # Database SQLite (generato automaticamente)
├── assets/                 # Cartella con i dati CSV
│   ├── nomi.csv           # Sostantivi tedeschi
│   ├── verbi.csv          # Verbi tedeschi
│   └── aggettivi.csv      # Aggettivi tedeschi
└── src/                    # Codice sorgente
    ├── __init__.py
    ├── word.py            # Classi Word, Noun, Verb, Adjective
    ├── data_loader.py     # Caricamento dati dai CSV
    ├── database.py        # Gestione database errori
    └── game_manager.py    # Logica principale del gioco
```

## 🎮 Come Giocare

### Installazione

1. Assicurati di avere Python 3.7+ installato
2. Crea e attiva un ambiente virtuale (consigliato):

   macOS/Linux:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   Windows (PowerShell):
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. Clona o scarica il progetto
4. Crea i file CSV nella cartella `assets/` (vedi formato sotto)
5. (Opzionale, per interfaccia grafica) Installa Streamlit all'interno del venv attivo:

```bash
pip install streamlit
```

### Avvio del Gioco (CLI)

```bash
python main.py
```

### Avvio dell'Interfaccia Grafica (Streamlit)

```bash
streamlit run streamlit_app.py
```

- Dalla UI potrai scegliere la categoria (Nomi/Verbi/Aggettivi) e la modalità (Traduzione e, per i sostantivi, Articoli).
- I dati vengono letti dagli stessi CSV in `assets/`.
- Il salvataggio nel database `game_history.db` avviene come nella versione CLI.

## Modalità di Gioco

Il gioco offre tre categorie:

1. **Nomi (Sostantivi)**
   - Modalità Traduzione: traduci dall'italiano al tedesco
   - Modalità Articoli: indovina l'articolo (der/die/das)

2. **Verbi**
   - Modalità Traduzione: traduci dall'italiano al tedesco

3. **Aggettivi**
   - Modalità Traduzione: traduci dall'italiano al tedesco

## 📊 Formato dei File CSV

### nomi.csv
```csv
Sostantivo,Articolo,Plurale,Significato
Wasser,das,Wasser,acqua
Haus,das,Häuser,casa
Frau,die,Frauen,donna
```

### aggettivi.csv
```csv
Aggettivo,Comparativo,Superlativo,Significato
schön,schöner,am schönsten,bello
groß,größer,am größten,grande
gut,besser,am besten,buono
```

### verbi.csv
```csv
Verbo,Regolare,Significato,Präteritum,Participio passato,Perfetto,Caso,Riflessivo
sein,no,essere,war,gewesen,ist,nominativo,no
haben,no,avere,hatte,gehabt,hat,accusativo,no
gehen,si,andare,ging,gegangen,ist,nominativo,no
```

## 📈 Sistema di Valutazione

- **Risposta corretta**: 1 punto
- **Errore maiuscola** (es. "wasser" invece di "Wasser"): errore completo (-1 punto)
- **Errore umlaut** (es. "Waser" invece di "Wasser"): mezzo errore (-0.5 punti)
- **Altri errori**: errore completo (-1 punto)

Alla fine di ogni partita viene mostrata la **percentuale di successo**.

## 💾 Database

Il gioco salva automaticamente:
- Storico di tutte le partite
- Elenco dettagliato degli errori per ogni partita
- Statistiche su parole più sbagliate

Il database è un file SQLite (`game_history.db`) che viene creato automaticamente alla prima esecuzione.

### Struttura del Database

**Tabella `games`**
- `id`: ID univoco della partita
- `timestamp`: Data e ora della partita
- `game_type`: Tipo di gioco (Nomi/Verbi/Aggettivi)
- `mode`: Modalità (Traduzione/Articoli)
- `total_questions`: Numero totale di domande
- `correct_answers`: Numero di risposte corrette
- `success_rate`: Percentuale di successo

**Tabella `errors`**
- `id`: ID univoco dell'errore
- `game_id`: Riferimento alla partita
- `word_german`: Parola in tedesco
- `word_italian`: Traduzione italiana
- `user_answer`: Risposta dell'utente
- `correct_answer`: Risposta corretta
- `penalty`: Penalità applicata (0.5 o 1.0)

## 🎯 Funzionalità

- ✅ Gioco interattivo da linea di comando
- ✅ Interfaccia grafica Streamlit per giocare da browser
- ✅ Tre categorie di parole (nomi, verbi, aggettivi)
- ✅ Modalità speciale "der/die/das" per i sostantivi
- ✅ Sistema di valutazione con penalità per maiuscole e umlaut
- ✅ Salvataggio automatico degli errori in database
- ✅ Statistiche dettagliate a fine partita
- ✅ Possibilità di interrompere la partita in qualsiasi momento

## 🚀 Esempio di Utilizzo (CLI)

```
=================================================
🇩🇪  BENVENUTO AL GIOCO DI TEDESCO  🇩🇪
=================================================

Cosa vuoi studiare?
1. Nomi (Sostantivi)
2. Verbi
3. Aggettivi

Scelta (1/2/3): 1

✅ Caricati 50 sostantivi

Scegli modalità:
1. Traduzione (Italiano → Tedesco)
2. Articoli (der/die/das)

Modalità (1/2): 2

==================================================
🎮 MODALITÀ: ARTICOLI (DER/DIE/DAS)
==================================================

📝 Domanda 1:
Articolo di 'Wasser'? (der/die/das)
➤ La tua risposta (der/die/das): das
✅ CORRETTO!

Continuare? (s/n): s

📝 Domanda 2:
Articolo di 'Haus'? (der/die/das)
➤ La tua risposta (der/die/das): der
❌ SBAGLIATO! Risposta corretta: das

Continuare? (s/n): n

==================================================
📊 RISULTATI FINALI
==================================================

✅ Risposte corrette: 1/2
❌ Errori totali: 1
📈 Percentuale di successo: 50.0%

──────────────────────────────────────────────────
Errori commessi:
──────────────────────────────────────────────────
1. casa → Haus
   Hai risposto: der (errore completo)

💾 Partita salvata nel database!
==================================================
```

## 🛠️ Estensioni Future

Possibili miglioramenti:
- Modalità di ripasso degli errori più frequenti
- Esportazione statistiche in formato CSV/PDF
- Modalità "sfida a tempo"
- Quiz su coniugazioni verbali (Präteritum, Partizip)
- Interfaccia grafica (GUI)

## 📝 Note Tecniche

- **Encoding**: Tutti i file CSV devono essere salvati in UTF-8 per supportare i caratteri speciali tedeschi (ä, ö, ü, ß)
- **Database**: Utilizza SQLite3, incluso nella libreria standard di Python
- **Compatibilità**: Python 3.7+

## 📄 Licenza

Progetto educativo per uso personale.

---

**Viel Erfolg beim Deutschlernen! 🎓**