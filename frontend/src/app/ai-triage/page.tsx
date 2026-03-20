'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

interface TriageSuggestion {
  case_id: string
  suggested_triage: '+' | '!' | '300' | '400' | '200'
  confidence: number
  reasoning: string
  vitals?: {
    heart_rate?: number
    blood_pressure?: string
    oxygen_sat?: number
    respiratory_rate?: number
  }
  injuries?: string[]
  ai_model: string
  timestamp: string
}

export default function AiTriagePage() {
  const [cases, setCases] = useState<TriageSuggestion[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function loadAiTriage() {
    try {
      setLoading(true)
      // Симуляція AI API - замінити на реальний endpoint
      const mockData: TriageSuggestion[] = [
        {
          case_id: 'case-001',
          suggested_triage: '+',
          confidence: 0.94,
          reasoning: 'Критична кровотеча, нестабільні показники життєдіяльності',
          vitals: {
            heart_rate: 140,
            blood_pressure: '80/40',
            oxygen_sat: 85,
            respiratory_rate: 28
          },
          injuries: [' penetrating chest wound', ' massive hemorrhage'],
          ai_model: 'Triage-Med-V2',
          timestamp: new Date().toISOString()
        },
        {
          case_id: 'case-002',
          suggested_triage: '!',
          confidence: 0.87,
          reasoning: 'Стабільні показники, але потребує негайної медичної допомоги',
          vitals: {
            heart_rate: 110,
            blood_pressure: '110/70',
            oxygen_sat: 92,
            respiratory_rate: 20
          },
          injuries: ['fractured femur', 'moderate bleeding'],
          ai_model: 'Triage-Med-V2',
          timestamp: new Date().toISOString()
        }
      ]
      setCases(mockData)
      setError('')
    } catch (e) {
      setError('Не вдалося завантажити AI тріаж')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAiTriage()
  }, [])

  const triageColors = {
    '+': 'bg-red-900 text-red-400',
    '!': 'bg-orange-900 text-orange-400',
    '300': 'bg-yellow-900 text-yellow-400',
    '400': 'bg-blue-900 text-blue-400',
    '200': 'bg-gray-800 text-gray-400'
  }

  const triageLabels = {
    '+': 'НЕГАЙНИЙ',
    '!': 'ТЕРМІНОВИЙ',
    '300': 'ПОТРЕБУЄ',
    '400': 'ЛЕГКИЙ',
    '200': 'ПОМЕРЛИЙ'
  }

  return (
    <div className="flex-1 flex flex-col">
      <header className="border-b border-[#262a30] bg-[#101317]">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="wolf-h1">AI ТРІАЖ</h1>
            <p className="wolf-title">автоматична класифікація пацієнтів</p>
          </div>
          <div className="flex gap-2">
            <Link href="/" className="wolf-btn">ГОЛОВНА</Link>
            <button onClick={loadAiTriage} className="wolf-btn">ОНОВИТИ</button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-4">
        {loading && <div className="wolf-panel p-4">Аналіз AI...</div>}
        
        {error && !loading && (
          <div className="wolf-panel p-4 text-red-400">{error}</div>
        )}

        {!loading && cases.length === 0 && !error && (
          <div className="wolf-panel p-4 text-gray-400">Немає даних для аналізу</div>
        )}

        {cases.map((caseData) => (
          <section key={caseData.case_id} className="wolf-panel p-4">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="wolf-title mb-2">Кейс: {caseData.case_id}</div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 text-xs ${triageColors[caseData.suggested_triage]}`}>
                    {caseData.suggested_triage} - {triageLabels[caseData.suggested_triage]}
                  </span>
                  <span className="text-xs text-gray-400">
                    Точність: {Math.round(caseData.confidence * 100)}%
                  </span>
                </div>
              </div>
              <div className="text-xs text-gray-500">
                {new Date(caseData.timestamp).toLocaleString()}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="wolf-title mb-2">AI Аналіз</div>
                <div className="text-sm text-gray-300 mb-2">{caseData.reasoning}</div>
                <div className="text-xs text-gray-500">Модель: {caseData.ai_model}</div>
              </div>

              {caseData.vitals && (
                <div>
                  <div className="wolf-title mb-2">Показники</div>
                  <div className="text-sm space-y-1">
                    <div>ЧСС: {caseData.vitals.heart_rate}</div>
                    <div>Тиск: {caseData.vitals.blood_pressure}</div>
                    <div>SaO₂: {caseData.vitals.oxygen_sat}%</div>
                    <div>ЧД: {caseData.vitals.respiratory_rate}</div>
                  </div>
                </div>
              )}
            </div>

            {caseData.injuries && caseData.injuries.length > 0 && (
              <div className="mt-4">
                <div className="wolf-title mb-2">Травми</div>
                <div className="flex flex-wrap gap-2">
                  {caseData.injuries.map((injury, idx) => (
                    <span key={idx} className="px-2 py-1 bg-[#1a2333] border border-[#3b4350] text-xs">
                      {injury}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-4 flex gap-2">
              <button
                onClick={() => alert('Рекомендацію зафіксовано в цьому режимі перегляду.')}
                className="wolf-btn-green"
              >
                ПРИЙНЯТИ РЕКОМЕНДАЦІЮ
              </button>
              <button
                onClick={() => alert('Детальний клінічний розбір буде доступний у наступному релізі.')}
                className="wolf-btn"
              >
                ПЕРЕГЛЯНУТИ ДЕТАЛІ
              </button>
            </div>
          </section>
        ))}
      </main>
    </div>
  )
}
