'use client'

import React from 'react'
import { FlaskConical, AlertTriangle } from 'lucide-react'

interface BloodTypeData {
  count: number
  min: number
  status: string
}

interface BloodInventoryProps {
  inventory: Record<string, BloodTypeData>
}

export default function BloodInventory({ inventory }: BloodInventoryProps) {
  return (
    <div className="wolf-panel p-5">
      <h3 className="text-sm font-bold tracking-widest uppercase text-white mb-6 flex items-center gap-2">
        <FlaskConical className="w-4 h-4 text-red-500" />
        ПОТОЧНИЙ ЗАПАС КРОВІ
      </h3>
      
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {Object.entries(inventory).map(([type, data]) => {
          const progress = Math.min(100, (data.count / (data.min * 2)) * 100)
          const barStyle = { '--progress': `${progress}%` } as React.CSSProperties

          return (
            <div key={type} className={`p-4 rounded-xl border border-[#262a30] transition-all hover:shadow-lg ${data.status === 'critical' ? 'bg-red-900/20 border-red-900/50' : data.status === 'warning' ? 'bg-orange-900/20 border-orange-900/50' : 'bg-[#1a1d24] shadow-md'}`}>
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-bold text-gray-400 tracking-wider truncate">{type}</span>
                {data.status === 'critical' && <AlertTriangle className="w-4 h-4 text-red-500" />}
              </div>
              <div className="flex items-end gap-2">
                <span className={`text-2xl font-bold ${data.status === 'critical' ? 'text-red-500' : data.status === 'warning' ? 'text-orange-400' : 'text-white'}`}>
                  {data.count}
                </span>
                <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1">од.</span>
              </div>
              <div className="mt-2 w-full bg-[#0f1217] rounded-full h-1.5 overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-1000 ${data.status === 'critical' ? 'bg-red-500' : data.status === 'warning' ? 'bg-orange-500' : 'bg-green-500'}`}
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
