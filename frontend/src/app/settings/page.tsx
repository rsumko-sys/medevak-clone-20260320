'use client'

import { useEffect, useState } from 'react'
import { Save, Shield, Database, Bell, User } from 'lucide-react'
import { useToast } from '@/components/Toast'
import { getSecurityPolicySettings, type SecurityPolicySettings } from '@/lib/api'

export default function SettingsPage() {
  const toast = useToast()
  const [unitName, setUnitName] = useState('Вовки Да Вінчі • «УЛЬФ»')
  const [deviceId, setDeviceId] = useState('DEV-ALPHA-01')
  const [isSyncEnabled, setIsSyncEnabled] = useState(true)
  const [whisperApiKey, setWhisperApiKey] = useState('')
  const [syncAuthToken, setSyncAuthToken] = useState('')
  const [cachePassphrase, setCachePassphrase] = useState('')
  const [securityPolicy, setSecurityPolicy] = useState<SecurityPolicySettings | null>(null)

  useEffect(() => {
    if (typeof window === 'undefined') return
    setWhisperApiKey(window.sessionStorage.getItem('whisperApiKey') || '')
    setSyncAuthToken(window.sessionStorage.getItem('syncAuthToken') || '')
    setCachePassphrase(window.sessionStorage.getItem('cachePassphrase') || '')

    getSecurityPolicySettings()
      .then(setSecurityPolicy)
      .catch(() => {
        setSecurityPolicy(null)
      })
  }, [])

  const handleSave = () => {
    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem('whisperApiKey', whisperApiKey.trim())
      window.sessionStorage.setItem('syncAuthToken', syncAuthToken.trim())
      window.sessionStorage.setItem('cachePassphrase', cachePassphrase.trim())
    }
    toast.success('Налаштування збережено')
  }

  const handleChangePin = () => {
    toast.info('Зміна PIN буде доступна у захищеному режимі адміністратора')
  }

  const handleEmergencyWipe = () => {
    toast.error('Екстренне видалення заблоковано: потрібне підтвердження командування')
  }

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto">
      <header className="mb-8">
        <h1 className="wolf-h1">НАЛАШТУВАННЯ СИСТЕМИ</h1>
        <p className="wolf-title text-gray-500">конфігурація терміналу та безпеки</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-4xl">
        
        {/* Unit Settings */}
        <section className="wolf-panel p-6 space-y-4">
          <h2 className="text-sm font-bold tracking-widest text-white uppercase flex items-center gap-2 mb-4">
            <User className="w-4 h-4 text-red-500" /> ІДЕНТИФІКАЦІЯ ПІДРОЗДІЛУ
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-[10px] text-gray-500 uppercase font-bold mb-2">НАЗВА ПІДРОЗДІЛУ</label>
              <input 
                type="text" 
                value={unitName} 
                onChange={(e) => setUnitName(e.target.value)}
                className="wolf-input w-full"
              />
            </div>
            <div>
              <label className="block text-[10px] text-gray-500 uppercase font-bold mb-2">ID ТЕРМІНАЛУ</label>
              <input 
                type="text" 
                value={deviceId} 
                readOnly
                className="wolf-input w-full opacity-50 cursor-not-allowed"
              />
            </div>
          </div>
        </section>

        {/* Sync Settings */}
        <section className="wolf-panel p-6 space-y-4">
          <h2 className="text-sm font-bold tracking-widest text-white uppercase flex items-center gap-2 mb-4">
            <Database className="w-4 h-4 text-blue-500" /> СИНХРОНІЗАЦІЯ ДАНИХ
          </h2>
          
          <div className="flex items-center justify-between p-3 bg-[#1a1d24] rounded-md border border-[#262a30]">
            <div>
              <div className="text-xs text-gray-300 font-bold uppercase tracking-wider">АВТОМАТИЧНА СИНХРОНІЗАЦІЯ</div>
              <div className="text-[10px] text-gray-500 uppercase mt-1">Передача даних на сервер при появі зв'язку</div>
            </div>
            <button 
              onClick={() => setIsSyncEnabled(!isSyncEnabled)}
              className={`w-12 h-6 rounded-full relative transition-colors ${isSyncEnabled ? 'bg-green-600' : 'bg-gray-700'}`}
            >
              <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${isSyncEnabled ? 'left-7' : 'left-1'}`} />
            </button>
          </div>

          <div className="p-3 bg-blue-900/10 border border-blue-900/30 rounded-md">
            <p className="text-[10px] text-blue-400 leading-relaxed uppercase font-bold">
              Всі дані шифруються за стандартом AES-256 перед відправкою.
            </p>
          </div>

            <div className="space-y-3">
              <div>
                <label className="block text-[10px] text-gray-500 uppercase font-bold mb-2">WHISPER API КЛЮЧ (СЕСІЯ)</label>
                <input
                  type="password"
                  value={whisperApiKey}
                  onChange={(e) => setWhisperApiKey(e.target.value)}
                  className="wolf-input w-full"
                  placeholder="wk-..."
                />
              </div>
              <div>
                <label className="block text-[10px] text-gray-500 uppercase font-bold mb-2">ТОКЕН АВТЕНТИФІКАЦІЇ SYNC (СЕСІЯ)</label>
                <input
                  type="password"
                  value={syncAuthToken}
                  onChange={(e) => setSyncAuthToken(e.target.value)}
                  className="wolf-input w-full"
                  placeholder="Bearer ..."
                />
              </div>
              <div>
                <label className="block text-[10px] text-gray-500 uppercase font-bold mb-2">ПАРОЛЬ ФРАЗА КЕШУ (СЕСІЯ)</label>
                <input
                  type="password"
                  value={cachePassphrase}
                  onChange={(e) => setCachePassphrase(e.target.value)}
                  className="wolf-input w-full"
                  placeholder="Пароль фраза"
                />
              </div>
            </div>
        </section>

        {/* Security Settings */}
        <section className="wolf-panel p-6 space-y-4 lg:col-span-2">
          <h2 className="text-sm font-bold tracking-widest text-white uppercase flex items-center gap-2 mb-4">
            <Shield className="w-4 h-4 text-orange-500" /> БЕЗПЕКА ТА ДОСТУП
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3 bg-[#1a1d24] rounded-md border border-[#262a30]">
              <div className="text-[10px] text-gray-500 uppercase font-bold mb-2">МЕРЕЖЕВИЙ РЕЖИМ</div>
              <div className={`text-xs font-bold uppercase tracking-wider ${securityPolicy?.private_network_only ? 'text-green-500' : 'text-orange-400'}`}>
                {securityPolicy?.private_network_only ? 'ТІЛЬКИ ПРИВАТНА МЕРЕЖА (LAN/VPN)' : 'ВІДКРИТИЙ ДОСТУП'}
              </div>
            </div>
            <div className="p-3 bg-[#1a1d24] rounded-md border border-[#262a30]">
              <div className="text-[10px] text-gray-500 uppercase font-bold mb-2">GPS КООРДИНАТИ</div>
              <div className={`text-xs font-bold uppercase tracking-wider ${securityPolicy?.allow_gps ? 'text-orange-400' : 'text-green-500'}`}>
                {securityPolicy?.allow_gps ? 'УВІМКНЕНО' : 'ВИМКНЕНО'}
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button onClick={handleChangePin} className="wolf-btn text-left py-4 flex flex-col items-start h-auto">
              <span className="text-white">ЗМІНИТИ PIN-КОД</span>
              <span className="text-[10px] text-gray-500 font-normal uppercase mt-1">Для швидкого доступу до терміналу</span>
            </button>
            <button onClick={handleEmergencyWipe} className="wolf-btn text-left py-4 flex flex-col items-start h-auto border-red-900/50 text-red-400">
              <span className="font-bold">ЕКСТРЕННЕ ВИДАЛЕННЯ ДАНИХ</span>
              <span className="text-[10px] text-red-900 font-normal uppercase mt-1">Повне очищення локальної бази</span>
            </button>
          </div>
        </section>

      </div>

      <div className="sticky bottom-0 pt-6 pb-2 pb-safe-area">
        <button 
          onClick={handleSave}
          className="flex items-center gap-3 px-8 py-4 bg-red-900 hover:bg-red-800 border border-red-700 text-white font-bold tracking-widest text-xs uppercase transition-colors shadow-lg"
        >
          <Save className="w-4 h-4" /> ЗБЕРЕГТИ НАЛАШТУВАННЯ
        </button>
      </div>
    </div>
  )
}
