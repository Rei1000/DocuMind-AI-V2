import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AnalyticsPage from '@/app/analytics/page'

describe('SHAP Analytics Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.setItem('access_token', 'test-token')
    localStorage.clear()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }))
  })

  it('zeigt Dashboard wenn Analytics in localStorage vorhanden sind', async () => {
    localStorage.setItem('lastAnalytics', JSON.stringify({
      query: 'Welche Risiken gibt es?',
      scores: [],
      background_data_stats: {},
      cache_stats: {},
      model_info: {}
    }))

    render(<AnalyticsPage />)

    await waitFor(() => {
      expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument()
      expect(screen.getByText(/Welche Risiken gibt es/i)).toBeInTheDocument()
    })
  })

  it('zeigt Hinweis wenn keine Analytics vorhanden sind', async () => {
    render(<AnalyticsPage />)

    await waitFor(() => {
      expect(screen.getByText(/Keine Analytics-Daten verfügbar/i)).toBeInTheDocument()
    })
  })

  it('zeigt Analytics-Seite stabil bei vorhandenen SHAP-Daten', async () => {
    localStorage.setItem('lastAnalytics', JSON.stringify({
      query: 'Warum wurde dieser Chunk bevorzugt?',
      scores: [
        {
          chunk_id: 'chunk-1',
          rank_position: 1,
          hybrid_score: 0.82,
          _extended_metadata: {
            shap_explanation: {
              feature_importance: { vector_score: 0.42, text_score: 0.33 },
              base_value: 0.1,
              prediction: 0.82,
              shap_values: [0.42, 0.33],
              feature_names: ['vector_score', 'text_score']
            }
          }
        }
      ],
      background_data_stats: {},
      cache_stats: {},
      model_info: {}
    }))

    render(<AnalyticsPage />)

    await waitFor(() => {
      expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument()
      expect(screen.getByText(/Warum wurde dieser Chunk bevorzugt/i)).toBeInTheDocument()
    })
  })

  it('zeigt Analytics-Kopfbereich und Mode-Umschalter an', async () => {
    localStorage.setItem('lastAnalytics', JSON.stringify({
      query: 'Systemstatus?',
      scores: [],
      background_data_stats: {},
      cache_stats: { hit_rate: 0.5 },
      model_info: { model_name: 'test-model' }
    }))

    render(<AnalyticsPage />)

    await waitFor(() => {
      expect(screen.getByText(/Analytics der letzten Chat-Anfrage/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Einfach erklärt/i })).toBeInTheDocument()
    })
  })
})

