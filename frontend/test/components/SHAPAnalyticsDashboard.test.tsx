/**
 * Unit Tests für SHAP Analytics Dashboard Erweiterung.
 * 
 * TDD Phase 3: RED - Tests schreiben bevor Code existiert.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AnalyticsPage from '@/app/analytics/page'

// Mock API
vi.mock('@/lib/api/rag', () => ({
  getRAGAnalytics: vi.fn()
}))

describe('SHAP Analytics Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })
  
  it('displays SHAP statistics section', async () => {
    const { getRAGAnalytics } = await import('@/lib/api/rag')
    vi.mocked(getRAGAnalytics).mockResolvedValue({
      feedback: {
        total: 0,
        positive: 0,
        negative: 0,
        neutral: 0,
        average_rating: 0
      },
      queries: {
        total: 0,
        average_score: 0,
        top_queries: []
      },
      chunking: {
        total_chunks: 0,
        average_chunk_length: 0
      },
      indexing: {
        total_indexed: 0,
        average_indexing_time: 0
      },
      messages: {
        total: 0,
        average_tokens: 0
      },
      quality: {
        average_score: 0,
        score_distribution: {}
      },
      shap: {  // NEU: SHAP-Statistiken
        total_explanations: 0,
        average_feature_count: 0,
        top_features: []
      }
    })
    
    render(<AnalyticsPage />)
    
    await waitFor(() => {
      expect(screen.getByText(/SHAP/i)).toBeInTheDocument()
    })
  })
  
  it('displays SHAP feature importance summary', async () => {
    const { getRAGAnalytics } = await import('@/lib/api/rag')
    vi.mocked(getRAGAnalytics).mockResolvedValue({
      feedback: { total: 0, positive: 0, negative: 0, neutral: 0, average_rating: 0 },
      queries: { total: 0, average_score: 0, top_queries: [] },
      chunking: { total_chunks: 0, average_chunk_length: 0 },
      indexing: { total_indexed: 0, average_indexing_time: 0 },
      messages: { total: 0, average_tokens: 0 },
      quality: { average_score: 0, score_distribution: {} },
      shap: {
        total_explanations: 10,
        average_feature_count: 7,
        top_features: [
          { feature: 'vector_score', average_importance: 0.4 },
          { feature: 'text_score', average_importance: 0.3 }
        ]
      }
    })
    
    render(<AnalyticsPage />)
    
    await waitFor(() => {
      expect(screen.getByText(/vector_score/i)).toBeInTheDocument()
      expect(screen.getByText(/text_score/i)).toBeInTheDocument()
    })
  })
  
  it('displays ML model performance metrics', async () => {
    const { getRAGAnalytics } = await import('@/lib/api/rag')
    vi.mocked(getRAGAnalytics).mockResolvedValue({
      feedback: { total: 0, positive: 0, negative: 0, neutral: 0, average_rating: 0 },
      queries: { total: 0, average_score: 0, top_queries: [] },
      chunking: { total_chunks: 0, average_chunk_length: 0 },
      indexing: { total_indexed: 0, average_indexing_time: 0 },
      messages: { total: 0, average_tokens: 0 },
      quality: { average_score: 0, score_distribution: {} },
      ml_performance: {  // NEU: ML-Performance-Metriken
        model_accuracy: 0.85,
        precision: 0.82,
        recall: 0.88,
        f1_score: 0.85,
        training_samples: 100
      }
    })
    
    render(<AnalyticsPage />)
    
    await waitFor(() => {
      expect(screen.getByText(/Model Accuracy|Accuracy/i)).toBeInTheDocument()
      expect(screen.getByText(/85%|0\.85/)).toBeInTheDocument()
    })
  })
  
  it('displays optimization history timeline', async () => {
    const { getRAGAnalytics } = await import('@/lib/api/rag')
    vi.mocked(getRAGAnalytics).mockResolvedValue({
      feedback: { total: 0, positive: 0, negative: 0, neutral: 0, average_rating: 0 },
      queries: { total: 0, average_score: 0, top_queries: [] },
      chunking: { total_chunks: 0, average_chunk_length: 0 },
      indexing: { total_indexed: 0, average_indexing_time: 0 },
      messages: { total: 0, average_tokens: 0 },
      quality: { average_score: 0, score_distribution: {} },
      optimization_history: [  // NEU: Optimization History
        {
          date: '2025-11-13',
          action: 'Hybrid Score Weighting Adjusted',
          before_score: 0.75,
          after_score: 0.82,
          improvement: 0.07
        }
      ]
    })
    
    render(<AnalyticsPage />)
    
    await waitFor(() => {
      expect(screen.getByText(/Optimization History|Optimierungs-Historie/i)).toBeInTheDocument()
      expect(screen.getByText(/Hybrid Score/i)).toBeInTheDocument()
    })
  })
})

