'use client'

import { useEffect, useState } from 'react'
import { addMedication, addObservation, addProcedure, getCase, listCases } from '@/lib/api'
import { CaseDetails, CaseItem } from '@/lib/types'
import Link from 'next/link'
import { ClipboardCheck, Activity, Pill, Stethoscope, RefreshCw, AlertCircle, Plus, ArrowLeft } from 'lucide-react'

export default function ProtocolsPage() {
  const [cases, setCases] = useState<CaseItem[]>([])
  const [selectedCaseId, setSelectedCaseId] = useState('')
  const [details, setDetails] = useState<CaseDetails | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [obsType, setObsType] = useState('BP')
  const [obsValue, setObsValue] = useState('')
  const [procCode, setProcCode] = useState('TOURNIQUET')
  const [procNotes, setProcNotes] = useState('')
  const [medCode, setMedCode] = useState('TXA')
  const [medDose, setMedDose] = useState('')
  const [medUnit, setMedUnit] = useState('mg')

  async function loadCases() {
    try {
      const items = await listCases()
      setCases(items)
      if (!selectedCaseId && items[0]?.id) setSelectedCaseId(items[0].id)
    } catch {
      setError('Не вдалося завантажити кейси')
    }
  }

  async function loadDetails(caseId: string) {
    if (!caseId) return
    try {
      setLoading(true)
      const data = await getCase(caseId)
      setDetails(data)
      setError('')
    } catch {
      setError('Помилка завантаження даних')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCases()
  }, [])

  useEffect(() => {
    loadDetails(selectedCaseId)
  }, [selectedCaseId])

  async function submitObservation(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedCaseId || !obsValue) return
    const key = obsType.trim().toUpperCase()
    const numeric = Number(obsValue)
    if (Number.isNaN(numeric)) {
      setError('Значення має бути числом')
      return
    }

    const payload: Record<string, number> = {}
    if (key === 'HR') payload.heart_rate = numeric
    else if (key === 'RR') payload.respiratory_rate = numeric
    else if (key === 'SPO2') payload.spo2_percent = numeric
    else if (key === 'TEMP') payload.temperature_celsius = numeric
    else if (key === 'SYS') payload.systolic_bp = numeric
    else if (key === 'DIA') payload.diastolic_bp = numeric
    else {
      setError('Підтримка: HR, RR, SPO2, TEMP, SYS, DIA')
      return
    }

    await addObservation(selectedCaseId, payload)
    setObsValue('')
    setError('')
    await loadDetails(selectedCaseId)
  }

  async function submitProcedure(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedCaseId) return
    await addProcedure(selectedCaseId, { procedure_code: procCode, notes: procNotes })
    setProcNotes('')
    await loadDetails(selectedCaseId)
  }

  async function submitMedication(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedCaseId) return
    await addMedication(selectedCaseId, {
      medication_code: medCode,
      dose_value: medDose,
      dose_unit_code: medUnit,
      time_administered: new Date().toISOString(),
    })
    setMedDose('')
    await loadDetails(selectedCaseId)
  }

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      {/* Top Header Section */}
      <div className="flex justify-between items-start mb-6">
        <div className="flex items-center gap-3">
          <Link href="/command" className="p-2 rounded-md bg-[#1a1d24] border border-[#2a2f3a] text-gray-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
          <h1 className="text-xl font-bold tracking-widest text-white uppercase mb-1">КЛІНІЧНІ ПРОТОКОЛИ</h1>
          <p className="text-xs text-gray-500 font-mono tracking-widest uppercase">MARCH • TCCC • АДМІНІСТРУВАННЯ</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button onClick={() => loadDetails(selectedCaseId)} className="p-2 border border-[#262a30] bg-[#1a1d24] rounded-md text-gray-400 hover:text-white transition-colors">
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Case Selector and Info */}
        <div className="lg:col-span-1 space-y-4">
          <section className="wolf-panel p-5">
            <h3 className="text-xs font-bold tracking-widest text-gray-500 uppercase mb-4 flex items-center gap-2">
              <ClipboardCheck className="w-3 h-3 text-blue-500" /> ВИБІР ПАЦІЄНТА
            </h3>
            <select 
              className="w-full bg-[#1a1d24] border border-[#262a30] text-gray-300 rounded-md p-2 text-sm focus:outline-none focus:border-blue-500" 
              value={selectedCaseId} 
              onChange={(e) => setSelectedCaseId(e.target.value)}
            >
              <option value="">Оберіть зі списку...</option>
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {(c.triage_code || '-') + ' • ' + (c.callsign || c.full_name || c.id.slice(0, 8))}
                </option>
              ))}
            </select>
            
            {details && (
              <div className="mt-6 space-y-3 pt-6 border-t border-[#1a1d24]">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500 font-bold uppercase tracking-tighter">Позивний</span>
                  <span className="text-white font-bold uppercase">{details.callsign || '-'}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500 font-bold uppercase tracking-tighter">Тріаж</span>
                  <span className={`font-bold uppercase ${details.triage_code === 'IMMEDIATE' ? 'text-red-500' : 'text-orange-500'}`}>{details.triage_code || '-'}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500 font-bold uppercase tracking-tighter">Підрозділ</span>
                  <span className="text-gray-300 truncate max-w-[100px] text-right">{details.unit || '-'}</span>
                </div>
              </div>
            )}
            
            {error && (
              <div className="mt-4 p-2 bg-red-900/20 text-red-500 text-[10px] font-bold border border-red-900/50 rounded flex items-center gap-2">
                <AlertCircle className="w-3 h-3" /> {error}
              </div>
            )}
          </section>
        </div>

        {/* Action Forms */}
        <div className="lg:col-span-3 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Observations Form */}
            <section className="wolf-panel p-5 bg-[#1a1d24]/30">
              <h3 className="text-xs font-bold tracking-widest text-[#5e97ff] uppercase mb-4 flex items-center gap-2">
                <Activity className="w-3 h-3" /> ПОКАЗНИКИ (OBS)
              </h3>
              <form onSubmit={submitObservation} className="space-y-3">
                <input className="w-full bg-[#0f1217] border border-[#262a30] text-gray-200 p-2 text-xs rounded outline-none focus:border-blue-500" value={obsType} onChange={(e) => setObsType(e.target.value)} placeholder="Тип (HR, RR, SPO2, TEMP, SYS, DIA)" />
                <input className="w-full bg-[#0f1217] border border-[#262a30] text-gray-200 p-2 text-xs rounded outline-none focus:border-blue-500" value={obsValue} onChange={(e) => setObsValue(e.target.value)} placeholder="Значення" />
                <button type="submit" className="w-full py-2 bg-blue-900/20 hover:bg-blue-600 border border-blue-900 text-blue-400 hover:text-white transition-colors rounded-sm text-[10px] font-bold tracking-widest uppercase flex items-center justify-center gap-1">
                  <Plus className="w-3 h-3" /> ДОДАТИ
                </button>
              </form>
            </section>

            {/* Procedures Form */}
            <section className="wolf-panel p-5 bg-[#1a1d24]/30">
              <h3 className="text-xs font-bold tracking-widest text-green-500 uppercase mb-4 flex items-center gap-2">
                <Stethoscope className="w-3 h-3" /> МАНІПУЛЯЦІЇ (PROC)
              </h3>
              <form onSubmit={submitProcedure} className="space-y-3">
                <input className="w-full bg-[#0f1217] border border-[#262a30] text-gray-200 p-2 text-xs rounded outline-none focus:border-green-500" value={procCode} onChange={(e) => setProcCode(e.target.value)} placeholder="Код маніпуляції" />
                <input className="w-full bg-[#0f1217] border border-[#262a30] text-gray-200 p-2 text-xs rounded outline-none focus:border-green-500" value={procNotes} onChange={(e) => setProcNotes(e.target.value)} placeholder="Нотатки" />
                <button type="submit" className="w-full py-2 bg-green-900/20 hover:bg-green-600 border border-green-900 text-green-500 hover:text-white transition-colors rounded-sm text-[10px] font-bold tracking-widest uppercase flex items-center justify-center gap-1">
                  <Plus className="w-3 h-3" /> ДОДАТИ
                </button>
              </form>
            </section>

            {/* Medications Form */}
            <section className="wolf-panel p-5 bg-[#1a1d24]/30">
              <h3 className="text-xs font-bold tracking-widest text-red-500 uppercase mb-4 flex items-center gap-2">
                <Pill className="w-3 h-3" /> МЕДИКАМЕНТИ (MEDS)
              </h3>
              <form onSubmit={submitMedication} className="space-y-2">
                <input className="w-full bg-[#0f1217] border border-[#262a30] text-gray-200 p-2 text-xs rounded outline-none focus:border-red-500" value={medCode} onChange={(e) => setMedCode(e.target.value)} placeholder="Препарат" />
                <div className="flex gap-2">
                  <input className="flex-1 bg-[#0f1217] border border-[#262a30] text-gray-200 p-2 text-xs rounded outline-none focus:border-red-500" value={medDose} onChange={(e) => setMedDose(e.target.value)} placeholder="Доза" />
                  <input className="w-16 bg-[#0f1217] border border-[#262a30] text-gray-200 p-2 text-xs rounded outline-none focus:border-red-500" value={medUnit} onChange={(e) => setMedUnit(e.target.value)} placeholder="од." />
                </div>
                <button type="submit" className="w-full py-2 bg-red-900/20 hover:bg-red-600 border border-red-900 text-red-500 hover:text-white transition-colors rounded-sm text-[10px] font-bold tracking-widest uppercase flex items-center justify-center gap-1">
                  <Plus className="w-3 h-3" /> ДОДАТИ
                </button>
              </form>
            </section>
          </div>

          {/* Historical Data Tables */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="wolf-panel p-4 flex flex-col h-[300px]">
              <h4 className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-3 border-b border-[#1a1d24] pb-2">Історія показників</h4>
              <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar pr-1">
                {details?.observations?.map((o) => (
                  <div key={o.id} className="flex justify-between border-b border-[#1a1d24]/50 py-1.5 text-xs">
                    <span className="text-gray-400 font-medium">{[
                      o.heart_rate != null ? 'HR' : null,
                      o.respiratory_rate != null ? 'RR' : null,
                      o.systolic_bp != null ? 'SYS' : null,
                      o.diastolic_bp != null ? 'DIA' : null,
                      o.spo2_percent != null ? 'SpO2' : null,
                      o.temperature_celsius != null ? 'TEMP' : null,
                    ].filter(Boolean).join(', ') || o.observation_type || '-'}</span>
                    <span className="text-white font-bold">{[
                      o.heart_rate != null ? `HR ${o.heart_rate}` : null,
                      o.respiratory_rate != null ? `RR ${o.respiratory_rate}` : null,
                      o.systolic_bp != null ? `SYS ${o.systolic_bp}` : null,
                      o.diastolic_bp != null ? `DIA ${o.diastolic_bp}` : null,
                      o.spo2_percent != null ? `SpO2 ${o.spo2_percent}` : null,
                      o.temperature_celsius != null ? `T ${o.temperature_celsius}` : null,
                    ].filter(Boolean).join(' • ') || o.value || '-'}</span>
                  </div>
                )) || <div className="text-gray-600 text-[10px]">Записи відсутні</div>}
              </div>
            </div>

            <div className="wolf-panel p-4 flex flex-col h-[300px]">
              <h4 className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-3 border-b border-[#1a1d24] pb-2">Виконані маніпуляції</h4>
              <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar pr-1">
                {details?.procedures?.map((p) => (
                  <div key={p.id} className="border-b border-[#1a1d24]/50 py-1.5 space-y-1">
                    <div className="text-xs text-white font-bold">{p.procedure_code}</div>
                    {p.notes && <div className="text-[10px] text-gray-500">{p.notes}</div>}
                  </div>
                )) || <div className="text-gray-600 text-[10px]">Записи відсутні</div>}
              </div>
            </div>

            <div className="wolf-panel p-4 flex flex-col h-[300px]">
              <h4 className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-3 border-b border-[#1a1d24] pb-2">Лист призначень</h4>
              <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar pr-1">
                {details?.sub_medications?.map((m) => (
                  <div key={m.id} className="flex justify-between items-center border-b border-[#1a1d24]/50 py-1.5 text-xs">
                    <span className="text-white font-bold">{m.medication_code}</span>
                    <span className="text-red-500 bg-red-900/20 px-1.5 py-0.5 rounded text-[9px] font-bold">
                      {m.dose_value} {m.dose_unit_code}
                    </span>
                  </div>
                )) || <div className="text-gray-600 text-[10px]">Записи відсутні</div>}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
