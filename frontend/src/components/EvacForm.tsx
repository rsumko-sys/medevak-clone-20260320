'use client'

import React from 'react'
import { Plane, Truck, ClipboardList } from 'lucide-react'

interface EvacFormProps {
  data: any
  mist: string
  onChange: (data: any) => void
  onGenerateMist: () => void
}

export default function EvacForm({ data, mist, onChange, onGenerateMist }: EvacFormProps) {
  const updateField = (field: string, value: any) => {
    onChange({ ...data, [field]: value })
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Evacuation Priority */}
      <section className="wolf-panel p-5 border border-[#262a30] bg-[#14171b] rounded-md">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-gray-500 font-bold mb-4">ПРІОРИТЕТ ЕВАКУАЦІЇ</h2>
        <div className="grid grid-cols-3 gap-3">
          {[
            { id: 'URGENT', label: 'ТЕРМІНОВО', cls: 'bg-red-900/30 border-red-500 text-red-500' },
            { id: 'PRIORITY', label: 'ПРІОРИТЕТНО', cls: 'bg-orange-900/30 border-orange-500 text-orange-500' },
            { id: 'ROUTINE', label: 'ПЛАНОВО', cls: 'bg-green-900/30 border-green-500 text-green-500' }
          ].map(p => (
            <button 
              key={p.id}
              onClick={() => updateField('evacuation_priority', p.id)}
              className={`py-4 border rounded text-[10px] font-bold tracking-widest uppercase transition-all ${data.evacuation_priority === p.id ? p.cls : 'bg-[#181b21] border-[#262a30] text-gray-500'}`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </section>

      {/* Transport & Destination */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="wolf-panel p-5 border border-[#262a30] bg-[#14171b] rounded-md">
           <h2 className="text-[10px] uppercase tracking-[0.2em] text-gray-500 font-bold mb-4">ТРАНСПОРТ</h2>
           <div className="flex gap-4">
              <button 
                onClick={() => updateField('transport_type', 'GROUND')}
                className={`flex-1 p-4 border rounded flex flex-col items-center gap-2 transition-all ${data.transport_type === 'GROUND' ? 'bg-[#2a2f3a] border-gray-400 text-white' : 'bg-[#181b21] border-[#262a30] text-gray-600'}`}
              >
                <Truck className="w-6 h-6" />
                <span className="text-[10px] font-bold tracking-widest uppercase">НАЗЕМНИЙ</span>
              </button>
              <button 
                onClick={() => updateField('transport_type', 'AIR')}
                className={`flex-1 p-4 border rounded flex flex-col items-center gap-2 transition-all ${data.transport_type === 'AIR' ? 'bg-[#2a2f3a] border-gray-400 text-white' : 'bg-[#181b21] border-[#262a30] text-gray-600'}`}
              >
                <Plane className="w-6 h-6" />
                <span className="text-[10px] font-bold tracking-widest uppercase">ПОВІТРЯНИЙ</span>
              </button>
           </div>
        </section>

        <section className="wolf-panel p-5 border border-[#262a30] bg-[#14171b] rounded-md">
           <h2 className="text-[10px] uppercase tracking-[0.2em] text-gray-500 font-bold mb-4">ПУНКТ ПРИЗНАЧЕННЯ</h2>
           <input 
            type="text" 
            placeholder="НАЗВА ГОСПІТАЛЮ / СТАБПУНКTУ"
            value={data.destination || ''}
            onChange={e => updateField('destination', e.target.value)}
            className="w-full bg-[#181b21] border border-[#262a30] rounded p-4 text-white uppercase font-bold tracking-wider text-xs focus:outline-none focus:border-gray-500 transition-colors"
           />
        </section>
      </div>

      {/* MIST Summary */}
      <section className="wolf-panel p-5 border border-[#262a30] bg-[#14171b] rounded-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-[10px] uppercase tracking-[0.2em] text-gray-500 font-bold flex items-center gap-2">
            <ClipboardList className="w-3 h-3" /> MIST ЗВЕДЕННЯ (РАДІОПЕРЕДАЧА)
          </h2>
          <button 
            onClick={onGenerateMist}
            className="text-[9px] font-bold tracking-widest uppercase bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1 rounded transition-colors"
          >
            ОНОВИТИ MIST
          </button>
        </div>
        
        <div className="bg-black/40 border border-[#1c1f26] rounded p-4 font-mono text-xs text-green-500/80 leading-relaxed whitespace-pre-wrap min-h-[120px]">
          {mist || 'MIST буде згенеровано автоматично на основі введених даних...'}
        </div>
      </section>
    </div>
  )
}
