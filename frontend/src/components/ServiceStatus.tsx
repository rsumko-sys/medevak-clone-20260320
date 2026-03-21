'use client'

import { useEffect, useState } from 'react'

type ServiceState = 'checking' | 'ok' | 'degraded' | 'offline'

interface ServiceInfo {
  label: string
  state: ServiceState
  detail?: string
}

const DOT: Record<ServiceState, string> = {
  checking: 'bg-yellow-500 animate-pulse',
  ok:       'bg-green-500',
  degraded: 'bg-yellow-400 animate-pulse',
  offline:  'bg-red-600',
}

const TEXT: Record<ServiceState, string> = {
  checking: 'text-yellow-400',
  ok:       'text-green-400',
  degraded: 'text-yellow-400',
  offline:  'text-red-400',
}

const LABEL: Record<ServiceState, string> = {
  checking: 'ПЕРЕВІРКА',
  ok:       'АКТИВНИЙ',
  degraded: 'ДЕГРАДАЦІЯ',
  offline:  'НЕДОСТУПНИЙ',
}

function ServicePill({ svc }: { svc: ServiceInfo }) {
  return (
    <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-widest">
      <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${DOT[svc.state]}`} />
      <span className="text-gray-500">{svc.label}</span>
      <span className={TEXT[svc.state]}>{LABEL[svc.state]}</span>
    </div>
  )
}

export default function ServiceStatus() {
  const [services, setServices] = useState<ServiceInfo[]>([
    { label: 'API BACKEND', state: 'checking' },
    { label: 'БАЗА ДАНИХ',  state: 'checking' },
    { label: 'ФРОНТЕНД',    state: 'ok' },
  ])

  useEffect(() => {
    const apiBase =
      process.env.NEXT_PUBLIC_API_BASE ??
      (typeof window !== 'undefined' &&
      (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
        ? 'http://localhost:8000/api'
        : '/api')

    // Derive the backend root from the api base (strip /api suffix)
    const backendRoot = String(apiBase).replace(/\/api\/?$/, '')

    async function check() {
      let apiState: ServiceState = 'offline'
      let dbState: ServiceState  = 'offline'

      try {
        const healthRes = await fetch(`${backendRoot}/health`, {
          signal: AbortSignal.timeout(6000),
          cache: 'no-store',
        })
        if (healthRes.ok) {
          const data = await healthRes.json()
          apiState = data.status === 'ok' ? 'ok' : 'degraded'
        }
      } catch {
        apiState = 'offline'
      }

      try {
        const readyRes = await fetch(`${backendRoot}/ready`, {
          signal: AbortSignal.timeout(6000),
          cache: 'no-store',
        })
        dbState = readyRes.ok ? 'ok' : 'degraded'
      } catch {
        dbState = 'offline'
      }

      setServices([
        { label: 'API BACKEND', state: apiState },
        { label: 'БАЗА ДАНИХ',  state: dbState },
        { label: 'ФРОНТЕНД',    state: 'ok' },
      ])
    }

    check()
    const id = setInterval(check, 30_000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="mt-12 flex flex-wrap items-center justify-center gap-6 px-4">
      {services.map((svc) => (
        <ServicePill key={svc.label} svc={svc} />
      ))}
    </div>
  )
}
