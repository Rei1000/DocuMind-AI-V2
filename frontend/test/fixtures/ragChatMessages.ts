/**
 * Test Fixtures für RAG Chat Messages
 * Basierend auf realen Daten aus Dokument 273 (Arbeitsanweisung Freilaufwelle)
 */

export const mockUserMessage = {
  id: 1,
  role: 'user' as const,
  content: 'Was ist die Artikelnummer der Freilaufwelle?',
  created_at: '2024-01-01T12:00:00Z',
  source_references: []
}

export const mockAssistantMessage = {
  id: 2,
  role: 'assistant' as const,
  content: 'Die Artikelnummer der Freilaufwelle lautet 26-10-204.',
  created_at: '2024-01-01T12:05:00Z',
  source_references: [{
    document_id: 273,
    document_title: 'Arbeitsanweisung Freilaufwelle Montage',
    page_number: 2,
    chunk_id: 5,
    relevance_score: 0.95,
    text_excerpt: 'Freilaufwelle 26-10-204 mit Lagern vormontieren und auf korrekte Funktion prüfen...'
  }]
}

export const mockStructuredDataMessage = {
  id: 3,
  role: 'assistant' as const,
  content: 'Hier sind die benötigten Artikel:',
  created_at: '2024-01-01T12:10:00Z',
  source_references: [],
  structured_data: [{
    data_type: 'article_data',
    content: {
      articles: [
        { name: 'Freilaufwelle', art_nr: '26-10-204', qty_number: 1, qty_unit: 'Stk' },
        { name: 'Lager', art_nr: '987.654.321', qty_number: 2, qty_unit: 'Stk' }
      ]
    },
    confidence: 0.92
  }]
}

export const mockSafetyDataMessage = {
  id: 4,
  role: 'assistant' as const,
  content: 'Wichtige Sicherheitshinweise:',
  created_at: '2024-01-01T12:12:00Z',
  source_references: [],
  structured_data: [{
    data_type: 'safety_instructions',
    content: {
      warnings: [
        'Vor Montage Strom abschalten',
        'Handschuhe tragen',
        'Werkzeug auf Beschädigungen prüfen'
      ]
    },
    confidence: 0.88
  }]
}

export const mockMultiSourceMessage = {
  id: 5,
  role: 'assistant' as const,
  content: 'Die Montage erfordert mehrere Schritte...',
  created_at: '2024-01-01T12:15:00Z',
  source_references: [
    {
      document_id: 273,
      document_title: 'Arbeitsanweisung Freilaufwelle',
      page_number: 2,
      chunk_id: 5,
      relevance_score: 0.95,
      text_excerpt: 'Schritt 2: Vormontage Freilaufwelle'
    },
    {
      document_id: 273,
      document_title: 'Arbeitsanweisung Freilaufwelle',
      page_number: 3,
      chunk_id: 8,
      relevance_score: 0.88,
      text_excerpt: 'Schritt 3: Freilaufwelle montieren'
    }
  ]
}

export const mockErrorMessage = {
  id: 6,
  role: 'user' as const,
  content: 'Test Fehler-Nachricht',
  created_at: '2024-01-01T12:20:00Z',
  source_references: [],
  failed: true
}

export const mockConversation = [
  mockUserMessage,
  mockAssistantMessage,
  {
    id: 7,
    role: 'user' as const,
    content: 'Welche Werkzeuge werden benötigt?',
    created_at: '2024-01-01T12:25:00Z',
    source_references: []
  },
  {
    id: 8,
    role: 'assistant' as const,
    content: 'Für die Montage werden folgende Werkzeuge benötigt: Drehmomentschlüssel, Schraubendreher, Prüflehre.',
    created_at: '2024-01-01T12:26:00Z',
    source_references: [{
      document_id: 273,
      document_title: 'Arbeitsanweisung Freilaufwelle',
      page_number: 1,
      chunk_id: 2,
      relevance_score: 0.92,
      text_excerpt: 'Benötigte Werkzeuge: Drehmomentschlüssel 10-50 Nm, Schraubendreher Set, Prüflehre...'
    }]
  }
]

