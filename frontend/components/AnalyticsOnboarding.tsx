/**
 * Analytics Onboarding Component
 * 
 * Zeigt eine Onboarding-Tour für neue User.
 * 
 * NEU v2.10.0
 */

'use client'

import { useState } from 'react'
import { X, ChevronRight, ChevronLeft, CheckCircle } from 'lucide-react'

interface OnboardingStep {
  title: string
  description: string
  target?: string // CSS Selector für Highlight
}

const onboardingSteps: OnboardingStep[] = [
  {
    title: 'Willkommen im Analytics Dashboard!',
    description: 'Dieses Dashboard zeigt dir detaillierte Analysen deiner RAG-Chat-Anfragen. Du siehst Scores, Metriken und SHAP-Erklärungen.',
  },
  {
    title: 'Query & Quick Summary',
    description: 'Oben siehst du die bewertete Frage und die wichtigsten Metriken auf einen Blick: NDCG@10, Precision@10 und MRR.',
  },
  {
    title: 'Detaillierte Scores',
    description: 'Im Tab "Detaillierte Scores" siehst du alle Score-Typen (Vector, Text, Hybrid, ML) für jedes Suchergebnis.',
  },
  {
    title: 'SHAP-Analyse',
    description: 'Im Tab "SHAP Analyse" siehst du, welche Features zum Ranking beitragen. Verschiedene Visualisierungen helfen dir, die Daten zu verstehen.',
  },
  {
    title: 'System Info',
    description: 'Im Tab "System Info" findest du technische Details über das RAG-System, Cache-Performance und Background-Daten.',
  },
]

interface AnalyticsOnboardingProps {
  onComplete?: () => void
}

export default function AnalyticsOnboarding({ onComplete }: AnalyticsOnboardingProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [isVisible, setIsVisible] = useState(true)

  const handleNext = () => {
    if (currentStep < onboardingSteps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      handleComplete()
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleComplete = () => {
    setIsVisible(false)
    // Speichere in localStorage, dass Onboarding abgeschlossen wurde
    localStorage.setItem('analytics_onboarding_completed', 'true')
    if (onComplete) {
      onComplete()
    }
  }

  if (!isVisible) return null

  const step = onboardingSteps[currentStep]
  const progress = ((currentStep + 1) / onboardingSteps.length) * 100

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full mx-4 border-2 border-blue-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-t-xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-2">{step.title}</h2>
              <div className="flex items-center gap-2 text-sm opacity-90">
                <span>Schritt {currentStep + 1} von {onboardingSteps.length}</span>
              </div>
            </div>
            <button
              onClick={handleComplete}
              className="text-white/80 hover:text-white transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="h-2 bg-gray-200">
          <div
            className="h-full bg-gradient-to-r from-blue-600 to-purple-600 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Content */}
        <div className="p-8">
          <p className="text-lg text-gray-700 mb-6">{step.description}</p>

          {/* Step Indicators */}
          <div className="flex items-center justify-center gap-2 mb-6">
            {onboardingSteps.map((_, index) => (
              <div
                key={index}
                className={`w-3 h-3 rounded-full transition-all ${
                  index === currentStep
                    ? 'bg-blue-600 w-8'
                    : index < currentStep
                    ? 'bg-green-500'
                    : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-6 flex items-center justify-between">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${
              currentStep === 0
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            Zurück
          </button>

          <button
            onClick={handleComplete}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
          >
            Überspringen
          </button>

          <button
            onClick={handleNext}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            {currentStep === onboardingSteps.length - 1 ? (
              <>
                <CheckCircle className="w-4 h-4" />
                Fertig
              </>
            ) : (
              <>
                Weiter
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

