'use client'

import React from 'react'
import { BodyRegion, InjuryRecord } from '@/lib/types'
import { BODY_ZONES, INJURY_ICONS } from '@/lib/constants'

interface BodyMapProps {
  activeView: 'front' | 'back'
  injuries: InjuryRecord[]
  selectedZone: BodyRegion | null
  onZoneClick: (zoneId: BodyRegion) => void
}

export default function BodyMap({ activeView, injuries, selectedZone, onZoneClick }: BodyMapProps) {
  type ViewSlot = BodyRegion | { front?: BodyRegion; back?: BodyRegion } | null

  const isInjuryVisibleOnView = (injury: InjuryRecord) => {
    // Drafts created before view tracking may miss the `view` field.
    if (!injury.view) return true
    return injury.view === activeView
  }

  const zoneById = new Map(BODY_ZONES.map((z) => [z.id, z]))

  const resolveSlot = (slot: ViewSlot): BodyRegion | null => {
    if (!slot) return null
    if (typeof slot === 'string') return slot
    return activeView === 'front' ? slot.front || null : slot.back || null
  }

  const renderZoneBlock = (zone: typeof BODY_ZONES[0]) => {
    const isSelected = selectedZone === zone.id
    const zoneInjuries = injuries.filter((i) => i.body_region === zone.id && isInjuryVisibleOnView(i))
    
    return (
      <button
        type="button"
        key={zone.id}
        onClick={() => onZoneClick(zone.id)}
        aria-label={`Зона ${zone.name}. Маркерів: ${zoneInjuries.length}`}
        className={`group relative h-[86px] w-full flex flex-col items-center justify-between p-2 border rounded-lg transition-all cursor-pointer
          ${isSelected 
            ? 'border-red-500 bg-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.2)]' 
            : zoneInjuries.length > 0 
              ? 'border-red-900/50 bg-red-950/20 shadow-inner' 
              : 'border-[#2b313d] bg-[#151922] hover:border-[#465068]'
          }`}
      >
        <div className="flex w-full justify-between items-start">
          <span className={`text-[9px] font-bold uppercase tracking-wider ${zoneInjuries.length > 0 ? 'text-red-400' : 'text-gray-500'}`}>
            {zone.name}
          </span>
          <div className="flex items-center gap-1">
            {zoneInjuries.length > 0 && (
              <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-red-900/40 text-red-300 border border-red-900/60">
                {zoneInjuries.length}
              </span>
            )}
            <div className={`w-6 h-6 rounded-full flex items-center justify-center border transition-colors
            ${isSelected ? 'bg-red-500 border-red-500 text-white' : 'bg-[#111317] border-[#3a3f4a] text-gray-400 group-hover:border-red-500 group-hover:text-red-500'}`}>
              <span className="text-sm font-bold">+</span>
            </div>
          </div>
        </div>

        {zone.protocol && (
          <div className="text-[8px] px-1.5 py-0.5 rounded border border-[#39414f] bg-[#12161d] text-gray-400 uppercase tracking-widest">
            {zone.protocol}
          </div>
        )}

        {/* Injury Markers */}
        <div className="flex flex-wrap gap-1 mt-2 justify-center">
          {zoneInjuries.map((inj) => (
            <div key={inj.id} className="bg-red-600 text-white text-[10px] font-black w-5 h-5 flex items-center justify-center rounded-sm shadow-sm ring-1 ring-red-400/50">
              {INJURY_ICONS[inj.injury_type]}
            </div>
          ))}
        </div>
      </button>
    )
  }

  const grid: ViewSlot[][] = [
    [null, null, null, 'HEAD', null, null, null],
    [null, null, null, { front: 'FACE' }, null, null, null],
    [null, null, null, 'NECK', null, null, null],
    ['L_SHOULDER', 'L_UPPER_ARM', { front: 'CHEST_LEFT_ANT', back: 'CHEST_LEFT_POST' }, { front: 'CHEST_CENTER_ANT', back: 'CHEST_CENTER_POST' }, { front: 'CHEST_RIGHT_ANT', back: 'CHEST_RIGHT_POST' }, 'R_UPPER_ARM', 'R_SHOULDER'],
    ['L_ELBOW', 'L_FOREARM', { front: 'ABDOMEN_LEFT', back: 'BACK_UPPER_LEFT' }, { front: 'ABDOMEN', back: 'SPINE' }, { front: 'ABDOMEN_RIGHT', back: 'BACK_UPPER_RIGHT' }, 'R_FOREARM', 'R_ELBOW'],
    ['L_WRIST', 'L_HAND', { front: 'PELVIS_LEFT', back: 'BACK_LOWER_LEFT' }, 'PELVIS', { front: 'PELVIS_RIGHT', back: 'BACK_LOWER_RIGHT' }, 'R_HAND', 'R_WRIST'],
    [null, null, 'L_THIGH', null, 'R_THIGH', null, null],
    [null, null, 'L_KNEE', null, 'R_KNEE', null, null],
    [null, null, 'L_LOWER_LEG', null, 'R_LOWER_LEG', null, null],
    [null, null, 'L_ANKLE', null, 'R_ANKLE', null, null],
    [null, null, 'L_FOOT', null, 'R_FOOT', null, null],
  ]

  return (
    <div className="w-full bg-[#0d0f12] p-4 md:p-6 rounded-2xl border border-[#262a30] shadow-2xl overflow-x-auto">
      <div className="grid grid-cols-7 gap-2 md:gap-3 max-w-6xl min-w-[760px] mx-auto">
        {grid.map((row, rowIdx) =>
          row.map((slot, colIdx) => {
            const zoneId = resolveSlot(slot)
            const zone = zoneId ? zoneById.get(zoneId) : undefined

            if (!zone || (zone.view !== 'both' && zone.view !== activeView)) {
              return <div key={`${rowIdx}-${colIdx}`} className="h-[86px]" />
            }

            return <div key={`${rowIdx}-${colIdx}`}>{renderZoneBlock(zone)}</div>
          })
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-[#262a30] flex justify-between items-center text-[10px] text-gray-500 font-mono uppercase tracking-widest">
        <span>Вигляд: {activeView === 'front' ? 'ФРОНТ' : 'ТИЛ'}</span>
        <span className="animate-pulse">M / A / R / C: маркування зони за протоколом</span>
      </div>
    </div>
  )
}
