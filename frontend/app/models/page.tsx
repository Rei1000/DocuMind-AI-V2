'use client'

import { useState, useEffect } from 'react'

interface AIModel {
  id: string
  name: string
  provider: string
  model: string
  temperature: number
  max_tokens: number
  prompt: string
  latency: number
  metrics: {
    requests: number
    success_rate: number
    avg_response_time: number
  }
}

export default function ModelsPage() {
  const [models, setModels] = useState<AIModel[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Mock data for now
    setModels([
      {
        id: '1',
        name: 'GPT-4 Vision',
        provider: 'OpenAI',
        model: 'gpt-4-vision-preview',
        temperature: 0.7,
        max_tokens: 4096,
        prompt: 'Analyze this document and extract key information...',
        latency: 2.3,
        metrics: {
          requests: 1250,
          success_rate: 98.5,
          avg_response_time: 2.1
        }
      },
      {
        id: '2',
        name: 'Claude 3',
        provider: 'Anthropic',
        model: 'claude-3-opus-20240229',
        temperature: 0.5,
        max_tokens: 8192,
        prompt: 'Process the following quality management document...',
        latency: 1.8,
        metrics: {
          requests: 890,
          success_rate: 99.2,
          avg_response_time: 1.7
        }
      }
    ])
    setLoading(false)
  }, [])

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading models...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-foreground mb-8">AI Models</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {models.map((model) => (
          <div key={model.id} className="border rounded-lg p-6 hover:bg-accent transition-colors">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-semibold">{model.name}</h2>
              <span className="text-sm text-muted-foreground">{model.provider}</span>
            </div>
            
            <div className="space-y-2 mb-4">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Model:</span>
                <span className="text-sm font-mono">{model.model}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Temperature:</span>
                <span className="text-sm">{model.temperature}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Max Tokens:</span>
                <span className="text-sm">{model.max_tokens.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Latency:</span>
                <span className="text-sm">{model.latency}s</span>
              </div>
            </div>

            <div className="border-t pt-4">
              <h3 className="text-sm font-medium mb-2">Metrics</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-muted-foreground">Requests:</span>
                  <div className="font-semibold">{model.metrics.requests.toLocaleString()}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Success Rate:</span>
                  <div className="font-semibold">{model.metrics.success_rate}%</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Avg Response:</span>
                  <div className="font-semibold">{model.metrics.avg_response_time}s</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
