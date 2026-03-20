'use client'

import { useEffect, useState } from 'react'
import { exportFhirUrl, exportPdfUrl, exportQrUrl, listCases } from '@/lib/api'
import { CaseItem } from '@/lib/types'
import { Download, FileJson, QrCode, ClipboardList, AlertCircle, RefreshCcw } from 'lucide-react'

export default function ExportsPage() {
  const [cases, setCases] = useState<CaseItem[]>([])
  const [selectedCase, setSelectedCase] = useState('')
  const [qrData, setQrData] = useState('')
  const [loading, setLoading] = useState(true)
  const [isQrLoading, setIsQrLoading] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    try {
      setLoading(true)
      const items = await listCases()
      setCases(items)
      if (!selectedCase && items[0]?.id) setSelectedCase(items[0].id)
    } catch {
      setError('Не вдалося завантажити кейси')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function fetchQr() {
    if (!selectedCase || isQrLoading) return
    try {
      setIsQrLoading(true)
      setError('')
      const res = await fetch(exportQrUrl(selectedCase))
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const json = await res.json()
      setQrData(json?.data?.data || '')
    } catch (err: any) {
      setError(err?.message?.includes('Failed to fetch')
        ? 'Немає зв\'язку з сервером'
        : `Помилка QR: ${err?.message || 'Unknown'}`)
    } finally {
      setIsQrLoading(false)
    }
  }

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      {/* Top Header Section */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-xl font-bold tracking-widest text-white uppercase mb-1">ЕКСПОРТ ДАНИХ</h1>
          <p className="text-xs text-gray-500 font-mono tracking-widest uppercase">PDF • FHIR JSON • NATO QR</p>
        </div>
        <div className="flex gap-3">
          <button onClick={load} className="p-2 border border-[#262a30] bg-[#1a1d24] rounded-md text-gray-400 hover:text-white transition-colors">
            <RefreshCcw className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Export Controls */}
        <div className="lg:col-span-2 space-y-4">
          <section className="wolf-panel p-6 shadow-xl">
            <h3 className="text-sm font-bold tracking-widest uppercase text-white mb-6 flex items-center gap-2">
              <ClipboardList className="w-4 h-4 text-blue-500" /> ВИБІР ОБ'ЄКТА ЕКСПОРТУ
            </h3>

            <div className="space-y-6">
              <div>
                <label className="block text-[10px] tracking-widest text-gray-500 uppercase font-bold mb-2 text-left">ПЕРСОНАЛЬНИЙ КЕЙС</label>
                <select
                  className="w-full bg-[#1a1d24] border border-[#262a30] text-gray-300 rounded-md p-3 text-sm focus:outline-none focus:border-blue-500 transition-all"
                  value={selectedCase}
                  onChange={(e) => setSelectedCase(e.target.value)}
                >
                  <option value="">Оберіть кейс для генерації документів</option>
                  {cases.map((c) => (
                    <option key={c.id} value={c.id}>
                      {(c.triage_code || '-') + ' • ' + (c.callsign || c.full_name || c.id.slice(0, 8))}
                    </option>
                  ))}
                </select>
              </div>

              {error && (
                <div className="p-3 bg-red-900/20 border border-red-900/50 rounded-md flex items-center gap-3 text-red-500 text-xs font-medium uppercase tracking-wider">
                  <AlertCircle className="w-4 h-4" /> {error}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <a
                  href={selectedCase ? exportPdfUrl(selectedCase) : '#'}
                  className={`flex flex-col items-center justify-center p-6 border rounded-lg transition-all gap-3 ${selectedCase ? 'bg-blue-900/10 border-blue-900/50 text-blue-400 hover:bg-blue-900/30' : 'bg-gray-900/20 border-gray-800 text-gray-600 cursor-not-allowed opacity-50'}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Download className="w-8 h-8" />
                  <span className="text-[10px] font-bold tracking-widest uppercase">ЗАВАНТАЖИТИ PDF</span>
                </a>

                <a
                  href={selectedCase ? exportFhirUrl(selectedCase) : '#'}
                  className={`flex flex-col items-center justify-center p-6 border rounded-lg transition-all gap-3 ${selectedCase ? 'bg-blue-900/10 border-blue-900/50 text-blue-400 hover:bg-blue-900/30' : 'bg-gray-900/20 border-gray-800 text-gray-600 cursor-not-allowed opacity-50'}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  <FileJson className="w-8 h-8" />
                  <span className="text-[10px] font-bold tracking-widest uppercase">FHIR JSON</span>
                </a>

                <button
                  id="btn-qr-generate"
                  onClick={fetchQr}
                  disabled={!selectedCase || isQrLoading}
                  className={`flex flex-col items-center justify-center p-6 border rounded-lg transition-all gap-3 ${selectedCase && !isQrLoading ? 'bg-green-900/10 border-green-900/50 text-green-500 hover:bg-green-900/30' : 'bg-gray-900/20 border-gray-800 text-gray-600 cursor-not-allowed opacity-50'}`}
                >
                  {isQrLoading
                    ? <div className="w-8 h-8 border-2 border-green-500/30 border-t-green-500 rounded-full animate-spin" />
                    : <QrCode className="w-8 h-8" />}
                  <span className="text-[10px] font-bold tracking-widest uppercase">{isQrLoading ? 'ГЕНЕРАЦІЯ...' : 'NATO QR PAYLOAD'}</span>
                </button>
              </div>
            </div>
          </section>

          <section className="wolf-panel p-6 shadow-xl">
            <h3 className="text-sm font-bold tracking-widest uppercase text-white mb-4 flex items-center gap-2">
              <QrCode className="w-4 h-4 text-green-500" /> QR-ДАНІ (RAW DATA)
            </h3>
            <div className="relative">
              <textarea
                className="w-full bg-[#0f1217] border border-[#262a30] text-green-500/80 font-mono text-xs p-4 rounded-md h-44 resize-none focus:outline-none"
                value={qrData}
                readOnly
                placeholder="Натисніть «NATO QR PAYLOAD» для генерації коду для тактичних пристроїв..."
              />
              <div className="absolute top-2 right-2 text-[8px] text-gray-600 font-bold uppercase tracking-widest">ENCRYPTED</div>
            </div>
          </section>
        </div>

        {/* Sidebar Status Info */}
        <div className="space-y-4">
          <div className="wolf-panel p-5 bg-[#1a1d24]/50 border-dashed">
            <h4 className="text-[10px] text-gray-500 uppercase tracking-[0.2em] font-bold mb-4">Стандарти Експорту</h4>
            <ul className="space-y-4">
              <li className="flex gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5" />
                <div className="text-xs text-gray-400 leading-relaxed">
                  <span className="text-white font-bold">PDF</span> відповідає формі DD 1380 TCCC Card.
                </div>
              </li>
              <li className="flex gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5" />
                <div className="text-xs text-gray-400 leading-relaxed">
                  <span className="text-white font-bold">FHIR R4</span> забезпечує сумісність з медичними системами НАТО.
                </div>
              </li>
              <li className="flex gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5" />
                <div className="text-xs text-gray-400 leading-relaxed">
                  <span className="text-white font-bold">QR Payload</span> стиснутий формат для передачі по рації або слабким каналам зв'язку.
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
