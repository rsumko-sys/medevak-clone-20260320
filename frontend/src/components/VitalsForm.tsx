'use client'

import React from 'react'
import { Activity, Clock } from 'lucide-react'

interface VitalsFormProps {
  vitals: any
  onVitalsChange: (vitals: any) => void
  onAddAction: (type: 'medication' | 'procedure', code: string) => void
}

export default function VitalsForm({ vitals, onVitalsChange, onAddAction }: VitalsFormProps) {
  const updateVital = (field: string, value: any) => {
    onVitalsChange({ ...vitals, [field]: value })
  }

  const commonMeds = ['Naloxone', 'TXA', 'Fentanyl', 'Ketamine', 'Morphine', 'Ertapenem']
  const commonProcs = ['Турнікет', 'Тиснуча пов\'язка', 'Шина', 'Кисень']

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Quick Vitals Grid */}
      <section className="wolf-panel p-5 border border-[#262a30] bg-[#14171b] rounded-md">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-gray-500 font-bold mb-4 flex items-center gap-2">
          <Activity className="w-3 h-3 text-red-500" /> ВІТАЛЬНІ ПОКАЗНИКИ
        </h2>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
          <div className="bg-[#181b21] p-4 rounded border border-[#262a30] min-h-[118px] flex flex-col justify-between">
            <label className="text-[8px] uppercase text-gray-600 block mb-1">Пульс</label>
            <input 
              type="number" 
              placeholder="--"
              value={vitals.heart_rate || ''}
              onChange={e => updateVital('heart_rate', e.target.value)}
              className="bg-transparent text-3xl font-bold text-white w-full focus:outline-none no-spinner"
            />
          </div>
          <div className="bg-[#181b21] p-4 rounded border border-[#262a30] min-h-[118px] flex flex-col justify-between">
            <label className="text-[8px] uppercase text-gray-600 block mb-1">Частота дихання</label>
            <input 
              type="number" 
              placeholder="--"
                value={vitals.respiratory_rate || ''}
                onChange={e => updateVital('respiratory_rate', e.target.value)}
              className="bg-transparent text-3xl font-bold text-white w-full focus:outline-none no-spinner"
            />
          </div>
          <div className="bg-[#181b21] p-4 rounded border border-[#262a30] min-h-[118px] flex flex-col justify-between">
            <label className="text-[8px] uppercase text-gray-600 block mb-1">Артеріальний тиск</label>
            <div className="flex items-end gap-3">
               <input 
                type="number" 
                placeholder="СИС"
                value={vitals.systolic_bp || ''}
                onChange={e => updateVital('systolic_bp', e.target.value)}
                className="bg-transparent text-4xl font-black text-white w-full min-w-0 focus:outline-none no-spinner"
               />
               <span className="text-gray-500 text-3xl font-black leading-none pb-1">/</span>
               <input 
                type="number" 
                placeholder="ДІА"
                value={vitals.diastolic_bp || ''}
                onChange={e => updateVital('diastolic_bp', e.target.value)}
                className="bg-transparent text-4xl font-black text-white w-full min-w-0 focus:outline-none no-spinner"
               />
            </div>
          </div>
          <div className="bg-[#181b21] p-4 rounded border border-[#262a30] min-h-[118px] flex flex-col justify-between">
            <label className="text-[8px] uppercase text-gray-600 block mb-1">Насичення SpO2 %</label>
            <input 
              type="number" 
              placeholder="--"
              value={vitals.spo2_percent || ''}
              onChange={e => updateVital('spo2_percent', e.target.value)}
              className="bg-transparent text-3xl font-bold text-white w-full focus:outline-none no-spinner"
            />
          </div>
            <div className="bg-[#181b21] p-4 rounded border border-[#262a30] min-h-[118px] flex flex-col justify-between">
              <label className="text-[8px] uppercase text-gray-600 block mb-1">Температура C</label>
              <input
                type="number"
                step="0.1"
                placeholder="--"
                value={vitals.temperature_celsius || ''}
                onChange={e => updateVital('temperature_celsius', e.target.value)}
                className="bg-transparent text-3xl font-bold text-white w-full focus:outline-none no-spinner"
              />
            </div>
        </div>
      </section>

      {/* Quick Actions (Meds & Procs) */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="wolf-panel p-5 border border-[#262a30] bg-[#14171b] rounded-md">
          <h2 className="text-[10px] uppercase tracking-[0.2em] text-gray-500 font-bold mb-4">ПРЕПАРАТИ</h2>
          <div className="grid grid-cols-2 gap-2">
            {commonMeds.map(med => (
              <button 
                key={med}
                onClick={() => onAddAction('medication', med)}
                className="py-3 px-2 bg-[#181b21] border border-[#262a30] rounded text-[10px] font-bold tracking-widest uppercase text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
              >
                {med}
              </button>
            ))}
          </div>
        </div>

        <div className="wolf-panel p-5 border border-[#262a30] bg-[#14171b] rounded-md">
          <h2 className="text-[10px] uppercase tracking-[0.2em] text-gray-500 font-bold mb-4">ПРОЦЕДУРИ</h2>
          <div className="grid grid-cols-2 gap-2">
            {commonProcs.map(proc => (
              <button 
                key={proc}
                onClick={() => onAddAction('procedure', proc)}
                className="py-3 px-2 bg-[#181b21] border border-[#262a30] rounded text-[10px] font-bold tracking-widest uppercase text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
              >
                {proc}
              </button>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
