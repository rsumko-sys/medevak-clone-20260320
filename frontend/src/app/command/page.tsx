'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Users, PlaneTakeoff, Box, CheckCircle, FileText, RefreshCw } from 'lucide-react'
import { getCase, listCases } from '@/lib/api'
import { CaseItem } from '@/lib/types'
import StatCard from '@/components/StatCard'
import TriageDistributor from '@/components/TriageDistributor'
import PatientTable from '@/components/PatientTable'
import EvacuationStatus from '@/components/EvacuationStatus'

type CommandTab = 'dashboard' | 'form100'

type Form100Row = {
  caseId: string
  callsign: string
  triageCode: string
  caseStatus: string
  hasForm100: boolean
  documentNumber: string
  updatedAt: string
}

export default function CommandPage() {
  const [cases, setCases] = useState<CaseItem[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<CommandTab>('dashboard')
  const [form100Rows, setForm100Rows] = useState<Form100Row[]>([])
  const [form100Loading, setForm100Loading] = useState(false)
  const [form100Error, setForm100Error] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const items = await listCases()
        setCases(items)
      } catch (e) {
        console.error('Failed to load cases:', e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  async function loadForm100Overview() {
    if (cases.length === 0) {
      setForm100Rows([])
      return
    }

    setForm100Loading(true)
    setForm100Error('')
    try {
      // Keep command view responsive by checking only recent cases.
      const scope = cases.slice(0, 20)
      const details = await Promise.allSettled(scope.map((c) => getCase(c.id)))

      const rows: Form100Row[] = scope.map((c, index) => {
        const result = details[index]
        if (result.status === 'fulfilled') {
          const form = result.value.form100
          return {
            caseId: c.id,
            callsign: c.callsign,
            triageCode: c.triage_code || '-',
            caseStatus: c.case_status || '-',
            hasForm100: !!form,
            documentNumber: form?.document_number || '-',
            updatedAt: form?.updated_at || form?.created_at || '-',
          }
        }

        return {
          caseId: c.id,
          callsign: c.callsign,
          triageCode: c.triage_code || '-',
          caseStatus: c.case_status || '-',
          hasForm100: false,
          documentNumber: 'Помилка читання',
          updatedAt: '-',
        }
      })

      setForm100Rows(rows)
    } catch (e) {
      console.error('Failed to load Form 100 overview:', e)
      setForm100Error('Не вдалося завантажити огляд FORM 100')
    } finally {
      setForm100Loading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'form100') {
      loadForm100Overview()
    }
  }, [activeTab, cases])

  // Mock stats for the UI
  const stats = {
    total: cases.length,
    awaitingEvac: cases.filter(c => c.case_status === 'AWAITING_EVAC').length || 0,
    shortage: 0,
    evacuated: cases.filter(c => c.case_status === 'HANDED_OFF').length || 0,
    triage: {
      urgent: cases.filter(c => c.triage_code === 'IMMEDIATE').length,
      wounded: cases.filter(c => c.triage_code === 'DELAYED').length,
      concussed: cases.filter(c => c.triage_code === 'MINIMAL').length,
      light: cases.filter(c => c.triage_code === 'EXPECTANT').length,
      kia: cases.filter(c => c.triage_code === 'DECEASED').length,
    }
  }

  const recentCases = cases.slice(0, 5)
  const coveredCount = form100Rows.filter((r) => r.hasForm100).length
  const missingCount = form100Rows.length - coveredCount

  return (
    <div className="flex-1 p-4 md:p-6 space-y-4 md:space-y-6">
      
      {/* Page Title (Internal) */}
      <div className="mb-2">
        <h1 className="text-2xl font-black tracking-tighter text-white uppercase">Dashboard</h1>
      </div>

      <div className="border border-[#2a2f37] bg-[#161a20] rounded-lg p-1 inline-flex gap-1">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-4 py-2 text-xs font-bold tracking-[0.1em] rounded ${
            activeTab === 'dashboard'
              ? 'bg-[#242a33] text-white border border-[#3a424f]'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          ДАШБОРД
        </button>
        <button
          onClick={() => setActiveTab('form100')}
          className={`px-4 py-2 text-xs font-bold tracking-[0.1em] rounded flex items-center gap-2 ${
            activeTab === 'form100'
              ? 'bg-[#242a33] text-white border border-[#3a424f]'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <FileText className="w-4 h-4" />
          FORM 100 (ОФІЦІЙНИЙ ОБЛІК ПОРАНЕННЯ)
        </button>
      </div>

      {activeTab === 'dashboard' && (
        <>

          {/* Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 md:gap-6">
            <StatCard 
              title="всього поранених" 
              value={stats.total} 
              icon={Users} 
            />
            <StatCard 
              title="очікують евакуацію" 
              value={stats.awaitingEvac} 
              icon={PlaneTakeoff} 
              colorClass="text-orange-400"
              borderColor="border-b-orange-900/50"
            />
            <StatCard 
              title="нестача запасів" 
              value={stats.shortage} 
              icon={Box} 
              colorClass="text-red-500"
              borderColor="border-b-red-900/50"
            />
            <StatCard 
              title="евакуйовано" 
              value={stats.evacuated} 
              icon={CheckCircle} 
              colorClass="text-green-500"
              borderColor="border-b-green-900/50"
            />
          </div>

          {/* Middle Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
            <TriageDistributor stats={stats.triage} />
            <EvacuationStatus />
          </div>

          {/* Recent Patients Table */}
          <PatientTable cases={recentCases} loading={loading} />
        </>
      )}

      {activeTab === 'form100' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[#15181e] border border-[#2a2f37] rounded-lg p-4">
              <div className="text-xs text-gray-400 tracking-wider">КЕЙСИ В ОГЛЯДІ</div>
              <div className="text-2xl font-black text-white mt-1">{form100Rows.length}</div>
            </div>
            <div className="bg-[#15181e] border border-[#2a2f37] rounded-lg p-4">
              <div className="text-xs text-gray-400 tracking-wider">FORM 100 ЗАПОВНЕНО</div>
              <div className="text-2xl font-black text-green-400 mt-1">{coveredCount}</div>
            </div>
            <div className="bg-[#15181e] border border-[#2a2f37] rounded-lg p-4">
              <div className="text-xs text-gray-400 tracking-wider">ПОТРЕБУЄ ЗАПОВНЕННЯ</div>
              <div className="text-2xl font-black text-amber-400 mt-1">{missingCount}</div>
            </div>
          </div>

          <div className="flex items-center justify-between bg-[#15181e] border border-[#2a2f37] rounded-lg p-3">
            <div className="text-sm text-gray-300">
              Окрема вкладка FORM 100 для командного контролю по кейсах.
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={loadForm100Overview}
                className="wolf-btn inline-flex items-center gap-2"
                disabled={form100Loading}
              >
                <RefreshCw className={`w-4 h-4 ${form100Loading ? 'animate-spin' : ''}`} />
                Оновити
              </button>
              <Link href="/cases" className="wolf-btn">
                Відкрити CASES
              </Link>
            </div>
          </div>

          <div className="bg-[#15181e] border border-[#2a2f37] rounded-lg overflow-auto">
            <table className="w-full min-w-[860px] text-sm">
              <thead className="bg-[#1b2028] text-gray-400">
                <tr>
                  <th className="text-left px-3 py-2">CASE ID</th>
                  <th className="text-left px-3 py-2">CALLSIGN</th>
                  <th className="text-left px-3 py-2">TRIAGE</th>
                  <th className="text-left px-3 py-2">STATUS</th>
                  <th className="text-left px-3 py-2">FORM 100</th>
                  <th className="text-left px-3 py-2">ДОКУМЕНТ</th>
                  <th className="text-left px-3 py-2">ОНОВЛЕНО</th>
                </tr>
              </thead>
              <tbody>
                {form100Loading && (
                  <tr>
                    <td className="px-3 py-3 text-gray-400" colSpan={7}>Завантаження FORM 100...</td>
                  </tr>
                )}
                {!form100Loading && form100Error && (
                  <tr>
                    <td className="px-3 py-3 text-red-400" colSpan={7}>{form100Error}</td>
                  </tr>
                )}
                {!form100Loading && !form100Error && form100Rows.length === 0 && (
                  <tr>
                    <td className="px-3 py-3 text-gray-500" colSpan={7}>Немає кейсів для огляду.</td>
                  </tr>
                )}
                {!form100Loading && !form100Error && form100Rows.map((row) => (
                  <tr key={row.caseId} className="border-t border-[#232933] text-gray-200">
                    <td className="px-3 py-2 font-mono text-xs">{row.caseId.slice(0, 8)}...</td>
                    <td className="px-3 py-2">{row.callsign || '-'}</td>
                    <td className="px-3 py-2">{row.triageCode}</td>
                    <td className="px-3 py-2">{row.caseStatus}</td>
                    <td className="px-3 py-2">
                      <span className={row.hasForm100 ? 'text-green-400' : 'text-amber-400'}>
                        {row.hasForm100 ? 'Заповнено' : 'Відсутня'}
                      </span>
                    </td>
                    <td className="px-3 py-2">{row.documentNumber}</td>
                    <td className="px-3 py-2">{row.updatedAt === '-' ? '-' : new Date(row.updatedAt).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  )
}
