'use client'

import React from 'react'
import { FlaskConical, AlertTriangle, Plus, Minus } from 'lucide-react'

interface BloodTypeData {
  count: number
  min: number
  status: string
}

interface BloodInventoryProps {
  inventory: Record<string, BloodTypeData>
  onUpdate?: (type: string, delta: number) => void
}

export default function BloodInventory({ inventory, onUpdate }: BloodInventoryProps) {
  return (
    <div className="wolf-panel p-5">
      <h3 className="text-sm font-bold tracking-widest uppercase text-white mb-6 flex items-center gap-2">
        <FlaskConical className="w-4 h-4 text-red-500" />
        ПОТОЧНИЙ ЗАПАС КРОВІ
      </h3>
      
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {Object.entries(inventory).map(([type, data]) => {
          const progress = Math.min(100, (data.count / (data.min * 2)) * 100)
          const sc = data.status === 'critical' ? 'bg-red-900/20 border-red-900/50' : data.status === 'warning' ? 'bg-orange-900/20 border-orange-900/50' : 'bg-[#1a1d24] border-[#262a30] shadow-md'
          const nc = data.status === 'critical' ? 'text-red-500' : data.status === 'warning' ? 'text-orange-400' : 'text-white'
          const bc = data.status === 'critical' ? 'bg-red-500' : data.status === 'warning' ? 'bg-orange-500' : 'bg-green-500'

          return (
            <div key={type} className={`p-4 rounded-xl border transition-all hover:shadow-lg ${sc}`}>
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-bold text-gray-400 tracking-wider truncate pr-1">{type}</span>
                {data.status === 'critical' && <AlertTriangle className="w-4 h-4 text-red-500 shrink-0" />}
              </div>
              <div className="flex items-end gap-2 mb-2">
                <span className={`text-2xl font-bold ${nc}`}>{data.count}</span>
                <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1">од.</span>
              </div>
              <div className="w-full bg-[#0f1217] rounded-full h-1.5 overflow-hidden mb-3">
                <div className={`h-full rounded-full transition-all duration-500 ${bc}`} style={{ width: `${progress}%` }} />
              </div>
              {onUpdate && (
                <div className="flex items-center justify-between gap-1">
                  <button onClick={() => onUpdate(type, -1)}
                    className="flex-1 flex items-center justify-center py-1 rounded bg-[#0f1217] border border-[#262a30] text-gray-500 hover:text-red-400 hover:border-red-900/50 transition-colors"
                    title="Зменшити">
                    <Minus className="w-3 h-3" />
                  </button>
                  <span className="text-[9px] text-gray-600 font-mono">мін:{data.min}</span>
                  <button onClick={() => onUpdate(type, 1)}
                    className="flex-1 flex items-center justify-center py-1 rounded bg-[#0f1217] border border-[#262a30] text-gray-500 hover:text-green-400 hover:border-green-900/50 transition-colors"
                    title="Збільшити">
                    <Plus className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
