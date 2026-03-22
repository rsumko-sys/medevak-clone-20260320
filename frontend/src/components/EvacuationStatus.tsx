'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

export default function EvacuationStatus() {
  return (
    <div className="wolf-panel p-5 h-full flex flex-col">
      <div className="flex justify-between items-center mb-6 shrink-0">
        <h3 className="text-sm font-bold tracking-widest uppercase text-white">СТАТУС ЕВАКУАЦІЇ</h3>
        <Link href="/evac" className="text-gray-500 hover:text-white transition-colors" title="Відкрити евакуацію">
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
      <div className="flex-1 flex items-center justify-center text-gray-500 text-sm border border-dashed border-[#262a30] rounded-lg">
        Немає активних евакуацій
      </div>
    </div>
  )
}
