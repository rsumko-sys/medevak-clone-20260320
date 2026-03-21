'use client'

import { useEffect, useMemo, useState } from 'react'
import { PlaneTakeoff, ShieldAlert, ArrowRightCircle, CheckCircle, Clock } from 'lucide-react'
import { listCases, updateCase } from '@/lib/api'
import { CaseItem } from '@/lib/types'

type EvacSortKey = 'newest' | 'oldest' | 'triage' | 'unit'

const EVAC_FILTERS_KEY = 'evacTableFilters:v1'

function readEvacFilters() {
  if (typeof window === 'undefined') {
    return { search: '', triage: 'all', status: 'all', unit: 'all', sort: 'newest' as EvacSortKey }
  }
  try {
    const raw = window.localStorage.getItem(EVAC_FILTERS_KEY)
    if (!raw) return { search: '', triage: 'all', status: 'all', unit: 'all', sort: 'newest' as EvacSortKey }
    const parsed = JSON.parse(raw) as {
      search?: string
      triage?: string
      status?: string
      unit?: string
      sort?: EvacSortKey
    }
    return {
      search: parsed.search || '',
      triage: parsed.triage || 'all',
      status: parsed.status || 'all',
      unit: parsed.unit || 'all',
      sort: parsed.sort || 'newest',
    }
  } catch {
    return { search: '', triage: 'all', status: 'all', unit: 'all', sort: 'newest' as EvacSortKey }
  }
}

