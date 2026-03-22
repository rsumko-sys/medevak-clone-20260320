'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { FlaskConical, Activity, Droplet, ArrowLeft } from 'lucide-react'
import { listCases } from '@/lib/api'
import { CaseItem } from '@/lib/types'
import BloodInventory from '@/components/BloodInventory'

export default function BloodPage() {
  const [cases, setCases] = useState<CaseItem[]>([])
  const [loading, setLoading] = useState(true)

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

  // Calculate generic mock inventory for visual fullness
  const inventory = {
    'O+ (O(I) Rh+)': { count: 14, min: 10, status: 'ok' },
    'O- (O(I) Rh-)': { count: 3, min: 8, status: 'critical' },
    'A+ (A(II) Rh+)': { count: 12, min: 8, status: 'ok' },
    'A- (A(II) Rh-)': { count: 2, min: 5, status: 'warning' },
    'B+ (B(III) Rh+)': { count: 8, min: 5, status: 'ok' },
    'B- (B(III) Rh-)': { count: 1, min: 2, status: 'warning' },
    'AB+ (AB(IV) Rh+)': { count: 5, min: 2, status: 'ok' },
    'AB- (AB(IV) Rh-)': { count: 0, min: 1, status: 'critical' },
    'Whole Blood LTOWB': { count: 4, min: 10, status: 'critical' },
  }

  // Patients who need blood mapping (Mock logic: ANY IMMEDIATE case or actively bleeding case, here mapped generically to IMMEDIATE)
  const patientsNeedingBlood = cases.filter(c => c.triage_code === 'IMMEDIATE' && ['ACTIVE', 'STABILIZING'].includes(c.case_status))

  return (
    <div className="flex-1 p-6 space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <Link href="/command" className="p-2 rounded-md bg-[#1a1d24] border border-[#2a2f3a] text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold tracking-widest text-white uppercase">КРОВ</h1>
          <p className="text-xs text-gray-500 font-mono tracking-widest uppercase">Інвентаризація запасів крові</p>
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Inventory Column */}
        <div className="lg:col-span-2">
          <BloodInventory inventory={inventory} />
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
