'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { listAudit } from '@/lib/api'
import { AuditEntry } from '@/lib/types'

export default function AuditPage() {
  const [items, setItems] = useState<AuditEntry[]>([])
  const [loading, setLoading] = useState(true)

  async function load() {
    try {
      setLoading(true)
      const data = await listAudit()
      setItems(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div className="flex-1 flex flex-col">
      <header className="border-b border-[#262a30] bg-[#101317]">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="wolf-h1">ЖУРНАЛ АУДИТУ</h1>
            <p className="wolf-title">створено / оновлено / видалено</p>
          </div>
          <div className="flex gap-2">
              <Link href="/command" className="wolf-btn">DASHBOARD</Link>
            <button onClick={load} className="wolf-btn">ОНОВИТИ</button>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto"><div className="max-w-7xl mx-auto px-4 py-6">
        <section className="wolf-panel p-4 overflow-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b border-[#2a2f37] text-gray-400">
                <th className="py-2">час</th>
                <th className="py-2">таблиця</th>
                <th className="py-2">дія</th>
                <th className="py-2">рядок</th>
                <th className="py-2">користувач</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="py-3">Завантаження...</td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={5} className="py-3 text-gray-500">Записів немає</td></tr>
              ) : (
                items.map((a) => (
                  <tr key={a.id} className="border-b border-[#232830]">
                    <td className="py-2">{a.created_at ? new Date(a.created_at).toLocaleString() : '-'}</td>
                    <td className="py-2">{a.table_name || '-'}</td>
                    <td className="py-2">{a.action || '-'}</td>
                    <td className="py-2">{a.row_id || '-'}</td>
                    <td className="py-2">{a.user_id || '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </section>
      </div>
      </main>
    </div>
  )
}