export default function EvacPage() {
  const initialFilters = readEvacFilters()
  const [cases, setCases] = useState<CaseItem[]>([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<string | null>(null)
  const [search, setSearch] = useState(initialFilters.search)
  const [filterTriage, setFilterTriage] = useState(initialFilters.triage)
  const [filterStatus, setFilterStatus] = useState(initialFilters.status)
  const [filterUnit, setFilterUnit] = useState(initialFilters.unit)
  const [sortBy, setSortBy] = useState<EvacSortKey>(initialFilters.sort)

  useEffect(() => {
    load()
  }, [])

  async function load() {
    try {
      setLoading(true)
      const items = await listCases()
      setCases(items)
    } catch (e) {
      console.error('Failed to load cases:', e)
    } finally {
      setLoading(false)
    }
  }

  async function handleStatusChange(caseId: string, newStatus: string) {
    if (updating) return
    setUpdating(caseId)
    try {
      await updateCase(caseId, { evac_status: newStatus } as any)
      await load()
    } catch (e) {
      console.error('Failed to update evac status', e)
    } finally {
      setUpdating(null)
    }
  }

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(
      EVAC_FILTERS_KEY,
      JSON.stringify({ search, triage: filterTriage, status: filterStatus, unit: filterUnit, sort: sortBy }),
    )
  }, [search, filterTriage, filterStatus, filterUnit, sortBy])

  // Filter cases relevant to evac
  const evacCases = cases.filter(c => ['AWAITING_EVAC', 'IN_TRANSPORT', 'HANDED_OFF'].includes(c.case_status))

  const unitOptions = useMemo(() => {
    const set = new Set<string>()
    for (const item of evacCases) {
      const value = (item.unit || '').trim()
      if (value) set.add(value)
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b, 'uk'))
  }, [evacCases])

  const triageSortOrder: Record<string, number> = {
    IMMEDIATE: 0,
    DELAYED: 1,
    MINIMAL: 2,
    EXPECTANT: 3,
    DECEASED: 4,
  }

  const viewCases = useMemo(() => {
    const filtered = evacCases.filter((c) => {
      const q = search.trim().toLowerCase()
      const matchesSearch = !q ||
        c.case_number?.toLowerCase().includes(q) ||
        c.callsign?.toLowerCase().includes(q) ||
        c.full_name?.toLowerCase().includes(q) ||
        c.unit?.toLowerCase().includes(q)
      const matchesTriage = filterTriage === 'all' || c.triage_code === filterTriage
      const matchesStatus = filterStatus === 'all' || c.case_status === filterStatus
      const matchesUnit = filterUnit === 'all' || (c.unit || '') === filterUnit
      return matchesSearch && matchesTriage && matchesStatus && matchesUnit
    })

    return filtered.sort((a, b) => {
      if (sortBy === 'unit') return (a.unit || '').localeCompare((b.unit || ''), 'uk')
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
  }, [evacCases, search, filterTriage, filterStatus, filterUnit, sortBy])
  
  const awaitingCount = evacCases.filter(c => c.case_status === 'AWAITING_EVAC').length
  const inTransitCount = evacCases.filter(c => c.case_status === 'IN_TRANSPORT').length
  const completedCount = evacCases.filter(c => c.case_status === 'HANDED_OFF').length

  return (
    <div className="flex-1 p-4 md:p-6 overflow-y-auto">
      {/* Top Header Section */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3 mb-4 md:mb-6">
        <div>
          <h1 className="text-xl font-bold tracking-widest text-white uppercase mb-1">МЕДИЧНА ЄВАКУАЦІЯ</h1>
          <p className="text-xs text-gray-500 font-mono tracking-widest uppercase">9-LINE / ZMIST ТРАКІНГ</p>
        </div>
        <div className="flex gap-3 w-full sm:w-auto">
          <button onClick={load} className="w-full sm:w-auto px-4 py-2 border border-[#262a30] bg-[#1a1d24] rounded-md text-xs font-bold tracking-widest text-gray-400 hover:text-white uppercase transition-colors">
            Оновити Дані
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4 md:mb-6">
        <div className="wolf-panel p-5 relative overflow-hidden group border-b-2 border-b-orange-900/50">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-3xl font-bold text-orange-400">{awaitingCount}</h2>
            <Clock className="w-5 h-5 text-orange-900/50" />
          </div>
          <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">ОЧІКУЮТЬ ЕВАКУАЦІЮ</p>
        </div>

        <div className="wolf-panel p-5 relative overflow-hidden group border-b-2 border-b-blue-900/50">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-3xl font-bold text-blue-500">{inTransitCount}</h2>
            <PlaneTakeoff className="w-5 h-5 text-blue-900/50" />
          </div>
          <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">В ДОРОЗІ (IN TRANSIT)</p>
        </div>

        <div className="wolf-panel p-5 relative overflow-hidden group border-b-2 border-b-green-900/50">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-3xl font-bold text-green-500">{completedCount}</h2>
            <CheckCircle className="w-5 h-5 text-green-900/50" />
          </div>
          <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">ПЕРЕДАНО (HANDED OFF)</p>
        </div>
      </div>

      {/* Main Table */}
      <div className="wolf-panel p-5">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-sm font-bold tracking-widest uppercase text-white flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-orange-500" />
            ЧЕРГА НА ЕВАКУАЦІЮ
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-2 mb-4">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Пошук (кейс/позивний/підрозділ)"
            className="wolf-input text-xs md:col-span-2"
          />
          <select className="wolf-input text-xs" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="all">Всі статуси евак</option>
            <option value="AWAITING_EVAC">AWAITING_EVAC</option>
            <option value="IN_TRANSPORT">IN_TRANSPORT</option>
            <option value="HANDED_OFF">HANDED_OFF</option>
          </select>
          <select className="wolf-input text-xs" value={filterTriage} onChange={(e) => setFilterTriage(e.target.value)}>
            <option value="all">Всі triage</option>
            <option value="IMMEDIATE">IMMEDIATE</option>
            <option value="DELAYED">DELAYED</option>
            <option value="MINIMAL">MINIMAL</option>
            <option value="EXPECTANT">EXPECTANT</option>
            <option value="DECEASED">DECEASED</option>
          </select>
          <select className="wolf-input text-xs" value={filterUnit} onChange={(e) => setFilterUnit(e.target.value)}>
            <option value="all">Всі підрозділи</option>
            {unitOptions.map((unit) => (
              <option key={unit} value={unit}>{unit}</option>
            ))}
          </select>
        </div>

        <div className="mb-4">
          <select className="wolf-input text-xs w-full md:w-80" value={sortBy} onChange={(e) => setSortBy(e.target.value as EvacSortKey)}>
            <option value="newest">Сортування: найновіші</option>
            <option value="oldest">Сортування: найстаріші</option>
            <option value="triage">Сортування: triage пріоритет</option>
            <option value="unit">Сортування: підрозділ A-Z</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[780px] text-left border-collapse">
            <thead>
              <tr className="border-b border-[#262a30] text-[10px] text-gray-500 uppercase tracking-widest">
                <th className="py-3 px-2 font-medium">КЕЙС / ПАЦІЄНТ</th>
                <th className="py-3 px-2 font-medium">ТРІАЖ</th>
                <th className="py-3 px-2 font-medium">МЕХАНІЗМ ТРАВМИ</th>
                <th className="py-3 px-2 font-medium">СТАТУС ЕВАКУАЦІЇ</th>
                <th className="py-3 px-2 font-medium text-right">ДІЯ</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-sm text-gray-500">Завантаження...</td>
                </tr>
              ) : viewCases.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-sm text-gray-500">Немає пацієнтів за поточними фільтрами</td>
                </tr>
              ) : (
                viewCases.map((c) => (
                  <tr key={c.id} className="border-b border-[#262a30]/50 hover:bg-[#1a1d24] transition-colors text-sm">
                    <td className="py-4 px-2">
                      <div className="font-bold text-white">{c.case_number || c.callsign || '-'}</div>
                      <div className="text-xs text-gray-500 mt-1">{c.full_name || 'Невідомий'} / {c.unit || '-'}</div>
                    </td>
                    <td className="py-4 px-2">
                      {c.triage_code ? (
                        <span className={`inline-block px-2 py-1 text-[10px] font-bold tracking-widest uppercase rounded-sm ${c.triage_code === 'IMMEDIATE' ? 'bg-red-900/30 text-red-500 border border-red-900' : 'bg-orange-900/30 text-orange-500 border border-orange-900'}`}>
                          {c.triage_code}
                        </span>
                      ) : '-'}
                    </td>
                    <td className="py-4 px-2">
                      <div className="text-gray-300 font-medium">{c.mechanism_of_injury || 'Не вказано'}</div>
                      <div className="text-xs text-gray-500 mt-1 truncate max-w-[200px]">{c.notes || '-'}</div>
                    </td>
                    <td className="py-4 px-2">
                      <span className={`inline-block px-2 text-xs font-bold rounded-sm ${c.case_status === 'AWAITING_EVAC' ? 'text-orange-400' : c.case_status === 'IN_TRANSPORT' ? 'text-blue-400' : 'text-green-500'}`}>
                        {c.case_status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-4 px-2 text-right">
                      {c.case_status === 'AWAITING_EVAC' && (
                        <button 
                          onClick={() => handleStatusChange(c.id, 'IN_TRANSPORT')}
                          className="flex items-center gap-2 ml-auto px-3 py-1.5 bg-blue-900/30 hover:bg-blue-600 border border-blue-800 rounded-sm text-blue-400 hover:text-white transition-colors text-xs font-bold tracking-widest uppercase"
                        >
                          <PlaneTakeoff className="w-3 h-3" /> ПОЧАТИ ЕВАК
                        </button>
                      )}
                      {c.case_status === 'IN_TRANSPORT' && (
                        <button 
                          onClick={() => handleStatusChange(c.id, 'HANDED_OFF')}
                          className="flex items-center gap-2 ml-auto px-3 py-1.5 bg-green-900/30 hover:bg-green-600 border border-green-800 rounded-sm text-green-400 hover:text-white transition-colors text-xs font-bold tracking-widest uppercase"
                        >
                          <ArrowRightCircle className="w-3 h-3" /> ЗАВЕРШИТИ
                        </button>
                      )}
                      {c.case_status === 'HANDED_OFF' && (
                        <span className="inline-flex items-center gap-2 ml-auto px-3 py-1.5 opacity-50 text-xs font-bold tracking-widest uppercase text-gray-500">
                          <CheckCircle className="w-3 h-3" /> ГОТОВО
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
