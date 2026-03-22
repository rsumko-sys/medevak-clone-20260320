'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  LayoutDashboard, 
  Users, 
  Box, 
  Droplet, 
  PlaneTakeoff, 
  Folder,
  ShieldAlert,
  Download,
  UploadCloud,
  ClipboardList,
  Settings
} from 'lucide-react'

export default function Sidebar() {
  const pathname = usePathname()
  
  // Operational items (field-use priority)
  const operationalItems = [
    { name: 'Дашборд', path: '/command', icon: LayoutDashboard },
    { name: 'Пацієнти', path: '/cases', icon: Users },
    { name: 'Медзапаси', path: '/supplies', icon: Box },
    { name: 'Кров', path: '/blood', icon: Droplet },
    { name: 'Евакуація', path: '/evac', icon: PlaneTakeoff },
  ]

  // Administrative / support items
  const adminItems = [
    { name: 'Документи', path: '/documents', icon: Folder },
    { name: 'Протоколи', path: '/protocols', icon: ShieldAlert },
    { name: 'Експорт', path: '/exports', icon: Download },
    { name: 'Синхронізація', path: '/sync', icon: UploadCloud },
    { name: 'Аудит', path: '/audit', icon: ClipboardList },
    { name: 'Налаштування', path: '/settings', icon: Settings },
  ]

  return (
    <aside className="w-56 shrink-0 bg-sidebar border-r border-[#1a1d24] flex flex-col sticky top-0 h-screen overflow-y-auto scrollbar-hide">
      {/* Logo Area */}
      <div className="p-6 border-b border-[#1a1d24]">
        <h1 className="text-xl font-bold tracking-widest leading-tight">КОМАНДНИЙ ЦЕНТР</h1>
        <p className="text-xs text-gray-500 tracking-widest mt-1 uppercase">АЗОВ • МЕДИЧНИЙ ПІДРОЗДІЛ</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        <ul className="space-y-1 px-3">
          {operationalItems.map((item) => {
            const isActive = pathname === item.path || pathname?.startsWith(item.path + '/')
            const Icon = item.icon
            return (
              <li key={item.path}>
                <Link
                  href={item.path}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                    isActive
                      ? 'bg-[#1e232b] text-white font-medium'
                      : 'text-gray-400 hover:text-white hover:bg-[#1a1e24]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.name}
                  {isActive && (
                    <span className="ml-auto w-1.5 h-5 bg-red-500 rounded-full" />
                  )}
                </Link>
              </li>
            )
          })}

          {/* Separator: operational / admin */}
          <li aria-hidden="true" className="mx-1 my-2 border-t border-[#1a1d24]" />

          {adminItems.map((item) => {
            const isActive = pathname === item.path || pathname?.startsWith(item.path + '/')
            const Icon = item.icon
            return (
              <li key={item.path}>
                <Link
                  href={item.path}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                    isActive
                      ? 'bg-[#1e232b] text-white font-medium'
                      : 'text-gray-400 hover:text-white hover:bg-[#1a1e24]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.name}
                  {isActive && (
                    <span className="ml-auto w-1.5 h-5 bg-red-500 rounded-full" />
                  )}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Bottom Area */}
      <div className="p-4 border-t border-[#1a1d24] flex flex-col gap-3">
        <Link href="/battlefield" className="flex items-center gap-2 text-xs text-gray-400 hover:text-white transition-colors">
          <ShieldAlert className="w-4 h-4 text-red-500" />
          <span>Бойовий режим</span>
        </Link>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span>Система активна</span>
        </div>
      </div>
    </aside>
  )
}
