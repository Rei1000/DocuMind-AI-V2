/**
 * SHAP Type Definitions
 * 
 * TypeScript-Typen für SHAP-Erklärungen und Analytics.
 * Basierend auf Backend-Schemas (contexts/ragintegration/interface/schemas.py).
 */

/**
 * SHAP Explanation Response
 * 
 * Repräsentiert eine SHAP-Erklärung für einen RAG-Such-Ergebnis.
 * Entspricht SHAPExplanationResponse aus Backend.
 */
export interface SHAPExplanationResponse {
  /** Feature-Importance-Werte (Dict[feature_name, importance]) */
  feature_importance: Record<string, number>
  
  /** Base Value (Durchschnittlicher Score) */
  base_value: number
  
  /** SHAP Values (Liste von Importance-Werten) */
  shap_values: number[]
  
  /** Expected Value (Erwarteter Score) */
  expected_value: number
  
  /** Prediction (Tatsächlicher Score) */
  prediction: number
  
  /** Die ursprüngliche Query */
  query: string
  
  /** Chunk-ID */
  chunk_id: string
  
  /** Timestamp der Erklärung (ISO-8601 String) */
  timestamp: string
  
  /** Normalisierte Feature-Werte */
  features: Record<string, number>
}

/**
 * SHAP Feature Importance Response
 * 
 * Einzelnes Feature mit Importance-Werten.
 */
export interface SHAPFeatureImportanceResponse {
  feature_name: string
  importance: number
  normalized_importance: number
  description: string
}

/**
 * SHAP Waterfall Feature
 * 
 * Feature für Waterfall-Chart.
 */
export interface SHAPWaterfallFeature {
  name: string
  value: number
  shap_value: number
}

/**
 * SHAP Waterfall Data Response
 * 
 * Daten für Waterfall-Visualisierung.
 */
export interface SHAPWaterfallDataResponse {
  base_value: number
  expected_value: number
  prediction: number
  features: SHAPWaterfallFeature[]
}

/**
 * SHAP Analytics Response
 * 
 * Umfassendes Analytics-Dashboard mit SHAP-Daten.
 */
export interface SHAPAnalyticsResponse {
  feature_importance: SHAPFeatureImportanceResponse[]
  waterfall_data: SHAPWaterfallDataResponse
  background_data_stats: {
    total_records: number
    background_data_shape: number[] | null
    last_update: string | null
    oldest_record: string | null
    newest_record: string | null
  }
  model_info: {
    model_type: string
    explainer_type: string
    n_features: number
    feature_names: string[]
  }
}

