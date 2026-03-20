'use client'

import React from 'react'
import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  colorClass?: string
  borderColor?: string
}

export default function StatCard({ 
  title, 
  value, 
  icon: Icon, 
  colorClass = 'text-gray-300',
  borderColor 
}: StatCardProps) {
  return (
    <div className={`wolf-panel p-5 relative overflow-hidden group ${borderColor ? `border-b-2 ${borderColor}` : ''}`}>
      <div className="flex justify-between items-start mb-4">
        <h2 className={`text-3xl font-bold ${colorClass}`}>{value}</h2>
        <Icon className={`w-5 h-5 ${colorClass.replace('text-', 'text-opacity-50 text-')}`} />
      </div>
      <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">{title}</p>
    </div>
  )
}
