'use client'

import { createContext, useCallback, useContext, useState, ReactNode } from 'react'
import { CheckCircle, XCircle, AlertCircle, X } from 'lucide-react'

export type ToastType = 'success' | 'error' | 'info'

interface ToastItem {
  id: string
  message: string
  type: ToastType
}

interface ToastContextValue {
  addToast: (message: string, type?: ToastType) => void
  success: (message: string) => void
  error: (message: string) => void
  info: (message: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const dismiss = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const addToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).slice(2)
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => dismiss(id), 4000)
  }, [dismiss])

  const ctx: ToastContextValue = {
    addToast,
    success: (m) => addToast(m, 'success'),
    error: (m) => addToast(m, 'error'),
    info: (m) => addToast(m, 'info'),
  }

  const ICONS = {
    success: <CheckCircle className="w-5 h-5 shrink-0 text-green-400" />,
    error:   <XCircle    className="w-5 h-5 shrink-0 text-red-400"   />,
    info:    <AlertCircle className="w-5 h-5 shrink-0 text-blue-400" />,
  }

  const BG = {
    success: 'bg-[#0e2016] border-green-800',
    error:   'bg-[#200e0e] border-red-800',
    info:    'bg-[#0e1420] border-blue-800',
  }

  return (
    <ToastContext.Provider value={ctx}>
      {children}
      {/* Toast Container */}
      <div className="fixed bottom-20 right-4 z-[9999] flex flex-col gap-3 pointer-events-none max-w-sm w-full">
        {toasts.map(t => (
          <div
            key={t.id}
            className={`flex items-start gap-3 p-4 rounded-lg border shadow-2xl pointer-events-auto animate-in slide-in-from-right-4 ${BG[t.type]}`}
          >
            {ICONS[t.type]}
            <span className="text-sm text-gray-200 font-medium flex-1 leading-snug">{t.message}</span>
            <button
              onClick={() => dismiss(t.id)}
              className="text-gray-500 hover:text-white transition-colors ml-1 shrink-0"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>')
  return ctx
}
