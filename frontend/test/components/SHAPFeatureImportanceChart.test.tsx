/**
 * Unit Tests für SHAP Feature Importance Chart.
 * 
 * TDD Phase 3: RED - Tests schreiben bevor Code existiert.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import SHAPFeatureImportanceChart from '@/components/SHAPFeatureImportanceChart'

describe('SHAPFeatureImportanceChart', () => {
  it('renders feature importance chart', () => {
    const explanation = {
      feature_importance: {
        vector_score: 0.4,
        text_score: 0.3,
        keyword_matches: 0.2
      },
      base_value: 0.5,
      prediction: 0.81,
      query: 'Test Query',
      chunk_id: 'test_chunk_1',
      timestamp: new Date().toISOString(),
      features: {}
    }
    
    render(<SHAPFeatureImportanceChart explanation={explanation} />)
    
    expect(screen.getByText('SHAP Feature Importance')).toBeInTheDocument()
  })
  
  it('displays all features in chart', () => {
    const explanation = {
      feature_importance: {
        vector_score: 0.4,
        text_score: 0.3,
        keyword_matches: 0.2,
        user_level: 0.05,
        chunk_length: 0.03
      },
      base_value: 0.5,
      prediction: 0.81,
      query: 'Test Query',
      chunk_id: 'test_chunk_1',
      timestamp: new Date().toISOString(),
      features: {}
    }
    
    render(<SHAPFeatureImportanceChart explanation={explanation} />)
    
    // Alle Features sollten angezeigt werden
    expect(screen.getByText('vector_score')).toBeInTheDocument()
    expect(screen.getByText('text_score')).toBeInTheDocument()
    expect(screen.getByText('keyword_matches')).toBeInTheDocument()
  })
  
  it('sorts features by importance', () => {
    const explanation = {
      feature_importance: {
        vector_score: 0.4,  // Höchste Importance
        text_score: 0.3,
        keyword_matches: 0.2  // Niedrigste Importance
      },
      base_value: 0.5,
      prediction: 0.81,
      query: 'Test Query',
      chunk_id: 'test_chunk_1',
      timestamp: new Date().toISOString(),
      features: {}
    }
    
    render(<SHAPFeatureImportanceChart explanation={explanation} />)
    
    // Features sollten nach Importance sortiert sein (höchste zuerst)
    const featureElements = screen.getAllByText(/vector_score|text_score|keyword_matches/)
    // vector_score sollte zuerst kommen (höchste Importance)
    expect(featureElements[0]).toHaveTextContent('vector_score')
  })
  
  it('displays feature importance values as percentages', () => {
    const explanation = {
      feature_importance: {
        vector_score: 0.4  // Sollte als 40% angezeigt werden
      },
      base_value: 0.5,
      prediction: 0.81,
      query: 'Test Query',
      chunk_id: 'test_chunk_1',
      timestamp: new Date().toISOString(),
      features: {}
    }
    
    render(<SHAPFeatureImportanceChart explanation={explanation} />)
    
    // Importance wird auf eine Nachkommastelle formatiert
    expect(screen.getByText('40.0%')).toBeInTheDocument()
  })
  
  it('handles empty feature importance gracefully', () => {
    const explanation = {
      feature_importance: {},
      base_value: 0.5,
      prediction: 0.81,
      query: 'Test Query',
      chunk_id: 'test_chunk_1',
      timestamp: new Date().toISOString(),
      features: {}
    }
    
    render(<SHAPFeatureImportanceChart explanation={explanation} />)
    
    // Sollte eine Meldung anzeigen, dass keine Features vorhanden sind
    expect(screen.getByText(/keine Features|no features/i)).toBeInTheDocument()
  })
})

