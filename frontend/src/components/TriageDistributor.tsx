'use client'

import React from 'react'

interface TriageCategoryProps {
  label: string
  count: number
  colorClass: string
  bgClass: string
  icon: string
}

function TriageRow({ label, count, colorClass, bgClass, icon }: TriageCategoryProps) {
  return (
    <div className="flex items-center gap-4 bg-[#1e232b] p-2 rounded-sm border border-[#262a30]">
      <div className={`${bgClass} ${colorClass} w-8 h-8 flex items-center justify-center font-bold text-xs rounded-sm`}>
        {icon}
      </div>
      <div className={`flex-1 text-sm font-medium ${colorClass} tracking-wider`}>
        {label}
      </div>
      <div className="text-sm font-bold w-6 text-right">{count}</div>
    </div>
  )
}

interface TriageDistributorProps {
  stats: {
    urgent: number
    wounded: number
    concussed: number
    kia: number
  }
}

export default function TriageDistributor({ stats }: TriageDistributorProps) {
  return (
    <div className="wolf-panel p-5">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-sm font-bold tracking-widest uppercase text-white">РОЗПОДІЛ ТРІАЖУ</h3>
        <div className="text-gray-500">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
        </div>
      </div>
      
      <div className="space-y-3">
        <TriageRow 
          label="ЕКСТРЕННО" 
          count={stats.urgent} 
          colorClass="text-red-400" 
          bgClass="bg-red-900" 
          icon="+" 
        />
        <TriageRow 
          label="ВІДСТРОЧЕНО" 
          count={stats.wounded} 
          colorClass="text-orange-400" 
          bgClass="bg-orange-900" 
          icon="300" 
        />
        <TriageRow 
          label="МІНІМАЛЬНО" 
          count={stats.concussed} 
          colorClass="text-gray-400" 
          bgClass="bg-gray-800" 
          icon="400" 
        />
        <TriageRow 
          label="ЗАГИБЛИЙ" 
          count={stats.kia} 
          colorClass="text-gray-400" 
          bgClass="bg-gray-800" 
          icon="200" 
        />
      </div>
    </div>
  )
}
