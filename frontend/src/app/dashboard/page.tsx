'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { createCase, listCases } from '@/lib/api'
import { CaseItem, TriageCategory } from '@/lib/types'

export default function DashboardPage() {
  const [cases, setCases] = useState<CaseItem[]>([])
  const [triageCodes] = useState<TriageCategory[]>(['IMMEDIATE', 'DELAYED', 'MINIMAL', 'EXPECTANT', 'DECEASED'])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [triageCat, setTriageCat] = useState<TriageCategory>('IMMEDIATE')
  const [callsign, setCallsign] = useState('')
  const [fullName, setFullName] = useState('')
  const [unit, setUnit] = useState('')
  const [notes, setNotes] = useState('')

  async function reload() {
    try {
      setLoading(true)
      const caseItems = await listCases()
      setCases(caseItems)
      setError('')
    } catch (e) {
      setError('Не вдалося завантажити дані')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    reload()
  }, [])

  const stats = useMemo(() => {
    return {
      total: cases.length,
      critical: cases.filter((c) => c.triage_code === 'IMMEDIATE').length,
      urgent: cases.filter((c) => c.triage_code === 'DELAYED').length,
      wounded: cases.filter((c) => c.triage_code === 'MINIMAL').length,
      contused: cases.filter((c) => c.triage_code === 'EXPECTANT').length,
      dead: cases.filter((c) => c.triage_code === 'DECEASED').length,
    }
  }, [cases])

  async function onCreateCase(e: React.FormEvent) {
    e.preventDefault()
    try {
      await createCase({
        triage_code: triageCat,
        case_status: 'ACTIVE',
        callsign,
        full_name: fullName,
        unit,
        notes,
        tourniquet_applied: false
      } as any)
      setCallsign('')
      setFullName('')
      setUnit('')
      setNotes('')
      await reload()
    } catch (e) {
      setError('Не вдалося створити кейс')
    }
  }

  return (
    <div className="flex-1 flex flex-col">
      <header className="border-b border-[#262a30] bg-[#101317]">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="wolf-h1">БОЙОВИЙ РЕЖИМ</h1>
            <p className="wolf-title">командний центр</p>
          </div>
          <div className="flex gap-2">
            <Link href="/protocols" className="wolf-btn">ПРОТОКОЛИ</Link>
            <Link href="/exports" className="wolf-btn">ЕКСПОРТ</Link>
            <Link href="/audit" className="wolf-btn">АУДИТ</Link>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto"><div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {error && <div className="wolf-panel p-3 text-red-400 text-sm">{error}</div>}

        <section className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <div className="wolf-panel p-4"><div className="wolf-title">всього</div><div className="text-2xl">{stats.total}</div></div>
          <div className="wolf-panel p-4"><div className="wolf-title">ЕКСТРЕННО</div><div className="text-2xl text-red-400">{stats.critical}</div></div>
          <div className="wolf-panel p-4"><div className="wolf-title">ВІДСТРОЧЕНО</div><div className="text-2xl text-orange-400">{stats.urgent}</div></div>
          <div className="wolf-panel p-4"><div className="wolf-title">МІНІМАЛЬНО</div><div className="text-2xl text-amber-300">{stats.wounded}</div></div>
          <div className="wolf-panel p-4"><div className="wolf-title">ОЧІКУЮТЬ</div><div className="text-2xl text-blue-300">{stats.contused}</div></div>
          <div className="wolf-panel p-4"><div className="wolf-title">ЗАГИБЛІ</div><div className="text-2xl text-gray-400">{stats.dead}</div></div>
        </section>

        <section className="wolf-panel p-4">
          <div className="wolf-title mb-3">новий протокол / кейс</div>
          <form onSubmit={onCreateCase} className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <select className="wolf-input" value={triageCat} onChange={(e) => setTriageCat(e.target.value as unknown as TriageCategory)}>
              {triageCodes.map((code) => (
                <option key={code} value={code}>{code}</option>
              ))}
            </select>
            <input className="wolf-input" placeholder="Позивний" value={callsign} onChange={(e) => setCallsign(e.target.value)} />
            <input className="wolf-input" placeholder="ПІБ" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            <input className="wolf-input" placeholder="Підрозділ" value={unit} onChange={(e) => setUnit(e.target.value)} />
            <input className="wolf-input" placeholder="Нотатки" value={notes} onChange={(e) => setNotes(e.target.value)} />
            <button type="submit" className="wolf-btn-danger md:col-span-3">ЗБЕРЕГТИ КЕЙС</button>
          </form>
        </section>

        <section className="wolf-panel p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="wolf-title">активні кейси</div>
            <button className="wolf-btn" onClick={reload}>ОНОВИТИ</button>
          </div>
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b border-[#2a2f37]">
                  <th className="py-2">TRIAGE</th>
                  <th className="py-2">ПОЗИВНИЙ</th>
                  <th className="py-2">ПІБ</th>
                  <th className="py-2">ПІДРОЗДІЛ</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td className="py-3" colSpan={5}>Завантаження...</td></tr>
                ) : cases.length === 0 ? (
                  <tr><td className="py-3 text-gray-500" colSpan={5}>Кейсів немає</td></tr>
                ) : (
                  cases.map((c) => (
                    <tr key={c.id} className="border-b border-[#232830]">
                      <td className="py-2">{c.triage_code || '-'}</td>
                      <td className="py-2">{c.callsign || '-'}</td>
                      <td className="py-2">{c.full_name || '-'}</td>
                      <td className="py-2">{c.unit || '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
      </main>
    </div>
  )
}
