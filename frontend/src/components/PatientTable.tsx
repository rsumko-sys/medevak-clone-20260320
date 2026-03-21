'use client'

import Link from 'next/link'
import { CaseItem } from '@/lib/types'

interface PatientTableProps {
  cases: CaseItem[]
  loading?: boolean
}

export default function PatientTable({ cases, loading }: PatientTableProps) {
  return (
    <div className="wolf-panel p-4 md:p-5 overflow-hidden">
      <div className="flex flex-wrap justify-between items-center gap-2 mb-4">
        <h3 className="text-xs md:text-sm font-bold tracking-widest uppercase text-white">ОСТАННІ ПАЦІЄНТИ</h3>
        <Link
          href="/cases"
          className="text-[10px] tracking-widest uppercase font-bold text-gray-400 hover:text-white transition-colors flex items-center gap-1"
        >
          ВСІ
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
        </Link>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[700px] text-left border-collapse">
          <thead>
            <tr className="border-b border-[#262a30] text-[10px] text-gray-500 uppercase tracking-widest">
              <th className="py-3 px-2 font-medium">ПОЗИВНИЙ</th>
              <th className="py-3 px-2 font-medium">СТАТЬ</th>
              <th className="py-3 px-2 font-medium">ТРІАЖ</th>
              <th className="py-3 px-2 font-medium">ТРАВМА</th>
              <th className="py-3 px-2 font-medium">ЧАС</th>
              <th className="py-3 px-2 font-medium">СТАТУС</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-sm text-gray-500">Завантаження...</td>
              </tr>
            ) : cases.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-sm text-gray-500">Пацієнтів не знайдено</td>
              </tr>
            ) : (
              cases.map((c) => (
                <tr key={c.id} className="border-b border-[#262a30]/50 hover:bg-[#1a1d24] transition-colors text-sm">
                  <td className="py-3 px-2 font-bold text-white">
                    <Link href={`/cases?id=${c.id}`} className="hover:text-red-500 transition-colors">
                      {c.callsign || c.full_name || '-'}
                    </Link>
                  </td>
                  <td className="py-3 px-2 text-gray-400">{c.sex || '-'}</td>
                  <td className="py-3 px-2">
                    {c.triage_code ? (
                      <span className={`inline-block px-2 text-xs font-bold rounded-sm ${c.triage_code === 'IMMEDIATE' ? 'bg-red-900 text-red-400' : 'bg-orange-900 text-orange-400'}`}>
                        {c.triage_code}
                      </span>
                    ) : '-'}
                  </td>
                  <td className="py-3 px-2 text-gray-400">{c.mechanism_of_injury || '-'}</td>
                  <td className="py-3 px-2 text-gray-400 truncate max-w-[120px]">
                    {c.injury_datetime ? new Date(c.injury_datetime).toLocaleTimeString() : '-'}
                  </td>
                  <td className="py-3 px-2 text-gray-400">{c.case_status || 'ACTIVE'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
