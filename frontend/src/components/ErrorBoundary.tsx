'use client'

import React, { ReactNode } from 'react'
import { AlertTriangle, RefreshCcw } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  message: string
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, message: '' }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error?.message || 'Unknown error' }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary]', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-screen bg-[#0b0d10] p-8 text-center">
          <div className="w-20 h-20 rounded-full bg-red-900/20 border border-red-800 flex items-center justify-center mb-6">
            <AlertTriangle className="w-10 h-10 text-red-500" />
          </div>
          <h1 className="text-xl font-bold text-white tracking-widest uppercase mb-2">Критична Помилка</h1>
          <p className="text-gray-400 text-sm font-mono mb-6 max-w-md leading-relaxed">{this.state.message}</p>
          <button
            onClick={() => { this.setState({ hasError: false, message: '' }); window.location.reload() }}
            className="flex items-center gap-2 px-6 py-3 bg-red-900 border border-red-700 text-white rounded-md font-bold tracking-wider uppercase text-sm hover:bg-red-800 transition-colors"
          >
            <RefreshCcw className="w-4 h-4" />
            Перезавантажити
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
