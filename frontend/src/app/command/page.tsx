'use client'

import { useEffect, useState } from 'react'
import { Users, PlaneTakeoff, Box, CheckCircle } from 'lucide-react'
import { listCases } from '@/lib/api'
import { CaseItem } from '@/lib/types'
import StatCard from '@/components/StatCard'
import TriageDistributor from '@/components/TriageDistributor'
import PatientTable from '@/components/PatientTable'
import EvacuationStatus from '@/components/EvacuationStatus'

export default function CommandPage() {
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

  return (
    <div className="flex-1 p-6 space-y-6">
      
      {/* Page Title (Internal) */}
      <div className="mb-2">
        <h1 className="text-2xl font-black tracking-tighter text-white uppercase">Dashboard</h1>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
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
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TriageDistributor stats={stats.triage} />
        <EvacuationStatus />
      </div>

      {/* Recent Patients Table */}
      <PatientTable cases={recentCases} loading={loading} />

    </div>
  )
}
