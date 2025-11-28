/**
 * RAG Chat Settings Modal
 * 
 * Ermöglicht es Usern, AI-Modell-Einstellungen zu konfigurieren:
 * - Temperature (0.0 - 2.0)
 * - Max Tokens (1 - 8000)
 * - Top P (0.0 - 1.0)
 * 
 * Version: 2.10.3
 */

'use client'

import { X, Info, RotateCcw } from 'lucide-react'
import { useState, useEffect } from 'react'

interface RAGChatSettingsModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (settings: AISettings) => void
  currentSettings: AISettings
}

export interface AISettings {
  temperature: number
  max_tokens: number
  top_p: number
}

const DEFAULT_SETTINGS: AISettings = {
  temperature: 0.0,  // NEU v2.10.3: Default auf 0 für konsistente Antworten
  max_tokens: 4000,
  top_p: 0.9
}

export default function RAGChatSettingsModal({
  isOpen,
  onClose,
  onSave,
  currentSettings
}: RAGChatSettingsModalProps) {
  const [settings, setSettings] = useState<AISettings>(currentSettings)
  const [errors, setErrors] = useState<Partial<Record<keyof AISettings, string>>>({})

  // Update settings when currentSettings changes
  useEffect(() => {
    setSettings(currentSettings)
  }, [currentSettings])

  if (!isOpen) return null

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof AISettings, string>> = {}

    if (settings.temperature < 0 || settings.temperature > 2) {
      newErrors.temperature = 'Temperature muss zwischen 0.0 und 2.0 liegen'
    }

    if (settings.max_tokens < 1 || settings.max_tokens > 8000) {
      newErrors.max_tokens = 'Max Tokens muss zwischen 1 und 8000 liegen'
    }

    if (settings.top_p < 0 || settings.top_p > 1) {
      newErrors.top_p = 'Top P muss zwischen 0.0 und 1.0 liegen'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSave = () => {
    if (validate()) {
      onSave(settings)
      onClose()
    }
  }

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS)
    setErrors({})
  }

  const handleChange = (key: keyof AISettings, value: number) => {
    setSettings(prev => ({ ...prev, [key]: value }))
    // Clear error for this field
    if (errors[key]) {
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[key]
        return newErrors
      })
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">AI-Modell Einstellungen</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Temperature */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">
                Temperature
              </label>
              <span className="text-xs text-gray-500">
                {settings.temperature.toFixed(1)}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={settings.temperature}
              onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex items-center justify-between mt-1">
              <span className="text-xs text-gray-400">0.0 (Deterministisch)</span>
              <span className="text-xs text-gray-400">2.0 (Kreativ)</span>
            </div>
            {errors.temperature && (
              <p className="text-xs text-red-600 mt-1">{errors.temperature}</p>
            )}
            <div className="mt-2 flex items-start gap-2 text-xs text-gray-500">
              <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <p>
                Niedrige Werte (0.0-0.5): Konsistente, präzise Antworten. 
                Hohe Werte (1.0-2.0): Kreativere, variablere Antworten.
              </p>
            </div>
          </div>

          {/* Max Tokens */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">
                Max Tokens
              </label>
              <span className="text-xs text-gray-500">
                {settings.max_tokens}
              </span>
            </div>
            <input
              type="number"
              min="1"
              max="8000"
              value={settings.max_tokens}
              onChange={(e) => handleChange('max_tokens', parseInt(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.max_tokens && (
              <p className="text-xs text-red-600 mt-1">{errors.max_tokens}</p>
            )}
            <div className="mt-2 flex items-start gap-2 text-xs text-gray-500">
              <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <p>
                Maximale Anzahl der Tokens in der Antwort. Höhere Werte ermöglichen längere Antworten, 
                verbrauchen aber mehr Tokens.
              </p>
            </div>
          </div>

          {/* Top P */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">
                Top P
              </label>
              <span className="text-xs text-gray-500">
                {settings.top_p.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={settings.top_p}
              onChange={(e) => handleChange('top_p', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex items-center justify-between mt-1">
              <span className="text-xs text-gray-400">0.0 (Fokus)</span>
              <span className="text-xs text-gray-400">1.0 (Breit)</span>
            </div>
            {errors.top_p && (
              <p className="text-xs text-red-600 mt-1">{errors.top_p}</p>
            )}
            <div className="mt-2 flex items-start gap-2 text-xs text-gray-500">
              <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <p>
                Nucleus Sampling: Steuert die Vielfalt der Antworten. 
                Niedrige Werte: Fokus auf wahrscheinlichste Tokens. 
                Hohe Werte: Breitere Auswahl.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-gray-200">
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Zurücksetzen
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
            >
              Abbrechen
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Speichern
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

