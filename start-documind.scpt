-- DocuMind-AI V2 Desktop Launcher
-- Doppelklick zum Starten der Anwendung

set modeChoice to choose from list {"Docker", "Lokal"} with prompt "DocuMind-AI V2 starten mit:" default items {"Docker"}
if modeChoice is false then
    return
end if

set chosenMode to item 1 of modeChoice
if chosenMode is "Lokal" then
    set startMode to "local"
else
    set startMode to "docker"
end if

tell application "Terminal"
    activate
    do script "cd '/Users/reiner/Documents/DocuMind-AI-V2' && ./start.sh " & startMode
end tell

-- Zeige Notification
display notification "DocuMind-AI V2 wird gestartet (" & chosenMode & ")..." with title "DocuMind-AI V2"

-- Öffne Browser nach kurzer Verzögerung
delay 3
tell application "Safari"
    activate
    open location "http://localhost:3000"
end tell
