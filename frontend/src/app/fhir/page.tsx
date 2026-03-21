'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

interface FhirStatus {
  fhir_available: boolean
  supported_resources: string[]
  fhir_version: string
  export_formats: string[]
  error?: string
  installation_hint?: string
}

export default function FhirStatusPage() {
  const [status, setStatus] = useState<FhirStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function checkStatus() {
    try {
      setLoading(true)
      const apiBase = typeof window !== 'undefined' && window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : ''
      const res = await fetch(`${apiBase}/api/fhir/status`)
      if (!res.ok) throw new Error('Не вдалося отримати статус')
      const json = await res.json()
      setStatus(json.data)
      setError('')
    } catch (e) {
      setError('FHIR недоступний')
      setStatus({
        fhir_available: false,
        supported_resources: [],
        fhir_version: 'R4',
        export_formats: [],
        error: 'Connection failed'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    checkStatus()
  }, [])

  return (
    <div className="flex-1 flex flex-col">
      <header className="border-b border-[#262a30] bg-[#101317]">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="wolf-h1">FHIR ІНТЕГРАЦІЯ</h1>
            <p className="wolf-title">Fast Healthcare Interoperability Resources</p>
          </div>
          <div className="flex gap-2">
            <Link href="/" className="wolf-btn">ГОЛОВНА</Link>
            <button onClick={checkStatus} className="wolf-btn">ОНОВИТИ</button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-4">
        {loading && <div className="wolf-panel p-4">Перевірка статусу...</div>}
        
        {error && !loading && (
          <div className="wolf-panel p-4 text-red-400">
            {error}
            {status?.installation_hint && (
              <div className="mt-2 text-sm text-gray-400">{status.installation_hint}</div>
            )}
          </div>
        )}

        {status && !loading && (
          <>
            <section className="wolf-panel p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="wolf-title">Статус системи</div>
                <div className={`px-2 py-1 text-xs ${status.fhir_available ? 'bg-green-900 text-green-400' : 'bg-red-900 text-red-400'}`}>
                  {status.fhir_available ? 'ОПЕРАТИВНИЙ' : 'НЕДОСТУПНИЙ'}
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-gray-500">FHIR версія</div>
                  <div>{status.fhir_version}</div>
                </div>
                <div>
                  <div className="text-gray-500">Доступність</div>
                  <div>{status.fhir_available ? 'Так' : 'Ні'}</div>
                </div>
              </div>
            </section>

            <section className="wolf-panel p-4">
              <div className="wolf-title mb-3">Підтримувані ресурси</div>
              <div className="flex flex-wrap gap-2">
                {status.supported_resources.map((resource) => (
                  <span key={resource} className="px-2 py-1 bg-[#1a2333] border border-[#3b4350] text-xs">
                    {resource}
                  </span>
                ))}
              </div>
            </section>

            <section className="wolf-panel p-4">
              <div className="wolf-title mb-3">Формати експорту</div>
              <div className="flex flex-wrap gap-2">
                {status.export_formats.map((format) => (
                  <span key={format} className="px-2 py-1 bg-[#1a2333] border border-[#3b4350] text-xs">
                    {format}
                  </span>
                ))}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  )
}
