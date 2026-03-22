'use client'

import React from 'react'
import { usePathname } from 'next/navigation'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import { ToastProvider } from './Toast'
import { ErrorBoundary } from './ErrorBoundary'

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isNoSidebarPage = pathname === '/' || pathname === '/battlefield' || pathname === '/field'

  if (isNoSidebarPage) {
    return (
      <ErrorBoundary>
        <ToastProvider>
          <main className="flex-1 min-w-0">{children}</main>
        </ToastProvider>
      </ErrorBoundary>
    )
  }

  return (
    <ErrorBoundary>
      <ToastProvider>
        {/* Sidebar sticks to the left; content scrolls independently */}
        <div className="flex min-h-screen w-full overflow-hidden">
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0">
            <Topbar />
            <main className="flex-1 min-w-0 overflow-y-auto scrollbar-hide">
              {children}
            </main>
          </div>
        </div>
      </ToastProvider>
    </ErrorBoundary>
  )
}
