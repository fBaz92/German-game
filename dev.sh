#!/bin/bash

# Script per sviluppo con Docker + hot reload
# Uso: ./dev.sh [ui|cli]

set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funzione per stampare messaggi colorati
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Controlla se Docker è in esecuzione
if ! docker info >/dev/null 2>&1; then
    print_error "Docker non è in esecuzione. Avvia Docker e riprova."
    exit 1
fi

# Determina la modalità (default: cli)
MODE=${1:-cli}

if [[ "$MODE" != "cli" && "$MODE" != "ui" ]]; then
    print_error "Modalità non valida. Usa: ./dev.sh [cli|ui]"
    print_status "  cli = modalità comando (default)"
    print_status "  ui  = modalità interfaccia web"
    exit 1
fi

print_status "Avvio sviluppo in modalità: $MODE"

# Nome del container
CONTAINER_NAME="german-game-dev"

# Pulisci container precedenti se esistono
if docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    print_status "Rimuovo container precedente..."
    docker rm -f $CONTAINER_NAME >/dev/null 2>&1 || true
fi

# Costruisci l'immagine
print_status "Costruisco l'immagine Docker..."
docker build -t german-game . >/dev/null 2>&1
print_success "Immagine costruita con successo!"

# Determina il comando da eseguire
if [[ "$MODE" == "ui" ]]; then
    print_status "Avvio in modalità UI (Streamlit)..."
    print_status "L'app sarà disponibile su: http://localhost:8501"
    docker run -it \
        --name $CONTAINER_NAME \
        -p 8501:8501 \
        -v "$PWD":/app \
        -e APP_MODE=ui \
        german-game
else
    print_status "Avvio in modalità CLI con hot reload..."
    print_status "Modifica i file e il gioco si riavvierà automaticamente!"
    print_status "Digita 'n' durante il gioco per terminare."
    docker run -it \
        --name $CONTAINER_NAME \
        -v "$PWD":/app \
        -e APP_MODE=cli \
        german-game \
        bash -lc "pip install --no-cache-dir watchfiles >/dev/null 2>&1 && watchfiles 'python main.py' /app"
fi

print_success "Container terminato."
