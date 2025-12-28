/**
 * Analytics Story Mode ("Einfach erklärt")
 *
 * Ziel: Analytics so erklären, dass es auch ein 10-jähriges Kind versteht.
 * Prinzip: Progressive Disclosure – erst die 4 Bausteine, dann "Warum #1 oben?".
 */
 
'use client'

import { useMemo, useState } from 'react'
import { BarChart3, Sparkles, Layers, ArrowRight, Info, CheckCircle2 } from 'lucide-react'

type Score = {
  chunk_id: string
  vector_score?: number
  text_score?: number
  hybrid_score?: number
  ml_score?: number
  ml_score_raw?: number
  final_score?: number
  rank_position?: number
  _extended_metadata?: {
    document_title?: string
    page_number?: number
    shap_explanation?: unknown
    [key: string]: unknown
  }
}

type LiveModelInfo = {
  model_info?: {
    hybrid_weight?: number
    ml_weight?: number
  }
}

export default function AnalyticsStoryMode(props: {
  query: string
  scores: Score[]
  liveModelInfo?: LiveModelInfo | null
  onShowDetails: () => void
  onGoChat: () => void
  onShowShap: () => void
}) {
  const { query, scores, liveModelInfo, onShowDetails, onGoChat, onShowShap } = props
  const [showMoreWhy, setShowMoreWhy] = useState(false)

  const sorted = useMemo(() => {
    const copy = [...scores]
    copy.sort((a, b) => (a.rank_position ?? 999) - (b.rank_position ?? 999))
    return copy
  }, [scores])

  const top = sorted[0]
  const topDoc = top?._extended_metadata?.document_title ?? 'Dokument'
  const topPage = top?._extended_metadata?.page_number

  const rawValues = useMemo(() => {
    return sorted
      .map(s => s.ml_score_raw)
      .filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
  }, [sorted])
  const rawMin = rawValues.length ? Math.min(...rawValues) : undefined
  const rawMax = rawValues.length ? Math.max(...rawValues) : undefined

  const hybridWeight = liveModelInfo?.model_info?.hybrid_weight ?? 0.6
  const mlWeight = liveModelInfo?.model_info?.ml_weight ?? 0.4

  const percent = (v?: number) => (typeof v === 'number' ? `${(v * 100).toFixed(1)}%` : '—')

  const whyBullets = useMemo(() => {
    if (!top) return []
    const out: string[] = []
    const vs = top.vector_score ?? 0
    const ts = top.text_score ?? 0
    const ms = top.ml_score
    if (vs >= 0.6) out.push('Es klingt inhaltlich sehr ähnlich zu deiner Frage (Vector hoch).')
    else out.push('Es ist inhaltlich passend (Vector).')
    if (ts >= 0.55) out.push('Viele Wörter passen gut zusammen (Text hoch).')
    if (typeof ms === 'number') {
      if (ms >= 0.7) out.push('Der „Lern‑Teil“ (ML) hat es zusätzlich nach oben geschoben.')
      else if (ms <= 0.3) out.push('Der „Lern‑Teil“ (ML) hat es eher runtergezogen – trotzdem war Hybrid stark.')
      else out.push('Der „Lern‑Teil“ (ML) war mittel und hat etwas mitgeholfen.')
    }
    out.push(`Am Ende mischen wir beides: Final = ${hybridWeight}×Hybrid + ${mlWeight}×ML.`)
    return out
  }, [top, hybridWeight, mlWeight])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-start justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-blue-900">
              <BarChart3 className="w-4 h-4" />
              Einfach erklärt
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mt-2">Warum ist eine Textstelle oben?</h2>
            <p className="text-sm text-gray-700 mt-2 max-w-3xl">
              Wir bauen den Score wie ein Rezept: erst <span className="font-semibold">Finden</span>, dann{" "}
              <span className="font-semibold">Mischen</span>, dann <span className="font-semibold">Lernen</span>, dann{" "}
              <span className="font-semibold">Final</span>.
            </p>
            <div className="mt-3 text-xs text-gray-600">
              <span className="font-semibold">Mini-Wörterbuch:</span> „Chunk“ = „Textstelle“ (ein kleines Stück Text aus einem Dokument).
            </div>
            <div className="mt-3 text-sm text-gray-700">
              <span className="font-semibold">Frage:</span> “{query}”
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={onGoChat}
              className="px-4 py-2 rounded-lg bg-white border border-gray-200 text-sm font-semibold text-gray-800 hover:bg-gray-50"
            >
              Neue Frage stellen
            </button>
            <button
              type="button"
              onClick={onShowDetails}
              className="px-4 py-2 rounded-lg bg-blue-600 text-sm font-semibold text-white hover:bg-blue-700"
            >
              Zu Pro-Ansicht <ArrowRight className="inline w-4 h-4 ml-1" />
            </button>
          </div>
        </div>
      </div>

      {/* Rezept-Leiste (ultra-simpel) */}
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <div className="text-sm font-semibold text-gray-900 mb-2">Das Rezept (kurz)</div>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
          <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg p-2">
            <CheckCircle2 className="w-4 h-4 text-blue-700" />
            <span><span className="font-semibold">1.</span> Finden</span>
          </div>
          <div className="flex items-center gap-2 bg-indigo-50 border border-indigo-200 rounded-lg p-2">
            <CheckCircle2 className="w-4 h-4 text-indigo-700" />
            <span><span className="font-semibold">2.</span> Mischen</span>
          </div>
          <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg p-2">
            <CheckCircle2 className="w-4 h-4 text-green-700" />
            <span><span className="font-semibold">3.</span> Lernen</span>
          </div>
          <div className="flex items-center gap-2 bg-pink-50 border border-pink-200 rounded-lg p-2">
            <CheckCircle2 className="w-4 h-4 text-pink-700" />
            <span><span className="font-semibold">4.</span> Final sortieren</span>
          </div>
        </div>
      </div>

      {/* Step Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-blue-600 text-white font-bold">1</span>
            <h3 className="text-lg font-bold text-gray-900">Finden</h3>
          </div>
          <p className="text-sm text-gray-700 mb-4">
            Das System sucht in deinen Dokumenten nach Textstellen, die zur Frage passen.
          </p>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="text-xs text-gray-700">Vector (Inhalt)</div>
              <div className="text-xl font-bold text-blue-800">{percent(top?.vector_score)}</div>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
              <div className="text-xs text-gray-700">Text (Wörter)</div>
              <div className="text-xl font-bold text-purple-800">{percent(top?.text_score)}</div>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600 text-white font-bold">2</span>
            <h3 className="text-lg font-bold text-gray-900">Mischen (Hybrid)</h3>
          </div>
          <p className="text-sm text-gray-700 mb-4">
            Wir mischen Inhalt + Wörter. Dadurch entsteht der <span className="font-semibold">Hybrid</span>.
          </p>
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
            <div className="text-xs text-gray-700">Hybrid = 0.7×Vector + 0.3×Text</div>
            <div className="text-xl font-bold text-indigo-800 mt-1">{percent(top?.hybrid_score)}</div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-green-600 text-white font-bold">3</span>
            <h3 className="text-lg font-bold text-gray-900">Lernen (ML)</h3>
          </div>
          <p className="text-sm text-gray-700 mb-4">
            Ein Modell gibt erst <span className="font-semibold">Roh‑Punkte</span> aus. Damit man es wie Prozent lesen kann,
            rechnen wir die Roh‑Punkte für diese Suche auf 0–100% um.
          </p>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="text-xs text-gray-700">ML (normalisiert)</div>
              <div className="text-xl font-bold text-green-800">{percent(top?.ml_score)}</div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <div className="text-xs text-gray-700">ML roh (Punkte)</div>
              <div className="text-xl font-bold text-gray-900">
                {typeof top?.ml_score_raw === 'number' ? top.ml_score_raw.toFixed(3) : '—'}
              </div>
            </div>
          </div>
          {typeof rawMin === 'number' && typeof rawMax === 'number' && (
            <div className="mt-3 text-xs text-gray-600">
              Roh‑Punkte in dieser Suche: min {rawMin.toFixed(3)} • max {rawMax.toFixed(3)}
            </div>
          )}

          {/* Feedback Hinweis (kindgerecht) */}
          <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-xs text-yellow-900">
            <span className="font-semibold">Wichtig:</span> Dein 👍/👎 Feedback ändert den ML‑Teil nicht sofort.
            Es wird gesammelt, dann wird das Modell später neu trainiert – <span className="font-semibold">ab dann</span> kann der ML‑Score besser werden.
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-pink-600 text-white font-bold">4</span>
            <h3 className="text-lg font-bold text-gray-900">Final (Ranking)</h3>
          </div>
          <p className="text-sm text-gray-700 mb-4">
            Zum Schluss mischen wir Hybrid und ML. Das ist der Score, nach dem sortiert wird.
          </p>
          <div className="bg-pink-50 border border-pink-200 rounded-lg p-3">
            <div className="text-xs text-gray-700">Final = {hybridWeight}×Hybrid + {mlWeight}×ML</div>
            <div className="text-xl font-bold text-pink-800 mt-1">{percent(top?.final_score)}</div>
          </div>
        </div>
      </div>

      {/* Why #1 */}
      {top && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-600" />
                <h3 className="text-lg font-bold text-gray-900">Warum ist #1 oben?</h3>
              </div>
              <p className="text-sm text-gray-700 mt-2">
                <span className="font-semibold">{topDoc}</span>
                {typeof topPage === 'number' ? ` • Seite ${topPage}` : ''}
              </p>
            </div>
            <button
              type="button"
              onClick={onShowShap}
              className="px-3 py-2 rounded-lg bg-gray-900 text-white text-sm font-semibold hover:bg-black"
            >
              „Warum?“ (SHAP) ansehen
            </button>
          </div>

          <ul className="mt-4 space-y-2 text-sm text-gray-800">
            {(showMoreWhy ? whyBullets : whyBullets.slice(0, 3)).map((t, idx) => (
              <li key={idx} className="flex gap-2">
                <span className="mt-1 w-2 h-2 rounded-full bg-blue-600 flex-shrink-0" />
                <span>{t}</span>
              </li>
            ))}
          </ul>

          {whyBullets.length > 3 && (
            <button
              type="button"
              onClick={() => setShowMoreWhy(v => !v)}
              className="mt-3 text-sm font-semibold text-blue-700 hover:text-blue-900 underline"
            >
              {showMoreWhy ? 'Weniger anzeigen' : 'Mehr anzeigen'}
            </button>
          )}

          <div className="mt-4 bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-700 flex items-start gap-2">
            <Info className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
            <div>
              <span className="font-semibold">Merke:</span> Hybrid ist immer 0–100%. ML startet als Roh‑Punkte und wird für diese Suche in 0–100% umgerechnet, damit man es gut vergleichen kann.
            </div>
          </div>
        </div>
      )}

      {/* Tiny footer */}
      <div className="flex items-center justify-between text-xs text-gray-600">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4" />
          <span>{scores.length} Chunks in dieser Suche</span>
        </div>
        <button
          type="button"
          onClick={onShowDetails}
          className="text-blue-700 hover:text-blue-900 font-semibold underline"
        >
          Details & Charts öffnen
        </button>
      </div>
    </div>
  )
}


