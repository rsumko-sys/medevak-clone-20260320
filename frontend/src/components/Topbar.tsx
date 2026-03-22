'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Settings, LogOut } from 'lucide-react'
import { logout } from '@/lib/api'

export default function Topbar() {
  const router = useRouter()
  const [confirmLogout, setConfirmLogout] = useState(false)

  const currentDate = new Date().toLocaleDateString('uk-UA', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })

  const handleLogout = () => {
    logout()
    router.replace('/login')
  }

  return (
    <header className="h-16 shrink-0 border-b border-borderContent bg-background flex items-center justify-between px-6 sticky top-0 z-10">
      <div>
        <h2 className="text-sm font-bold tracking-widest text-white uppercase">МЕДЕВАК СИСТЕМА</h2>
        <p className="hidden md:block text-xs text-gray-500 font-mono tracking-widest uppercase">{currentDate}</p>
      </div>

      <div className="flex items-center gap-3">
        <Link href="/settings" className="p-2 border border-borderContent bg-panel rounded-md text-gray-400 hover:text-white hover:bg-[#252a33] transition-colors outline-none focus:outline-none">
          <Settings className="w-4 h-4" />
        </Link>
        <div className="hidden md:flex px-3 py-1.5 border border-borderContent bg-panel rounded-md items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-xs tracking-widest text-gray-400 uppercase font-bold">ОНЛАЙН</span>
        </div>
        {confirmLogout ? (
          <div className="flex items-center gap-1">
            <button
              onClick={handleLogout}
              className="px-2 py-1 text-[10px] font-bold uppercase tracking-widest bg-red-900/40 border border-red-700 text-red-400 rounded-md transition-colors"
            >
              ВИЙТИ
            </button>
            <button
              onClick={() => setConfirmLogout(false)}
              className="px-2 py-1 text-[10px] font-bold uppercase tracking-widest border border-borderContent bg-panel text-gray-400 rounded-md transition-colors"
            >
              НІ
            </button>
          </div>
        ) : (
          <button
            onClick={() => setConfirmLogout(true)}
            className="p-2 border border-borderContent bg-panel rounded-md text-gray-400 hover:text-red-400 hover:bg-red-900/20 hover:border-red-900/50 transition-colors outline-none focus:outline-none"
            title="Вийти"
          >
            <LogOut className="w-4 h-4" />
          </button>
        )}
      </div>
    </header>
  )
}
