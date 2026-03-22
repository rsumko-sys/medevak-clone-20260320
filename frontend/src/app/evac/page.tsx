'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { PlaneTakeoff, ShieldAlert, ArrowRightCircle, CheckCircle, Clock, ArrowLeft } from 'lucide-react'
import { listCases, updateCase } from '@/lib/api'
import { CaseItem } from '@/lib/types'

export default function EvacPage() {
  const [cases, setCases] = useState<CaseItem[]>([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [confirmHandoff, setConfirmHandoff] = useState<string | null>(null)

  useEffect(() => {
    load()
  }, [])

  async function load() {
    try {
      setLoading(true)
      setError(null)
      const items = await listCases()
      setCases(items)
    } catch (e) {
      console.error('Failed to load cases:', e)
      setError('Помилка завантаження даних євакуації')
    } finally {
      setLoading(false)
    }
  }

  async function handleStatusChange(caseId: string, newStatus: string) {
    if (updating) return
    setUpdating(caseId)
    try {
      setError(null)
      await updateCase(caseId, { case_status: newStatus } as any)
      await load()
    } catch (e) {
      console.error('Failed to update evac status', e)
      setError('Помилка оновлення статусу евакуації')
    } finally {
      setUpdating(null)
    }
  }

  // Filter cases relevant to evac
  const evacCases = cases.filter(c => ['AWAITING_EVAC', 'IN_TRANSPORT', 'HANDED_OFF'].includes(c.case_status))
  
  const awaitingCount = evacCases.filter(c => c.case_status === 'AWAITING_EVAC').length
  const inTransitCount = evacCases.filter(c => c.case_status === 'IN_TRANSPORT').length
  const completedCount = evacCases.filter(c => c.case_status === 'HANDED_OFF').length

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      {/* Top Header Section */}
      <div className="flex justify-between items-start mb-6">
        <div className="flex items-center gap-3">
          <Link href="/command" className="p-2 rounded-md bg-[#1a1d24] border border-[#2a2f3a] text-gray-400 hover:text-white hover:bg-[#252a33] transition-colors outline-none focus:outline-none">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
          <h1 className="text-xl font-bold tracking-widest text-white uppercase mb-1">МЕДИЧНА ЄВАКУАЦІЯ</h1>
          <p className="text-xs text-gray-500 font-mono tracking-widest uppercase">9-LINE / ZMIST ТРАКІНГ</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button onClick={load} className="px-4 py-2 border border-[#262a30] bg-[#1a1d24] rounded-md text-xs font-bold tracking-widest text-gray-400 hover:text-white uppercase transition-colors">
            Оновити Дані
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-900/20 border border-red-900/50 rounded-md text-red-400 text-xs font-bold uppercase tracking-widest flex items-center justify-between">
          <span>⚠ {error}</span>
          <button onClick={load} className="underline text-red-300 hover:text-white">Повторити</button>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
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

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
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
              ) : evacCases.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-sm text-gray-500">Немає пацієнтів у черзі на евакуацію</td>
                </tr>
              ) : (
                evacCases.map((c) => (
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
                        confirmHandoff === c.id ? (
                          <div className="flex gap-1 ml-auto">
                            <button
                              onClick={() => { handleStatusChange(c.id, 'HANDED_OFF'); setConfirmHandoff(null) }}
                              className="flex items-center gap-1 px-2 py-1.5 bg-green-900 border border-green-600 rounded-sm text-green-300 text-xs font-bold uppercase"
                            >
                              <CheckCircle className="w-3 h-3" /> ПІДТВЕРДИТИ
                            </button>
                            <button
                              onClick={() => setConfirmHandoff(null)}
                              className="px-2 py-1.5 border border-[#262a30] bg-[#1a1d24] rounded-sm text-gray-400 text-xs font-bold"
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          <button 
                            onClick={() => setConfirmHandoff(c.id)}
                            className="flex items-center gap-2 ml-auto px-3 py-1.5 bg-green-900/30 hover:bg-green-600 border border-green-800 rounded-sm text-green-400 hover:text-white transition-colors text-xs font-bold tracking-widest uppercase"
                          >
                            <ArrowRightCircle className="w-3 h-3" /> ЗАВЕРШИТИ
                          </button>
                        )
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
