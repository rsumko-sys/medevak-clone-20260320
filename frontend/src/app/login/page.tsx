'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Shield, LogIn } from 'lucide-react'
import { login } from '@/lib/api'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email.trim(), password)
      const from = typeof window !== 'undefined'
        ? new URLSearchParams(window.location.search).get('from')
        : null
      const target = from && from !== '/login' ? from : '/dashboard'
      router.replace(target)
    } catch (err: any) {
      setError(err?.message || 'Помилка авторизації')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="flex flex-col items-center mb-8 gap-3">
          <Shield className="w-10 h-10 text-[#4a9eff]" />
          <div className="text-center">
            <h1 className="text-white font-bold tracking-[0.2em] text-lg uppercase">MEDEVAK</h1>
            <p className="text-gray-500 text-[10px] tracking-[0.15em] uppercase mt-1">АЗОВ • МЕДИЧНИЙ ПІДРОЗДІЛ</p>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-400 text-[10px] uppercase tracking-[0.15em] mb-1">
              Електронна пошта
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="username"
              placeholder="medic@unit.ua"
              className="w-full bg-[#111827] border border-[#2d3748] rounded px-3 py-2.5 text-white text-sm focus:outline-none focus:border-[#4a9eff] placeholder-gray-600"
            />
          </div>

          <div>
            <label className="block text-gray-400 text-[10px] uppercase tracking-[0.15em] mb-1">
              Пароль
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              placeholder="••••••••"
              className="w-full bg-[#111827] border border-[#2d3748] rounded px-3 py-2.5 text-white text-sm focus:outline-none focus:border-[#4a9eff] placeholder-gray-600"
            />
          </div>

          {error && (
            <div className="bg-red-900/30 border border-red-700 rounded px-3 py-2 text-red-400 text-xs">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-[#4a9eff] hover:bg-[#3a8eef] disabled:bg-[#2a5a8f] disabled:cursor-not-allowed text-white font-bold uppercase tracking-[0.15em] text-xs py-3 rounded transition-colors"
          >
            <LogIn className="w-4 h-4" />
            {loading ? 'ВХІД...' : 'УВІЙТИ'}
          </button>
        </form>

        <p className="text-center text-gray-600 text-[10px] tracking-[0.1em] mt-6 uppercase">
          Захищений доступ • АЗОВ MEDEVAK
        </p>
      </div>
    </div>
  )
}
