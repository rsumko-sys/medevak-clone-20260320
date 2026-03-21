'use client'

import { useEffect, useState, useRef } from 'react'
import { HardDriveUpload, Wifi, WifiOff, Server, Clock, Database, AlertCircle } from 'lucide-react'
import { getSyncStats, getSyncQueue } from '@/lib/api'

export default function SyncPage() {
  const [stats, setStats] = useState<any>(null)
  const [online, setOnline] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)

  const pending = stats?.pending || 0
  const acked = stats?.acked ?? stats?.synced ?? 0
  const deadLetter = stats?.dead_letter ?? stats?.failed ?? 0

  useEffect(() => {
    async function load() {
      try {
        const data = await getSyncStats()
        setStats(data)
      } catch (e) {
        setOnline(false)
      }
    }
    load()
    // Mock navigator.onLine hook
    const handleOnline = () => setOnline(true)
    const handleOffline = () => setOnline(false)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-xl font-bold tracking-widest text-white uppercase mb-1">ЦЕНТР СИНХРОНІЗАЦІЇ</h1>
          <p className="text-xs text-gray-500 font-mono tracking-widest uppercase">Локальна БД ↔ Хмарний Сервер</p>
        </div>
        <div className={`flex items-center gap-2 px-4 py-2 border rounded-md text-xs font-bold tracking-widest uppercase ${online ? 'border-green-900/50 bg-green-900/20 text-green-500' : 'border-red-900/50 bg-red-900/20 text-red-500'}`}>
          {online ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
          {online ? 'В МЕРЕЖІ' : 'ОФЛАЙН РЕЖИМ'}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="wolf-panel p-5 relative overflow-hidden group">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-3xl font-bold text-orange-400">{pending}</h2>
            <HardDriveUpload className="w-5 h-5 text-orange-900/50" />
          </div>
          <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">У ЧЕРЗІ НА ВІДПРАВКУ</p>
        </div>

        <div className="wolf-panel p-5 relative overflow-hidden group">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-3xl font-bold text-red-500">{deadLetter}</h2>
            <AlertCircle className="w-5 h-5 text-red-900/50" />
          </div>
          <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">НЕ ДОСТАВЛЕНО (DEAD LETTER)</p>
        </div>

        <div className="wolf-panel p-5 relative overflow-hidden group border-b-2 border-b-green-900/50">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-3xl font-bold text-green-500">{acked}</h2>
            <Database className="w-5 h-5 text-green-900/50" />
          </div>
          <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">ПІДТВЕРДЖЕНО (ACKED)</p>
        </div>
      </div>

      <div className="wolf-panel p-5">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-sm font-bold tracking-widest uppercase text-white flex items-center gap-2">
            <Server className="w-4 h-4 text-blue-500" /> РЕПЛІКАЦІЙНИЙ ЖУРНАЛ
          </h3>
          <button 
            onClick={async () => {
              if (syncing) {
                abortControllerRef.current?.abort()
                setSyncing(false)
                return
              }
              setSyncing(true)
              abortControllerRef.current = new AbortController()
              try {
                await getSyncQueue()
                const data = await getSyncStats()
                setStats(data)
              } catch (e) {
                if (e instanceof Error && e.name !== 'AbortError') {
                  console.error('Sync error:', e)
                }
              } finally {
                setSyncing(false)
              }
            }}
            disabled={false}
            className="text-[10px] tracking-widest uppercase font-bold text-blue-400 hover:text-white transition-colors disabled:opacity-50">
            {syncing ? 'СКАСУВАННЯ...' : 'ПРИМУСОВА РЕПЛІКАЦІЯ'}
          </button>
        </div>
        
        <div className="border border-dashed border-[#262a30] rounded-md p-10 flex flex-col items-center justify-center text-center bg-[#0f1217]">
          {online && pending === 0 ? (
             <>
               <Database className="w-12 h-12 text-green-900 mb-4" />
               <h4 className="text-lg font-bold text-gray-300">База даних повністю синхронізована</h4>
               <p className="text-sm text-gray-500 mt-2 max-w-sm">Усі локальні зміни успішно передано до центрального вузла CCRM.</p>
             </>
          ) : (
             <>
               <Clock className="w-12 h-12 text-orange-900 mb-4" />
               <h4 className="text-lg font-bold text-orange-400">Очікування підключення</h4>
               <p className="text-sm text-gray-500 mt-2 max-w-sm">Локальні записи поміщено у чергу. Вони будуть передані як тільки з'явиться стабільний зв'язок (Starlink/LTE).</p>
             </>
          )}
        </div>
      </div>
    </div>
  )
}

