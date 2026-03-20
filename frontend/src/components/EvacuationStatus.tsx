'use client'

import React from 'react'

export default function EvacuationStatus() {
  return (
    <div className="wolf-panel p-5 h-full flex flex-col">
      <div className="flex justify-between items-center mb-6 shrink-0">
        <h3 className="text-sm font-bold tracking-widest uppercase text-white">СТАТУС ЕВАКУАЦІЇ</h3>
        <button
          onClick={() => alert('Детальний перегляд евакуацій відкривається у вкладці ЕВАК.')}
          className="text-gray-500 hover:text-white transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
        </button>
      </div>
      <div className="flex-1 flex items-center justify-center text-gray-500 text-sm border border-dashed border-[#262a30] rounded-lg">
        Немає активних евакуацій
      </div>
    </div>
  )
}
