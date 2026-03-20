'use client'

import React from 'react'
import { TriageCategory } from '@/lib/types'

interface MarchFormProps {
  data: any
  onChange: (data: any) => void
}

export default function MarchForm({ data, onChange }: MarchFormProps) {
  const updateField = (field: string, value: any) => {
    onChange({ ...data, [field]: value })
  }

  const toggleField = (field: string) => {
    updateField(field, !data[field])
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Massive Bleeding */}
      <section className="wolf-panel p-5 border border-[#262a30] bg-[#14171b] rounded-md">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-red-500 font-bold mb-4">M - МАСИВНА КРОВОТЕЧА</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button 
            onClick={() => toggleField('m_massive_bleeding')}
            className={`p-4 border rounded font-bold text-xs tracking-widest uppercase transition-all ${data.m_massive_bleeding ? 'bg-red-900/40 border-red-500 text-red-500' : 'bg-[#181b21] border-[#262a30] text-gray-500'}`}
          >
            КРОВОТЕЧА? {data.m_massive_bleeding ? 'ТАК' : 'НІ'}
          </button>
          <div className="flex items-center gap-3 bg-[#181b21] p-3 rounded border border-[#262a30]">
             <span className="text-[10px] uppercase font-bold text-gray-600">Турнікети:</span>
             <input 
              type="number" 
              value={data.m_tourniquets_applied || 0}
              onChange={e => updateField('m_tourniquets_applied', parseInt(e.target.value) || 0)}
              className="bg-transparent border-b border-gray-700 w-12 text-center text-white focus:outline-none"
             />
          </div>
        </div>
      </section>

      {/* Airway */}
      <section className="wolf-panel p-5 border border-[#262a30] bg-[#14171b] rounded-md">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-blue-400 font-bold mb-4">A - ДИХАЛЬНІ ШЛЯХИ</h2>
        <div className="space-y-4">
          <div className="flex gap-2">
            {['INTACT', 'NPA', 'SGA', 'CRIC'].map(opt => (
              <button 
                key={opt}
                onClick={() => updateField('a_airway_intervention', opt)}
                className={`flex-1 py-3 border rounded text-[10px] font-bold tracking-widest uppercase transition-all ${data.a_airway_intervention === opt ? 'bg-blue-900/30 border-blue-500 text-blue-400' : 'bg-[#181b21] border-[#262a30] text-gray-500'}`}
              >
                {opt}
              </button>
            ))}
          </div>
          <button 
            onClick={() => toggleField('a_airway_open')}
            className={`w-full p-4 border rounded font-bold text-xs tracking-widest uppercase transition-all ${data.a_airway_open ? 'bg-blue-900/30 border-blue-500 text-blue-400' : 'bg-[#181b21] border-[#262a30] text-gray-500'}`}
          >
            ПРОХІДНІСТЬ: {data.a_airway_open ? 'НОРМА' : 'ПОРУШЕНО'}
          </button>
        </div>
      </section>

      {/* Respiration */}
      <section className="wolf-panel p-5 border border-[#262a30] bg-[#14171b] rounded-md">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-cyan-400 font-bold mb-4">R - ДИХАННЯ</h2>
        <div className="grid grid-cols-2 gap-2">
           {[
             {id: 'r_chest_seal_applied', l: 'Оклюз. наклейка'},
             {id: 'r_needle_d_performed', l: 'Декомпресія'},
             {id: 'r_chest_tube', l: 'Дренаж'}
           ].map(item => (
             <button 
                key={item.id}
                onClick={() => toggleField(item.id)}
                className={`p-3 border rounded text-[9px] font-bold tracking-widest uppercase transition-all ${data[item.id] ? 'bg-cyan-900/30 border-cyan-500 text-cyan-400' : 'bg-[#181b21] border-[#262a30] text-gray-500'}`}
             >
               {item.l}
             </button>
           ))}
        </div>
      </section>

      {/* Circulation */}
      <section className="wolf-panel p-5 border border-[#262a30] bg-[#14171b] rounded-md">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-orange-400 font-bold mb-4">C - КРОВООБІГ</h2>
        <div className="space-y-4">
           <div className="flex gap-2">
            {['Відсутній', 'Слабкий', 'Радіальний'].map(p => (
               <button 
                key={p}
                onClick={() => updateField('c_radial_pulse', p)}
                className={`flex-1 py-3 border rounded text-[10px] font-bold tracking-widest uppercase transition-all ${data.c_radial_pulse === p ? 'bg-orange-900/30 border-orange-500 text-orange-400' : 'bg-[#181b21] border-[#262a30] text-gray-500'}`}
               >
                 {p}
               </button>
             ))}
           </div>
           <div className="flex gap-2">
              <button 
                onClick={() => toggleField('c_iv_access')}
                className={`flex-1 p-3 border rounded text-[10px] font-bold tracking-widest uppercase transition-all ${data.c_iv_access ? 'bg-orange-900/30 border-orange-500 text-orange-400' : 'bg-[#181b21] border-[#262a30] text-gray-500'}`}
              >
                ВЕНОЗНИЙ ДОСТУП
              </button>
              <button 
                onClick={() => toggleField('c_pelvic_binder')}
                className={`flex-1 p-3 border rounded text-[10px] font-bold tracking-widest uppercase transition-all ${data.c_pelvic_binder ? 'bg-orange-900/30 border-orange-500 text-orange-400' : 'bg-[#181b21] border-[#262a30] text-gray-500'}`}
              >
                ТАЗОВИЙ БАНДАЖ
              </button>
           </div>
        </div>
      </section>

      {/* Hypothermia */}
      <section className="wolf-panel p-5 border border-[#262a30] bg-[#14171b] rounded-md">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-yellow-500 font-bold mb-4">H - ГІПОТЕРМІЯ / ГОЛОВА</h2>
        <div className="flex gap-2">
          <button 
            onClick={() => toggleField('h_hypothermia_prevented')}
            className={`flex-1 p-4 border rounded font-bold text-[10px] tracking-widest uppercase transition-all ${data.h_hypothermia_prevented ? 'bg-yellow-900/30 border-yellow-500 text-yellow-400' : 'bg-[#181b21] border-[#262a30] text-gray-500'}`}
          >
            ТЕРМОКОВДРА
          </button>
          <button 
            onClick={() => toggleField('h_active_warming')}
            className={`flex-1 p-4 border rounded font-bold text-[10px] tracking-widest uppercase transition-all ${data.h_active_warming ? 'bg-yellow-900/30 border-yellow-500 text-yellow-400' : 'bg-[#181b21] border-[#262a30] text-gray-500'}`}
          >
            АКТИВНЕ ЗІГРІВАННЯ
          </button>
        </div>
      </section>
    </div>
  )
}
