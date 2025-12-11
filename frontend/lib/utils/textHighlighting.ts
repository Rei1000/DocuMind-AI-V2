/**
 * Text-Highlighting Utilities für RAG Source References (Phase 3)
 * 
 * Hebt Query-Wörter im Text hervor, ähnlich wie die Backend-Funktion highlight_query_words.
 */

/**
 * Hebt Query-Wörter im Text hervor.
 * 
 * @param text Der Text, in dem Wörter hervorgehoben werden sollen
 * @param query Die Query (Suchanfrage)
 * @returns Text mit hervorgehobenen Query-Wörtern (als HTML-String mit <mark> Tags)
 */
export function highlightQueryWords(text: string, query?: string): string {
  // DEBUG: Logge Input-Parameter
  if (!query || !query.trim() || !text) {
    console.log('[TextHighlighting] DEBUG: Skipping - query=', query, 'text_length=', text?.length || 0)
    return text
  }
  
  // Tokenisiere Query (entferne Sonderzeichen, case-insensitive)
  // WICHTIG: Filtere Stop-Wörter heraus (Artikel, Präpositionen, etc.)
  const stopWords = new Set([
    'der', 'die', 'das', 'den', 'dem', 'des',
    'ein', 'eine', 'einen', 'einem', 'eines',
    'und', 'oder', 'aber', 'sondern',
    'in', 'auf', 'unter', 'über', 'vor', 'hinter', 'neben', 'zwischen',
    'mit', 'ohne', 'durch', 'für', 'gegen', 'um',
    'von', 'zu', 'bei', 'nach', 'seit', 'während',
    'ist', 'sind', 'war', 'waren', 'wird', 'werden',
    'haben', 'hat', 'hatte', 'hatten',
    'sein', 'seine', 'seinem', 'seinen',
    'was', 'wer', 'wie', 'wo', 'wann', 'warum', 'wohin', 'woher',
    'die', 'der', 'das', 'den', 'dem', 'des',
    'bei', 'bei der', 'bei dem'
  ])
  
  const queryWords = query
    .split(/\s+/)
    .map(word => word.trim().toLowerCase().replace(/[.,!?;:()\[\]{}'"]/g, ''))
    .filter(word => word.length > 2 && !stopWords.has(word))  // Mindestens 3 Zeichen, keine Stop-Wörter
  
  // DEBUG: Log für Troubleshooting
  if (queryWords.length === 0) {
    // Fallback: Wenn alle Wörter gefiltert wurden, verwende alle Wörter (außer sehr kurze)
    const fallbackWords = query
      .split(/\s+/)
      .map(word => word.trim().toLowerCase().replace(/[.,!?;:()\[\]{}'"]/g, ''))
      .filter(word => word.length > 2)
    console.log('[TextHighlighting] DEBUG: Alle Wörter gefiltert, verwende Fallback:', fallbackWords)
    if (fallbackWords.length > 0) {
      queryWords.push(...fallbackWords)
    }
  }
  
  if (queryWords.length === 0) {
    console.log('[TextHighlighting] DEBUG: Keine Query-Wörter nach Filterung, returning original text')
    return text
  }
  
  console.log('[TextHighlighting] DEBUG: queryWords=', queryWords, 'text_length=', text.length)
  
  // Erstelle Regex-Pattern für alle Query-Wörter (case-insensitive, Wortgrenzen)
  // Escape Sonderzeichen in Query-Wörtern
  const escapedWords = queryWords.map(word => 
    word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  )
  const pattern = new RegExp(`\\b(${escapedWords.join('|')})\\b`, 'gi')
  
  // Ersetze Query-Wörter mit Highlighting
  // WICHTIG: Escaped HTML-Zeichen im Text zuerst escapen, dann Highlighting anwenden
  const escapedText = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  
  const highlighted = escapedText.replace(
    pattern,
    '<mark class="rag-highlight">$1</mark>'
  )
  
  return highlighted
}

/**
 * Rendert hervorgehobenen Text als React-Element.
 * 
 * @param text Der Text mit HTML-Markup (z.B. mit <mark> Tags)
 * @returns React-Element mit dangerouslySetInnerHTML
 */
export function renderHighlightedText(text: string): { __html: string } {
  return { __html: text }
}

