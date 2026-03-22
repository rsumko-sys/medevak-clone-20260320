import Link from 'next/link'
import { Zap, Monitor, Mic, Map, Grid, Shield, Users, Box, Droplet, RefreshCw, Package, MapPin, Send, CheckCircle } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-[calc(100vh-2rem)] flex flex-col items-center justify-center p-4">
      
      {/* Header */}
      <div className="text-center mb-16 space-y-2">
        <p className="wolf-title text-gray-500 tracking-[0.3em]">АЗОВ</p>
        <h1 className="text-3xl md:text-5xl font-bold tracking-widest text-white">МЕДИЧНА СЛУЖБА</h1>
        <p className="wolf-title text-gray-400 tracking-[0.3em]">CCRM</p>
      </div>

      {/* Main Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl w-full">
        
        {/* Field Dashboard Card */}
        <div className="bg-[#181a1f] border border-[#2b2b2b] rounded-md overflow-hidden flex flex-col relative group">
          <div className="absolute top-0 right-0 w-16 h-16 bg-red-900/20 transform translate-x-8 -translate-y-8 rotate-45 border-l border-b border-red-500/30" />
          
          <div className="p-8 flex-1">
            <div className="flex items-center gap-4 mb-8">
              <div className="bg-red-900/40 p-3 rounded-sm text-red-500 border border-red-900/50">
                <Zap className="w-6 h-6" />
              </div>
              <div>
                <div className="text-[10px] text-red-500 uppercase tracking-widest font-bold mb-1">ПОЛЬОВИЙ РЕЖИМ</div>
                <h2 className="text-2xl font-bold tracking-widest text-white leading-tight">БОЙОВИЙ<br/>ДАШБОРД</h2>
              </div>
            </div>

            <ul className="space-y-4 mb-10">
              <li className="flex items-center gap-3 text-sm text-gray-400 font-medium">
                <Mic className="w-4 h-4 text-gray-500" /> ГОЛОСОВЕ ВВЕДЕННЯ (WHISPER AI)
              </li>
              <li className="flex items-center gap-3 text-sm text-gray-400 font-medium">
                <Map className="w-4 h-4 text-gray-500" /> СХЕМА ПОРАНЕНЬ — КАРТА ТІЛА
              </li>
              <li className="flex items-center gap-3 text-sm text-gray-400 font-medium">
                <Grid className="w-4 h-4 text-gray-500" /> ВЕЛИКІ КНОПКИ — РОБОТА В РУКАВИЦЯХ
              </li>
              <li className="flex items-center gap-3 text-sm text-gray-400 font-medium">
                <Shield className="w-4 h-4 text-gray-500" /> ТРІАЖ +, !, 200, 300, 400
              </li>
            </ul>

            <Link href="/battlefield" className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-red-900/30 hover:bg-red-900/50 border border-red-900/50 text-white font-bold tracking-widest text-sm transition-colors w-48">
              ВІДКРИТИ →
            </Link>
          </div>
        </div>

        {/* Command Center Card */}
        <div className="bg-[#181a1f] border border-[#2b2b2b] rounded-md overflow-hidden flex flex-col relative group">
          <div className="absolute top-0 right-0 w-16 h-16 bg-gray-800/20 transform translate-x-8 -translate-y-8 rotate-45 border-l border-b border-gray-600/30" />
          
          <div className="p-8 flex-1">
            <div className="flex items-center gap-4 mb-8">
              <div className="bg-[#22252b] p-3 rounded-sm text-gray-400 border border-[#333740]">
                <Monitor className="w-6 h-6" />
              </div>
              <div>
                <div className="text-[10px] text-gray-400 uppercase tracking-widest font-bold mb-1">ШТАБНИЙ РЕЖИМ</div>
                <h2 className="text-2xl font-bold tracking-widest text-white leading-tight">КОМАНДНИЙ<br/>ЦЕНТР</h2>
              </div>
            </div>

            <ul className="space-y-4 mb-10">
              <li className="flex items-center gap-3 text-sm text-gray-400 font-medium">
                <Users className="w-4 h-4 text-gray-500" /> АРХІВ ТА АКТИВНІ ПАЦІЄНТИ
              </li>
              <li className="flex items-center gap-3 text-sm text-gray-400 font-medium">
                <Box className="w-4 h-4 text-gray-500" /> ОБЛІК МЕДИЧНИХ ЗАПАСІВ
              </li>
              <li className="flex items-center gap-3 text-sm text-gray-400 font-medium">
                <Droplet className="w-4 h-4 text-gray-500" /> ОБЛІК ЗАПАСІВ КРОВІ
              </li>
              <li className="flex items-center gap-3 text-sm text-gray-400 font-medium">
                <RefreshCw className="w-4 h-4 text-gray-500" /> СИНХРОНІЗАЦІЯ ТА АУДИТ
              </li>
            </ul>

            <Link href="/command" className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-[#22252b] hover:bg-[#2a2e35] border border-[#333740] text-gray-300 font-bold tracking-widest text-sm transition-colors w-48">
              ВІДКРИТИ →
            </Link>
          </div>
        </div>

        {/* Field Contour Card */}
        <div className="bg-[#181a1f] border border-[#2b2b2b] rounded-md overflow-hidden flex flex-col relative group">
          <div className="absolute top-0 right-0 w-16 h-16 bg-orange-900/20 transform translate-x-8 -translate-y-8 rotate-45 border-l border-b border-orange-500/30" />
          
          <div className="p-8 flex-1">
            <div className="flex items-center gap-4 mb-8">
              <div className="bg-orange-900/40 p-3 rounded-sm text-orange-500 border border-orange-900/50">
                <Package className="w-6 h-6" />
              </div>
              <div>
                <div className="text-[10px] text-orange-500 uppercase tracking-widest font-bold mb-1">ПОЛЬОВИЙ КОНТУР</div>
                <h2 className="text-2xl font-bold tracking-widest text-white leading-tight">СКИДИ<br/>ПОЗИЦІЇ</h2>
              </div>
            </div>

            <ul className="space-y-4 mb-10">
              <li className="flex items-center gap-3 text-sm text-gray-400 font-medium">
                <MapPin className="w-4 h-4 text-gray-500" /> ПОЗИЦІЇ: АЛЬФА, БРАВО, ЧАРЛІ...
              </li>
              <li className="flex items-center gap-3 text-sm text-gray-400 font-medium">
                <Package className="w-4 h-4 text-gray-500" /> НАЯВНІСТЬ МЕДЗАСОБІВ НА ПОЗИЦІЇ
              </li>
              <li className="flex items-center gap-3 text-sm text-gray-400 font-medium">
                <Send className="w-4 h-4 text-gray-500" /> ЗАПИТ НА СКИД ДРОНОМ + КООРДИНАТИ
              </li>
              <li className="flex items-center gap-3 text-sm text-gray-400 font-medium">
                <CheckCircle className="w-4 h-4 text-gray-500" /> СТАТУС: ПРИЙНЯТО / В РОБОТІ / ВИКОНАНО
              </li>
            </ul>

            <Link href="/field" className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-orange-900/30 hover:bg-orange-900/50 border border-orange-900/50 text-white font-bold tracking-widest text-sm transition-colors w-48">
              ВІДКРИТИ →
            </Link>
          </div>
        </div>

      </div>

      {/* Footer Status */}
      <div className="mt-16 flex items-center justify-center gap-6 text-[10px] text-gray-600 font-mono uppercase tracking-widest">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 bg-green-500" />
          СИСТЕМА АКТИВНА
        </div>
        <div>CCRM MVP 1.0</div>
        <div>БЕРЕЗЕНЬ 2026</div>
      </div>

    </div>
  )
}

