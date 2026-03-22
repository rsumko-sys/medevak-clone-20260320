'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { listCases, getCase } from '@/lib/api'
import { CaseDetails, CaseItem } from '@/lib/types'

export default function CasesPage() {
  const [cases, setCases] = useState<CaseItem[]>([])
  const [selectedCase, setSelectedCase] = useState<CaseDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterTriage, setFilterTriage] = useState('all')
  const [error, setError] = useState<string | null>(null)

  const searchParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null
  const caseIdParam = searchParams?.get('id')

  async function loadCases() {
    try {
      setLoading(true)
      setError(null)
      const items = await listCases()
      setCases(items)
      
      const targetId = caseIdParam || (items.length > 0 ? items[0].id : null)
      if (targetId) {
        const details = await getCase(targetId)
        setSelectedCase(details)
      }
    } catch (e) {
      console.error('Failed to load cases:', e)
      setError("Помилка завантаження кейсів. Перевірте з'єднання з сервером.")
    } finally {
      setLoading(false)
    }
  }

  async function selectCase(caseId: string) {
    try {
      const details = await getCase(caseId)
      setSelectedCase(details)
    } catch (e) {
      console.error('Failed to load case details:', e)
      setError('Помилка завантаження деталей кейсу.')
    }
  }

  useEffect(() => {
    loadCases()
  }, [])

  const filteredCases = cases.filter(c => {
    const matchesSearch = !search || 
      c.callsign?.toLowerCase().includes(search.toLowerCase()) ||
      c.full_name?.toLowerCase().includes(search.toLowerCase()) ||
      c.unit?.toLowerCase().includes(search.toLowerCase())
    
    const matchesTriage = filterTriage === 'all' || c.triage_code === filterTriage
    
    return matchesSearch && matchesTriage
  })

  const triageColors: Record<string, string> = {
    'IMMEDIATE': 'bg-red-900 text-red-400',
    'DELAYED': 'bg-orange-900 text-orange-400',
    'MINIMAL': 'bg-yellow-900 text-yellow-400',
    'EXPECTANT': 'bg-blue-900 text-blue-400',
    'DECEASED': 'bg-gray-800 text-gray-400'
  }

  return (
    <div className="flex-1 flex flex-col">
      <header className="border-b border-[#262a30] bg-[#101317]">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/command" className="p-2 rounded-md bg-[#1a1d24] border border-[#2a2f3a] text-gray-400 hover:text-white hover:bg-[#252a33] transition-colors outline-none focus:outline-none">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
            <h1 className="wolf-h1">МЕДИЧНІ КЕЙСИ</h1>
            <p className="wolf-title">управління пацієнтами та протоколами</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Link href="/ai-triage" className="wolf-btn">AI ТРІАЖ</Link>
            <Link href="/exports" className="wolf-btn">ЕКСПОРТ</Link>
            <Link href="/audit" className="wolf-btn">АУДИТ</Link>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto"><div className="max-w-7xl mx-auto px-4 py-6">
        {error && (
          <div className="mb-4 px-4 py-3 bg-red-900/20 border border-red-900/50 rounded-md text-red-400 text-xs font-bold uppercase tracking-widest flex items-center justify-between">
            <span>⚠ {error}</span>
            <button onClick={loadCases} className="underline text-red-300 hover:text-white">Повторити</button>
          </div>
        )}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Left sidebar - cases list */}
          <div className="lg:col-span-1">
            <div className="wolf-panel p-4">
              <div className="wolf-title mb-3">фільтр</div>
              <input
                type="text"
                placeholder="Пошук..."
                className="wolf-input w-full mb-3"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <select
                className="wolf-input w-full"
                value={filterTriage}
                onChange={(e) => setFilterTriage(e.target.value)}
              >
                <option value="all">Всі статуси</option>
                <option value="IMMEDIATE">+ Екстренно</option>
                <option value="DELAYED">! Відстрочено</option>
                <option value="MINIMAL">300 Мінімально</option>
                <option value="EXPECTANT">400 Очікують</option>
                <option value="DECEASED">200 Померлі</option>
              </select>
            </div>

            <div className="wolf-panel p-4 mt-4">
              <div className="wolf-title mb-3">кейси ({filteredCases.length})</div>
              <div className="space-y-2 max-h-96 overflow-auto">
                {loading ? (
                  <div className="text-sm text-gray-400">Завантаження...</div>
                ) : filteredCases.length === 0 ? (
                  <div className="text-sm text-gray-400">Кейсів не знайдено</div>
                ) : (
                  filteredCases.map((caseItem) => (
                    <button
                      key={caseItem.id}
                      onClick={() => selectCase(caseItem.id)}
                      className={`w-full text-left p-2 border border-borderContent hover:border-red-500 transition-colors ${
                        selectedCase?.id === caseItem.id ? 'border-red-500' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm">
                          {caseItem.callsign || caseItem.full_name || caseItem.id.slice(0, 8)}
                        </span>
                        {caseItem.triage_code && (
                          <span className={`px-1 py-0 text-xs ${triageColors[caseItem.triage_code]}`}>
                            {caseItem.triage_code}
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {caseItem.unit || 'Невідомий підрозділ'}
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Main content - case details */}
          <div className="lg:col-span-3">
            {selectedCase ? (
              <div className="space-y-4">
                {/* Patient info header */}
                <div className="wolf-panel p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-lg font-bold mb-2">
                        {selectedCase.callsign || selectedCase.full_name || 'Невідомий'}
                      </h2>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <div className="text-gray-400">Статус</div>
                          <div>{selectedCase.case_status || '-'}</div>
                        </div>
                        <div>
                          <div className="text-gray-400">Підрозділ</div>
                          <div>{selectedCase.unit || '-'}</div>
                        </div>
                        <div>
                          <div className="text-gray-400">Група крові</div>
                          <div>{selectedCase.blood_type || '-'}</div>
                        </div>
                        <div>
                          <div className="text-gray-400">Triage</div>
                          <div>
                            {selectedCase.triage_code ? (
                              <span className={`px-2 py-1 text-xs ${triageColors[selectedCase.triage_code]}`}>
                                {selectedCase.triage_code}
                              </span>
                            ) : '-'}
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="text-right text-xs text-gray-400">
                      {selectedCase.injury_datetime ? new Date(selectedCase.injury_datetime).toLocaleString() : '-'}
                    </div>
                  </div>
                </div>

                {/* MARCH assessment */}
                <div className="wolf-panel p-4">
                  <div className="wolf-title mb-3">MARCH ОЦІНКА(placeholder)</div>
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-sm">
                    <div className="wolf-panel p-3">
                      <div className="text-red-400 font-bold mb-1">A</div>
                      <div className="text-gray-400">Airway</div>
                      <div>{'Норма'}</div>
                    </div>
                    <div className="wolf-panel p-3">
                      <div className="text-orange-400 font-bold mb-1">B</div>
                      <div className="text-gray-400">Breathing</div>
                      <div>{'Норма'}</div>
                    </div>
                    <div className="wolf-panel p-3">
                      <div className="text-yellow-400 font-bold mb-1">C</div>
                      <div className="text-gray-400">Circulation</div>
                      <div>{'Норма'}</div>
                    </div>
                    <div className="wolf-panel p-3">
                      <div className="text-green-400 font-bold mb-1">H</div>
                      <div className="text-gray-400">Head injury</div>
                      <div>{'Немає'}</div>
                    </div>
                    <div className="wolf-panel p-3">
                      <div className="text-blue-400 font-bold mb-1">R</div>
                      <div className="text-gray-400">Rest of body</div>
                      <div>{'Норма'}</div>
                    </div>
                  </div>
                </div>

                {/* Procedures */}
                <div className="wolf-panel p-4">
                  <div className="wolf-title mb-3">ТРАВМИ</div>
                  <div className="space-y-2 max-h-48 overflow-auto">
                    {selectedCase.injuries && selectedCase.injuries.length > 0 ? (
                      selectedCase.injuries.map((injury, idx) => (
                        <div key={idx} className="text-sm border-b border-borderContent pb-1">
                          <div className="flex justify-between items-center">
                            <span className="font-bold">{injury.body_region}</span>
                            <span className="text-xs text-gray-400">{injury.severity}</span>
                          </div>
                          <div>{injury.injury_type}</div>
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-gray-400">Травм не зафіксовано</div>
                    )}
                  </div>
                </div>

                {/* Notes */}
                {selectedCase.notes && (
                  <div className="wolf-panel p-4">
                    <div className="wolf-title mb-3">нотатки</div>
                    <div className="text-sm text-gray-300">{selectedCase.notes}</div>
                  </div>
                )}
              </div>
            ) : (
              <div className="wolf-panel p-8 text-center text-gray-400">
                Оберіть кейс для перегляду деталей
              </div>
            )}
          </div>
        </div>
      </div>
      </main>
    </div>
  )
}
