#!/bin/bash

# DocuMind-AI V2 Desktop Launcher
# Doppelklick zum Starten der Anwendung

# Finde das Projektverzeichnis
SCRIPT_DIR="$(dirname "$0")"
PROJECT_DIR=""

# Versuche verschiedene Pfade
if [ -f "$SCRIPT_DIR/start.sh" ]; then
    PROJECT_DIR="$SCRIPT_DIR"
elif [ -f "/Users/reiner/Documents/DocuMind-AI-V2/start.sh" ]; then
    PROJECT_DIR="/Users/reiner/Documents/DocuMind-AI-V2"
else
    # Suche nach start.sh im gesamten System
    PROJECT_DIR="$(find /Users -name "start.sh" -path "*/DocuMind-AI-V2/*" 2>/dev/null | head -1 | xargs dirname)"
fi

if [ -z "$PROJECT_DIR" ] || [ ! -f "$PROJECT_DIR/start.sh" ]; then
    osascript -e 'display notification "DocuMind-AI V2 Projekt nicht gefunden!" with title "Fehler"'
    echo "❌ DocuMind-AI V2 Projekt nicht gefunden!"
    echo "Bitte kopiere die App zurück ins Projektverzeichnis oder"
    echo "stelle sicher, dass das Projekt unter /Users/reiner/Documents/DocuMind-AI-V2/ existiert."
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi

# Wechsle ins Projektverzeichnis
cd "$PROJECT_DIR"

# Zeige Notification
osascript -e 'display notification "DocuMind-AI V2 wird gestartet..." with title "DocuMind-AI V2"'

# Starte die Anwendung im local mode
./start.sh local

# Warte auf Benutzer-Input vor dem Schließen
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🎉 DocuMind-AI V2 läuft!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📊 Access Points:"
echo "   🌐 Frontend:  http://localhost:3000"
echo "   🔧 Backend:   http://localhost:8000"
echo "   📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "🛑 Zum Beenden: Drücke Ctrl+C oder schließe dieses Fenster"
echo ""
echo "Drücke Enter zum Beenden..."

# Öffne automatisch den Browser
open http://localhost:3000

# Warte auf Enter
read -p ""

# Zeige Notification beim Beenden
osascript -e 'display notification "DocuMind-AI V2 wurde beendet." with title "DocuMind-AI V2"'
