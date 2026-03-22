'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Activity, Droplet, ArrowLeft, RefreshCw } from 'lucide-react'
import { adjustBloodInventory, getBloodInventory, listCases } from '@/lib/api'
import { BloodInventoryItem, CaseItem } from '@/lib/types'
import BloodInventory from '@/components/BloodInventory'
import { useToast } from '@/components/Toast'

type BloodTypeData = { count: number; min: number; status: string }

const BLOOD_MINIMUMS: Record<string, number> = {
  'O+': 10,
  'O-': 8,
  'A+': 8,
  'A-': 5,
  'B+': 5,
  'B-': 2,
  'AB+': 2,
  'AB-': 1,
  LTOWB: 10,
}

function mapInventory(items: BloodInventoryItem[]): Record<string, BloodTypeData> {
  return items.reduce<Record<string, BloodTypeData>>((acc, item) => {
    const min = BLOOD_MINIMUMS[item.blood_type] ?? 1
    const status = item.quantity < min * 0.2 ? 'critical' : item.quantity < min ? 'warning' : 'ok'
    acc[item.blood_type] = {
      count: item.quantity,
      min,
      status,
    }
    return acc
  }, {})
}

export default function BloodPage() {
  const toast = useToast()
  const [cases, setCases] = useState<CaseItem[]>([])
  const [inventory, setInventory] = useState<Record<string, BloodTypeData>>({})
  const [mutatingType, setMutatingType] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function updateInventory(type: string, delta: number) {
    try {
      setMutatingType(type)
      const updated = await adjustBloodInventory(type, {
        delta,
        reason: delta > 0 ? 'restock' : 'manual_use',
      })
      setInventory(prev => mapInventory([
        ...Object.entries(prev)
          .filter(([bloodType]) => bloodType !== type)
          .map(([bloodType, data]) => ({ blood_type: bloodType, quantity: data.count })),
        updated,
      ]))
      toast.success(`Запас ${type} оновлено`)
    } catch (e) {
      console.error('Failed to update blood inventory:', e)
      toast.error(delta < 0 ? 'Не вдалося списати кров' : 'Не вдалося поповнити запас')
    } finally {
      setMutatingType(null)
    }
  }

  async function syncBlood() {
    await load()
    toast.success('Дані крові синхронізовано')
  }

  async function load() {
    try {
      setLoading(true)
      setError(null)
      const [caseItems, inventoryItems] = await Promise.all([listCases(), getBloodInventory()])
      setCases(caseItems)
      setInventory(mapInventory(inventoryItems))
    } catch (e) {
      console.error('Failed to load cases:', e)
      setError('Помилка завантаження blood inventory або даних пацієнтів')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Patients who need blood mapping
  const patientsNeedingBlood = cases.filter(c => c.triage_code === 'IMMEDIATE' && ['ACTIVE', 'STABILIZING'].includes(c.case_status))

  return (
    <div className="flex-1 p-6 space-y-6">
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-3">
          <Link href="/command" className="p-2 rounded-md bg-[#1a1d24] border border-[#2a2f3a] text-gray-400 hover:text-white hover:bg-[#252a33] transition-colors outline-none focus:outline-none">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-widest text-white uppercase">КРОВ</h1>
            <p className="text-xs text-gray-500 font-mono tracking-widest uppercase">Інвентаризація запасів крові</p>
          </div>
        </div>
        <button onClick={syncBlood} disabled={loading} className="flex items-center gap-2 text-xs font-bold tracking-widest text-gray-400 hover:text-white uppercase border border-[#262a30] px-3 py-1.5 rounded bg-[#1a1d24] transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
          <RefreshCw className="w-3 h-3" /> СИНХРОНІЗУВАТИ
        </button>
      </div>
      {error && (
        <div className="px-4 py-3 bg-red-900/20 border border-red-900/50 rounded-md text-red-400 text-xs font-bold uppercase tracking-widest flex items-center justify-between">
          <span>⚠ {error}</span>
          <button onClick={load} className="underline text-red-300 hover:text-white">Повторити</button>
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Inventory Column */}
        <div className="lg:col-span-2">
          <BloodInventory inventory={inventory} onUpdate={mutatingType ? undefined : updateInventory} />
        </div>

        {/* Patients Column */}
        <div className="space-y-4">
          <div className="wolf-panel p-5 h-full">
            <h3 className="text-sm font-bold tracking-widest uppercase text-white mb-6 flex items-center gap-2">
              <Activity className="w-4 h-4 text-red-500" />
              ПАЦІЄНТИ З КРОВОВТРАТОЮ
            </h3>

            <div className="space-y-3">
              {loading ? (
                <div className="text-center text-sm text-gray-500 py-4">Оновлення бази...</div>
              ) : patientsNeedingBlood.length === 0 ? (
                <div className="text-center text-sm text-gray-500 py-8 border border-dashed border-[#262a30] rounded bg-[#1a1d24]">
                  Активні масивні кровотечі не зафіксовано
                </div>
              ) : (
                patientsNeedingBlood.map(c => (
                  <div key={c.id} className="p-3 bg-[#1a1d24] border border-red-900/30 rounded flex items-center justify-between">
                    <div>
                      <div className="font-bold text-white text-sm">{c.callsign || c.case_number}</div>
                      <div className="text-xs text-gray-400 flex items-center gap-1 mt-1">
                        <Droplet className="w-3 h-3 text-red-500" /> 
                        {c.blood_type || 'Тип невідомий'}
                      </div>
                    </div>
                    <span className="bg-red-900/40 text-red-400 px-2 py-1 text-[10px] uppercase tracking-widest font-bold rounded">
                      МАК
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
