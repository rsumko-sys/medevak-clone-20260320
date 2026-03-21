'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { createForm100, getCase, updateForm100, listCases } from '@/lib/api'
import { CaseDetails, CaseItem } from '@/lib/types'
import { buildDraftFromForm100, buildPayloadFromDraft, emptyForm100Draft } from '@/lib/form100-ui-sync'

type CaseSortKey = 'newest' | 'oldest' | 'triage' | 'callsign'
const CASES_SLICE_LIMIT = 100

function getInitialFilters() {
  if (typeof window === 'undefined') {
    return {
      caseId: null as string | null,
      search: '',
      triage: 'all',
      status: 'all',
      unit: 'all',
      sort: 'newest' as CaseSortKey,
    }
  }

  const q = new URLSearchParams(window.location.search)
  const sort = (q.get('sort') as CaseSortKey) || 'newest'
  return {
    caseId: q.get('id'),
    search: q.get('search') || '',
    triage: q.get('triage') || 'all',
    status: q.get('status') || 'all',
    unit: q.get('unit') || 'all',
    sort,
  }
}

export default function CasesPage() {
  const initial = getInitialFilters()
  const [cases, setCases] = useState<CaseItem[]>([])
  const [selectedCase, setSelectedCase] = useState<CaseDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState(initial.search)
  const [filterTriage, setFilterTriage] = useState(initial.triage)
  const [filterStatus, setFilterStatus] = useState(initial.status)
  const [filterUnit, setFilterUnit] = useState(initial.unit)
  const [sortBy, setSortBy] = useState<CaseSortKey>(initial.sort)
  const [savingForm100, setSavingForm100] = useState(false)
  const [form100Draft, setForm100Draft] = useState(() => emptyForm100Draft())

  const updateQuery = (updates: Record<string, string | null>) => {
    if (typeof window === 'undefined') return
    const q = new URLSearchParams(window.location.search)
    for (const [key, value] of Object.entries(updates)) {
      if (!value || value === 'all' || value === '') q.delete(key)
      else q.set(key, value)
    }
    const queryString = q.toString()
    const nextUrl = `${window.location.pathname}${queryString ? `?${queryString}` : ''}`
    window.history.replaceState({}, '', nextUrl)
  }

  async function loadCases() {
    try {
      setLoading(true)
      const items = await listCases({ offset: 0, limit: CASES_SLICE_LIMIT })
      setCases(items)
      
      const caseIdFromUrl = typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('id') : null
      const targetId = caseIdFromUrl || (items.length > 0 ? items[0].id : null)
      if (targetId) {
        const details = await getCase(targetId)
        setSelectedCase(details)
      }
    } catch (e) {
      console.error('Failed to load cases:', e)
    } finally {
      setLoading(false)
    }
  }

  async function selectCase(caseId: string) {
    try {
      const details = await getCase(caseId)
      setSelectedCase(details)
      updateQuery({ id: caseId })
    } catch (e) {
      console.error('Failed to load case details:', e)
    }
  }

  useEffect(() => {
    const f = selectedCase?.form100
    if (!f) {
      setForm100Draft(emptyForm100Draft())
      return
    }

    setForm100Draft(buildDraftFromForm100(f))
  }, [selectedCase?.id, selectedCase?.form100])

  async function saveForm100() {
    if (!selectedCase) return
    if (!form100Draft.document_number || !form100Draft.injury_datetime || !form100Draft.injury_location || !form100Draft.injury_mechanism || !form100Draft.diagnosis_summary || !form100Draft.documented_by) {
      alert('Form 100: заповніть обов\'язкові поля')
      return
    }

    setSavingForm100(true)
    try {
      const payload = buildPayloadFromDraft(form100Draft)
      if (selectedCase.form100?.id) {
        await updateForm100(selectedCase.id, payload)
      } else {
        await createForm100(selectedCase.id, payload)
      }
      const refreshed = await getCase(selectedCase.id)
      setSelectedCase(refreshed)
      alert('Form 100 збережено')
    } catch (e) {
      console.error('Failed to save Form 100', e)
      alert('Не вдалося зберегти Form 100')
    } finally {
      setSavingForm100(false)
    }
  }

  useEffect(() => {
    loadCases()
  }, [])

  useEffect(() => {
    updateQuery({
      search,
      triage: filterTriage,
      status: filterStatus,
      unit: filterUnit,
      sort: sortBy,
    })
  }, [search, filterTriage, filterStatus, filterUnit, sortBy])

  const unitOptions = useMemo(() => {
    const units = new Set<string>()
    for (const caseItem of cases) {
      const value = (caseItem.unit || '').trim()
      if (value) units.add(value)
    }
    return Array.from(units).sort((a, b) => a.localeCompare(b, 'uk'))
  }, [cases])

  const triageSortOrder: Record<string, number> = {
    IMMEDIATE: 0,
    DELAYED: 1,
    MINIMAL: 2,
    EXPECTANT: 3,
    DECEASED: 4,
  }

  const filteredCases = useMemo(() => {
    const filtered = cases.filter(c => {
      const q = search.trim().toLowerCase()
      const matchesSearch = !q ||
        c.callsign?.toLowerCase().includes(q) ||
        c.full_name?.toLowerCase().includes(q) ||
        c.unit?.toLowerCase().includes(q) ||
        c.case_number?.toLowerCase().includes(q)

      const matchesTriage = filterTriage === 'all' || c.triage_code === filterTriage
      const matchesStatus = filterStatus === 'all' || c.case_status === filterStatus
      const matchesUnit = filterUnit === 'all' || (c.unit || '') === filterUnit

      return matchesSearch && matchesTriage && matchesStatus && matchesUnit
    })

    return filtered.sort((a, b) => {
      if (sortBy === 'callsign') {
        const aKey = (a.callsign || a.full_name || '').toLowerCase()
        const bKey = (b.callsign || b.full_name || '').toLowerCase()
        return aKey.localeCompare(bKey, 'uk')
      }

      if (sortBy === 'triage') {
        const rankA = triageSortOrder[a.triage_code || ''] ?? 99
        const rankB = triageSortOrder[b.triage_code || ''] ?? 99
        if (rankA !== rankB) return rankA - rankB
      }

      const aTime = a.injury_datetime ? new Date(a.injury_datetime).getTime() : 0
      const bTime = b.injury_datetime ? new Date(b.injury_datetime).getTime() : 0
      if (sortBy === 'oldest') return aTime - bTime
      return bTime - aTime
    })
  }, [cases, search, filterTriage, filterStatus, filterUnit, sortBy])

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
        <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="wolf-h1">МЕДИЧНІ КЕЙСИ</h1>
            <p className="wolf-title">управління пацієнтами та протоколами</p>
          </div>
          <div className="flex gap-2 w-full sm:w-auto overflow-x-auto">
            <Link href="/ai-triage" className="wolf-btn">AI ТРІАЖ</Link>
            <Link href="/exports" className="wolf-btn">ЕКСПОРТ</Link>
            <Link href="/audit" className="wolf-btn">АУДИТ</Link>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto"><div className="max-w-7xl mx-auto px-4 py-4 md:py-6">
        <div className="mb-4 border border-amber-700/40 bg-amber-950/30 px-3 py-2 text-xs text-amber-200">
          Показано лише частину даних. Фільтри і сортування застосовуються до поточного завантаженого slice (до {CASES_SLICE_LIMIT} кейсів).
        </div>
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
              <select
                className="wolf-input w-full mt-3"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <option value="all">Всі case status</option>
                <option value="ACTIVE">ACTIVE</option>
                <option value="STABILIZING">STABILIZING</option>
                <option value="AWAITING_EVAC">AWAITING_EVAC</option>
                <option value="IN_TRANSPORT">IN_TRANSPORT</option>
                <option value="HANDED_OFF">HANDED_OFF</option>
                <option value="CLOSED">CLOSED</option>
                <option value="DECEASED">DECEASED</option>
              </select>
              <select
                className="wolf-input w-full mt-3"
                value={filterUnit}
                onChange={(e) => setFilterUnit(e.target.value)}
              >
                <option value="all">Всі підрозділи</option>
                {unitOptions.map((unit) => (
                  <option key={unit} value={unit}>{unit}</option>
                ))}
              </select>
              <select
                className="wolf-input w-full mt-3"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as CaseSortKey)}
              >
                <option value="newest">Сортування: найновіші</option>
                <option value="oldest">Сортування: найстаріші</option>
                <option value="triage">Сортування: triage пріоритет</option>
                <option value="callsign">Сортування: позивний A-Z</option>
              </select>
            </div>

            <div className="wolf-panel p-4 mt-4">
              <div className="wolf-title mb-3">кейси ({filteredCases.length})</div>
              <div className="space-y-2 max-h-80 md:max-h-96 overflow-auto">
                {loading ? (
                  <div className="text-sm text-gray-400">Завантаження...</div>
                ) : filteredCases.length === 0 ? (
                  <div className="text-sm text-gray-400">Кейсів не знайдено</div>
                ) : (
                  filteredCases.map((caseItem) => (
                    <button
                      key={caseItem.id}
                      onClick={() => selectCase(caseItem.id)}
                      className={`w-full text-left p-2 border border-[#2a2f37] hover:border-red-500 transition-colors ${
                        selectedCase?.id === caseItem.id ? 'border-red-500' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm truncate">
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
                        <div key={idx} className="text-sm border-b border-[#2a2f37] pb-1">
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

                <div className="wolf-panel p-4">
                  <div className="wolf-title mb-3">FORM 100 (ОФІЦІЙНИЙ ОБЛІК ПОРАНЕННЯ)</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <input className="wolf-input" placeholder="Номер документа *" value={form100Draft.document_number} onChange={(e) => setForm100Draft((s) => ({ ...s, document_number: e.target.value }))} />
                    <input className="wolf-input" type="datetime-local" placeholder="Дата/час травми *" value={form100Draft.injury_datetime} onChange={(e) => setForm100Draft((s) => ({ ...s, injury_datetime: e.target.value }))} />
                    <input className="wolf-input" placeholder="Локація травми *" value={form100Draft.injury_location} onChange={(e) => setForm100Draft((s) => ({ ...s, injury_location: e.target.value }))} />
                    <input className="wolf-input" placeholder="Механізм травми *" value={form100Draft.injury_mechanism} onChange={(e) => setForm100Draft((s) => ({ ...s, injury_mechanism: e.target.value }))} />
                    <input className="wolf-input" placeholder="Хто документував *" value={form100Draft.documented_by} onChange={(e) => setForm100Draft((s) => ({ ...s, documented_by: e.target.value }))} />
                    <label className="flex items-center gap-2 text-sm text-gray-300 px-2">
                      <input type="checkbox" checked={form100Draft.commander_notified} onChange={(e) => setForm100Draft((s) => ({ ...s, commander_notified: e.target.checked }))} />
                      Командування повідомлено
                    </label>
                  </div>
                  <textarea className="wolf-input w-full mt-3" placeholder="Діагноз *" rows={3} value={form100Draft.diagnosis_summary} onChange={(e) => setForm100Draft((s) => ({ ...s, diagnosis_summary: e.target.value }))} />
                  <textarea className="wolf-input w-full mt-3" placeholder="Лікування (опційно)" rows={2} value={form100Draft.treatment_summary} onChange={(e) => setForm100Draft((s) => ({ ...s, treatment_summary: e.target.value }))} />
                  <textarea className="wolf-input w-full mt-3" placeholder="Рекомендація щодо евакуації (опційно)" rows={2} value={form100Draft.evacuation_recommendation} onChange={(e) => setForm100Draft((s) => ({ ...s, evacuation_recommendation: e.target.value }))} />
                  <textarea className="wolf-input w-full mt-3" placeholder="Додаткові примітки (опційно)" rows={2} value={form100Draft.notes} onChange={(e) => setForm100Draft((s) => ({ ...s, notes: e.target.value }))} />

                  <div className="mt-4 border-t border-[#2a2f37] pt-3">
                    <div className="text-sm font-semibold mb-2">Canonical: Stub / Markers / Evac / Stage log</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <input className="wolf-input" type="datetime-local" placeholder="Stub: issued_at" value={form100Draft.stub_issued_at} onChange={(e) => setForm100Draft((s) => ({ ...s, stub_issued_at: e.target.value }))} />
                      <input className="wolf-input" placeholder="Legal status" value={form100Draft.legal_status} onChange={(e) => setForm100Draft((s) => ({ ...s, legal_status: e.target.value }))} />

                      <input className="wolf-input" placeholder="Evac transport" value={form100Draft.evacuation_transport} onChange={(e) => setForm100Draft((s) => ({ ...s, evacuation_transport: e.target.value }))} />
                      <input className="wolf-input" placeholder="Evac destination" value={form100Draft.evacuation_destination} onChange={(e) => setForm100Draft((s) => ({ ...s, evacuation_destination: e.target.value }))} />
                      <input className="wolf-input" placeholder="Evac position" value={form100Draft.evacuation_position} onChange={(e) => setForm100Draft((s) => ({ ...s, evacuation_position: e.target.value }))} />
                      <input className="wolf-input" placeholder="Evac priority" value={form100Draft.evacuation_priority} onChange={(e) => setForm100Draft((s) => ({ ...s, evacuation_priority: e.target.value }))} />

                      <input className="wolf-input" placeholder="Body diagram placeholder model" value={form100Draft.body_diagram_placeholder_model} onChange={(e) => setForm100Draft((s) => ({ ...s, body_diagram_placeholder_model: e.target.value }))} />
                      <input className="wolf-input" placeholder="Body mark type" value={form100Draft.body_mark_type} onChange={(e) => setForm100Draft((s) => ({ ...s, body_mark_type: e.target.value }))} />
                      <input className="wolf-input" placeholder="Body mark location" value={form100Draft.body_mark_location} onChange={(e) => setForm100Draft((s) => ({ ...s, body_mark_location: e.target.value }))} />
                      <input className="wolf-input" placeholder="Body mark notes" value={form100Draft.body_mark_notes} onChange={(e) => setForm100Draft((s) => ({ ...s, body_mark_notes: e.target.value }))} />
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-3 text-sm">
                      <label className="flex items-center gap-2 text-gray-300"><input type="checkbox" checked={form100Draft.stub_isolation_flag} onChange={(e) => setForm100Draft((s) => ({ ...s, stub_isolation_flag: e.target.checked }))} /> Stub isolation</label>
                      <label className="flex items-center gap-2 text-gray-300"><input type="checkbox" checked={form100Draft.stub_urgent_care_flag} onChange={(e) => setForm100Draft((s) => ({ ...s, stub_urgent_care_flag: e.target.checked }))} /> Stub urgent</label>
                      <label className="flex items-center gap-2 text-gray-300"><input type="checkbox" checked={form100Draft.stub_sanitary_processing_flag} onChange={(e) => setForm100Draft((s) => ({ ...s, stub_sanitary_processing_flag: e.target.checked }))} /> Stub sanitary</label>
                      <label className="flex items-center gap-2 text-gray-300"><input type="checkbox" checked={form100Draft.first_eme_completed} onChange={(e) => setForm100Draft((s) => ({ ...s, first_eme_completed: e.target.checked }))} /> First EME</label>

                      <label className="flex items-center gap-2 text-gray-300"><input type="checkbox" checked={form100Draft.triage_red_urgent_care} onChange={(e) => setForm100Draft((s) => ({ ...s, triage_red_urgent_care: e.target.checked }))} /> Red urgent</label>
                      <label className="flex items-center gap-2 text-gray-300"><input type="checkbox" checked={form100Draft.triage_yellow_sanitary_processing} onChange={(e) => setForm100Draft((s) => ({ ...s, triage_yellow_sanitary_processing: e.target.checked }))} /> Yellow sanitary</label>
                      <label className="flex items-center gap-2 text-gray-300"><input type="checkbox" checked={form100Draft.triage_black_isolation} onChange={(e) => setForm100Draft((s) => ({ ...s, triage_black_isolation: e.target.checked }))} /> Black isolation</label>
                      <label className="flex items-center gap-2 text-gray-300"><input type="checkbox" checked={form100Draft.triage_blue_radiation_measures} onChange={(e) => setForm100Draft((s) => ({ ...s, triage_blue_radiation_measures: e.target.checked }))} /> Blue radiation</label>

                      <label className="flex items-center gap-2 text-gray-300"><input type="checkbox" checked={form100Draft.continuity_required} onChange={(e) => setForm100Draft((s) => ({ ...s, continuity_required: e.target.checked }))} /> Continuity required</label>
                    </div>

                    <textarea
                      className="wolf-input w-full mt-3 font-mono text-xs"
                      placeholder="Back-side stage_log JSON array"
                      rows={7}
                      value={form100Draft.stage_log_text}
                      onChange={(e) => setForm100Draft((s) => ({ ...s, stage_log_text: e.target.value }))}
                    />
                    <div className="text-xs text-gray-500 mt-1">stage_log має бути JSON-масивом (invalid JSON буде збережено як порожній масив)</div>
                  </div>

                  {selectedCase.form100?.front_side && (
                    <pre className="mt-3 max-h-48 overflow-auto text-xs text-gray-400 border border-[#2a2f37] p-2">{JSON.stringify(selectedCase.form100.front_side, null, 2)}</pre>
                  )}

                  <div className="mt-3 flex justify-end">
                    <button className="wolf-btn" onClick={saveForm100} disabled={savingForm100}>
                      {savingForm100 ? 'Збереження...' : (selectedCase.form100?.id ? 'Оновити Form 100' : 'Створити Form 100')}
                    </button>
                  </div>
                  <div className="text-xs text-gray-500 mt-2">* обов'язкові поля для офіційної фіксації</div>
                </div>
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
