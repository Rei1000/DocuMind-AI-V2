-- DocuMind-AI V2 Desktop Launcher
-- Doppelklick zum Starten der Anwendung

tell application "Terminal"
    activate
    do script "cd '/Users/reiner/Documents/DocuMind-AI-V2' && ./start.sh local"
end tell

-- Zeige Notification
display notification "DocuMind-AI V2 wird gestartet..." with title "DocuMind-AI V2"

-- Öffne Browser nach kurzer Verzögerung
delay 3
tell application "Safari"
    activate
    open location "http://localhost:3000"
end tell
