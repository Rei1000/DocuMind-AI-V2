#!/bin/bash
# Script zum Entfernen nicht-wichtiger .md Dateien aus Git-Index
# Dateien bleiben lokal erhalten, werden nur nicht mehr getrackt

echo "🧹 Entferne nicht-wichtige .md Dateien aus Git-Index..."

# Liste der zu BEHALTENDEN Dateien (wichtig für Production)
KEEP_FILES=(
  "README.md"
  "docs/PROJECT_RULES.md"
  "docs/architecture.md"
  "docs/database-schema.md"
  "docs/user-manual/README.md"
  "docs/user-manual/01-upload.md"
  "docs/user-manual/02-workflow.md"
  "docs/user-manual/03-rag-chat.md"
  "docs/user-manual/04-archive.md"
  "contexts/aiplayground/README.md"
  "contexts/documentupload/README.md"
  "contexts/ragintegration/README.md"
)

# Hole alle getrackten .md Dateien
ALL_MD_FILES=$(git ls-files | grep "\.md$")

# Entferne alle .md Dateien außer den wichtigen
REMOVED=0
for file in $ALL_MD_FILES; do
  KEEP=0
  for keep_file in "${KEEP_FILES[@]}"; do
    if [ "$file" == "$keep_file" ]; then
      KEEP=1
      break
    fi
  done
  
  if [ $KEEP -eq 0 ]; then
    echo "  ❌ Entferne: $file"
    git rm --cached "$file" 2>/dev/null
    ((REMOVED++))
  else
    echo "  ✓ Behalte: $file"
  fi
done

echo ""
echo "✅ Fertig! $REMOVED Dateien aus Git-Index entfernt (lokal erhalten)"
echo ""
echo "📋 Wichtige Dateien bleiben getrackt:"
for keep_file in "${KEEP_FILES[@]}"; do
  if git ls-files --error-unmatch "$keep_file" >/dev/null 2>&1; then
    echo "  ✓ $keep_file"
  fi
done
