'use client'

import React from 'react'
import Link from 'next/link'
import { Settings, ArrowLeft } from 'lucide-react'

export default function Topbar() {
  const currentDate = new Date().toLocaleDateString('uk-UA', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })

  return (
    <header className="h-16 shrink-0 border-b border-borderContent bg-background flex items-center justify-between px-6 sticky top-0 z-10">
      <div className="flex items-center gap-4">
        <Link href="/" className="p-2 rounded-md bg-[#1a1d24] border border-[#2a2f3a] text-gray-400 hover:text-white transition-colors" title="На головну">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h2 className="text-sm font-bold tracking-widest text-white uppercase">МЕДЕВАК СИСТЕМА</h2>
          <p className="text-[10px] text-gray-500 font-mono tracking-widest uppercase">{currentDate}</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Link href="/settings" className="p-2 border border-borderContent bg-panel rounded-md text-gray-400 hover:text-white transition-colors">
          <Settings className="w-4 h-4" />
        </Link>
        <div className="px-3 py-1.5 border border-borderContent bg-panel rounded-md flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-[10px] tracking-widest text-gray-400 uppercase font-bold">ОНЛАЙН</span>
        </div>
      </div>
    </header>
  )
}
