'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowLeft, Package, Send, Clock, CheckCircle, AlertTriangle, Trash2 } from 'lucide-react'

type SupplyKey = 'tourniquet' | 'bandage' | 'iv' | 'morphine' | 'chest_seal' | 'nas'

const SUPPLY_LABELS: Record<SupplyKey, string> = {
  tourniquet: 'Джгут',
  bandage: 'Бинт',
  iv: 'ІВ',
  morphine: 'Морфін',
  chest_seal: 'Клапан',
  nas: 'НАТ',
}

const MAX = 10

type PosStatus = 'active' | 'silent' | 'unknown'

type Position = {
  id: string
  name: string
  coords: string
  personnel: number
  status: PosStatus
  supplies: Record<SupplyKey, number>
}

type DropStatus = 'pending' | 'accepted' | 'flying' | 'done'

type DropRequest = {
  id: string
  position: string
  coords: string
  items: string[]
  note: string
  status: DropStatus
  time: string
}

const DEFAULT_POSITIONS: Position[] = [
  { id: 'alpha',   name: 'АЛЬФА',  coords: '', personnel: 4, status: 'active',  supplies: { tourniquet: 8, bandage: 6, iv: 4, morphine: 2, chest_seal: 5, nas: 3 } },
  { id: 'bravo',   name: 'БРАВО',  coords: '', personnel: 3, status: 'active',  supplies: { tourniquet: 3, bandage: 2, iv: 1, morphine: 0, chest_seal: 2, nas: 1 } },
  { id: 'charlie', name: 'ЧАРЛІ',  coords: '', personnel: 5, status: 'active',  supplies: { tourniquet: 10, bandage: 9, iv: 6, morphine: 4, chest_seal: 7, nas: 5 } },
  { id: 'delta',   name: 'ДЕЛЬТА', coords: '', personnel: 2, status: 'silent',  supplies: { tourniquet: 1, bandage: 0, iv: 0, morphine: 0, chest_seal: 0, nas: 0 } },
]

const DROP_STATUS_CONFIG: Record<DropStatus, { label: string; dot: string; text: string }> = {
  pending:  { label: 'ПРИЙНЯТО', dot: 'bg-yellow-500',  text: 'text-yellow-400' },
  accepted: { label: 'В РОБОТІ', dot: 'bg-blue-500',    text: 'text-blue-400' },
  flying:   { label: 'ЛЕТИТЬ',   dot: 'bg-orange-500',  text: 'text-orange-400' },
  done:     { label: 'ВИКОНАНО', dot: 'bg-green-500',   text: 'text-green-400' },
}

function supplyLevel(val: number): 'ok' | 'low' | 'critical' {
  if (val / MAX > 0.6) return 'ok'
  if (val / MAX > 0.2) return 'low'
  return 'critical'
}

function posAlert(pos: Position): 'ok' | 'low' | 'critical' {
  const vals = Object.values(pos.supplies)
  const criticals = vals.filter(v => supplyLevel(v) === 'critical').length
  const lows = vals.filter(v => supplyLevel(v) === 'low').length
  if (criticals >= 2) return 'critical'
  if (criticals >= 1 || lows >= 3) return 'low'
  return 'ok'
}

const levelColor: Record<string, string> = {
  ok: 'bg-green-500', low: 'bg-yellow-500', critical: 'bg-red-500',
}
const levelText: Record<string, string> = {
  ok: 'text-green-400', low: 'text-yellow-400', critical: 'text-red-400',
}
const alertBorder: Record<string, string> = {
  ok: 'border-[#2b2b2b]', low: 'border-yellow-900/50', critical: 'border-red-900/60',
}

export default function FieldPage() {
  const [positions, setPositions] = useState<Position[]>(DEFAULT_POSITIONS)
  const [requests, setRequests] = useState<DropRequest[]>([])
  const [expandedPos, setExpandedPos] = useState<string | null>(null)

  // Drop request form
  const [reqPos,    setReqPos]    = useState('')
  const [reqCoords, setReqCoords] = useState('')
  const [reqItems,  setReqItems]  = useState<SupplyKey[]>([])
  const [reqNote,   setReqNote]   = useState('')

  useEffect(() => {
    const savedPos  = localStorage.getItem('field_positions')
    const savedReqs = localStorage.getItem('field_requests')
    if (savedPos)  setPositions(JSON.parse(savedPos))
    if (savedReqs) setRequests(JSON.parse(savedReqs))
  }, [])

  const savePositions = (pos: Position[]) => {
    setPositions(pos)
    localStorage.setItem('field_positions', JSON.stringify(pos))
  }
  const saveRequests = (reqs: DropRequest[]) => {
    setRequests(reqs)
    localStorage.setItem('field_requests', JSON.stringify(reqs))
  }

  const updateSupply = (posId: string, key: SupplyKey, val: number) => {
    savePositions(positions.map(p =>
      p.id === posId ? { ...p, supplies: { ...p.supplies, [key]: Math.max(0, Math.min(MAX, val)) } } : p
    ))
  }
  const updateCoords = (posId: string, coords: string) => {
    savePositions(positions.map(p => p.id === posId ? { ...p, coords } : p))
  }

  const submitRequest = () => {
    if (!reqPos || reqItems.length === 0) return
    const pos = positions.find(p => p.id === reqPos)
    const req: DropRequest = {
      id: Date.now().toString(),
      position: reqPos,
      coords: reqCoords || pos?.coords || '',
      items: reqItems,
      note: reqNote,
      status: 'pending',
      time: new Date().toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' }),
    }
    saveRequests([req, ...requests])
    setReqPos(''); setReqCoords(''); setReqItems([]); setReqNote('')
  }

  const cycleStatus = (id: string) => {
    const order: DropStatus[] = ['pending', 'accepted', 'flying', 'done']
    saveRequests(requests.map(r => {
      if (r.id !== id) return r
      const idx = order.indexOf(r.status)
      return { ...r, status: order[(idx + 1) % order.length] }
    }))
  }

  const deleteRequest = (id: string) => saveRequests(requests.filter(r => r.id !== id))

  const toggleItem = (key: SupplyKey) =>
    setReqItems(prev => prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key])

  return (
    <div className="min-h-screen bg-[#0c0e11] text-white">

      {/* ── HEADER ── */}
      <div className="border-b border-[#1e222a] px-6 py-4 flex items-center gap-4 sticky top-0 z-10 bg-[#0c0e11]">
        <Link href="/" className="p-2 rounded-md bg-[#1a1d24] border border-[#2a2f3a] text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <div className="text-[10px] text-orange-500 uppercase tracking-widest font-bold mb-0.5">ПОЛЬОВИЙ КОНТУР</div>
          <h1 className="text-xl font-black tracking-widest text-white uppercase">СКИДИ • ПОЗИЦІЇ • ЗАПАСИ</h1>
        </div>
        <div className="ml-auto flex items-center gap-2 text-[10px] text-gray-500 font-mono uppercase">
          <div className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
          {positions.filter(p => p.status === 'active').length} АКТИВНИХ
        </div>
      </div>

      <div className="p-6 grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* ── LEFT: Positions + Request history ── */}
        <div className="xl:col-span-2 space-y-6">

          {/* Position cards grid */}
          <div>
            <h2 className="text-[10px] font-bold tracking-widest text-gray-500 uppercase mb-3">ПОЗИЦІЇ — НАЯВНІСТЬ МЕДЗАСОБІВ</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {positions.map(pos => {
                const alert = posAlert(pos)
                const isExpanded = expandedPos === pos.id
                return (
                  <div key={pos.id} className={`bg-[#131518] border ${alertBorder[alert]} rounded-md overflow-hidden`}>

                    {/* Card header — click to expand */}
                    <div
                      className="p-4 flex items-center justify-between cursor-pointer hover:bg-[#1a1d24] transition-colors"
                      onClick={() => setExpandedPos(isExpanded ? null : pos.id)}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-8 rounded-full ${levelColor[alert]}`} />
                        <div>
                          <div className="font-black tracking-wider">{pos.name}</div>
                          <div className="text-[10px] text-gray-500 font-mono">{pos.personnel} чол.</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {pos.status === 'silent' && (
                          <span className="text-[9px] text-red-500 font-mono tracking-widest bg-red-900/20 border border-red-900/40 px-2 py-0.5 rounded">МОВЧИТЬ</span>
                        )}
                        <span className={`text-[11px] font-bold tracking-widest ${levelText[alert]}`}>
                          {alert === 'ok' ? 'ОК' : alert === 'low' ? 'МАЛО' : 'КРИТИЧНО'}
                        </span>
                      </div>
                    </div>

                    {/* Supply bars */}
                    <div className="px-4 pb-4 grid grid-cols-3 gap-x-3 gap-y-2">
                      {(Object.keys(SUPPLY_LABELS) as SupplyKey[]).map(key => (
                        <div key={key}>
                          <div className="text-[9px] text-gray-600 font-mono uppercase mb-0.5">{SUPPLY_LABELS[key]}</div>
                          <div className="h-1.5 bg-[#1e222a] rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${levelColor[supplyLevel(pos.supplies[key])]}`}
                              style={{ width: `${(pos.supplies[key] / MAX) * 100}%` }}
                            />
                          </div>
                          <div className={`text-[9px] font-mono mt-0.5 ${levelText[supplyLevel(pos.supplies[key])]}`}>
                            {pos.supplies[key]}/{MAX}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Expanded: edit supplies + coords */}
                    {isExpanded && (
                      <div className="border-t border-[#1e222a] p-4 space-y-4">
                        <div>
                          <label className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">Координати (Grid/MGRS)</label>
                          <input
                            type="text"
                            value={pos.coords}
                            onChange={e => updateCoords(pos.id, e.target.value)}
                            placeholder="напр. 37UEB 12345 67890"
                            className="mt-1 w-full bg-[#0c0e11] border border-[#2a2f3a] rounded px-3 py-2 text-xs font-mono text-white placeholder-gray-600 focus:outline-none focus:border-orange-500"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          {(Object.keys(SUPPLY_LABELS) as SupplyKey[]).map(key => (
                            <div key={key} className="flex items-center justify-between">
                              <span className="text-[10px] text-gray-400">{SUPPLY_LABELS[key]}</span>
                              <div className="flex items-center gap-1.5">
                                <button
                                  onClick={() => updateSupply(pos.id, key, pos.supplies[key] - 1)}
                                  className="w-6 h-6 flex items-center justify-center bg-[#1e222a] rounded text-gray-400 hover:text-white text-sm leading-none"
                                >−</button>
                                <span className={`w-6 text-center text-xs font-mono font-bold ${levelText[supplyLevel(pos.supplies[key])]}`}>
                                  {pos.supplies[key]}
                                </span>
                                <button
                                  onClick={() => updateSupply(pos.id, key, pos.supplies[key] + 1)}
                                  className="w-6 h-6 flex items-center justify-center bg-[#1e222a] rounded text-gray-400 hover:text-white text-sm leading-none"
                                >+</button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Request history */}
          <div>
            <h2 className="text-[10px] font-bold tracking-widest text-gray-500 uppercase mb-3">
              ЗАПИТИ НА СКИД {requests.length > 0 && <span className="text-gray-700">({requests.length})</span>}
            </h2>
            {requests.length === 0 ? (
              <div className="bg-[#131518] border border-[#1e222a] rounded-md py-10 text-center text-xs text-gray-600 font-mono">
                Немає активних запитів
              </div>
            ) : (
              <div className="space-y-2">
                {requests.map(req => {
                  const pos = positions.find(p => p.id === req.position)
                  const st = DROP_STATUS_CONFIG[req.status]
                  return (
                    <div key={req.id} className="bg-[#131518] border border-[#1e222a] rounded-md px-4 py-3 flex items-center gap-3">
                      <div className={`w-1.5 h-9 rounded-full shrink-0 ${st.dot}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-xs font-bold tracking-wider">{pos?.name ?? req.position}</span>
                          {req.coords && <span className="text-[10px] text-gray-500 font-mono truncate">{req.coords}</span>}
                          <span className="text-[10px] text-gray-600 font-mono ml-auto shrink-0">{req.time}</span>
                        </div>
                        <div className="text-[10px] text-gray-400 truncate">
                          {req.items.map(k => SUPPLY_LABELS[k as SupplyKey] ?? k).join(' • ')}
                          {req.note && <span className="text-gray-600"> — {req.note}</span>}
                        </div>
                      </div>
                      <button
                        onClick={() => cycleStatus(req.id)}
                        className={`shrink-0 text-[10px] font-bold tracking-widest px-2 py-1 rounded border border-[#2a2f3a] hover:border-orange-500/50 transition-colors ${st.text}`}
                        title="Натисніть, щоб змінити статус"
                      >
                        {st.label}
                      </button>
                      <button onClick={() => deleteRequest(req.id)} className="shrink-0 text-gray-600 hover:text-red-400 transition-colors">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* ── RIGHT: Drop request form ── */}
        <div className="space-y-4">
          <div className="bg-[#131518] border border-[#1e222a] rounded-md p-5 space-y-4">
            <div className="flex items-center gap-2 mb-1">
              <Send className="w-4 h-4 text-orange-500" />
              <h2 className="text-xs font-bold tracking-widest text-white uppercase">ЗАПИТ НА СКИД ДРОНОМ</h2>
            </div>

            <div>
              <label className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">Позиція</label>
              <select
                value={reqPos}
                onChange={e => {
                  setReqPos(e.target.value)
                  const p = positions.find(pos => pos.id === e.target.value)
                  if (p?.coords) setReqCoords(p.coords)
                }}
                className="mt-1 w-full bg-[#0c0e11] border border-[#2a2f3a] rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-orange-500"
              >
                <option value="">— оберіть позицію —</option>
                {positions.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">Координати скиду</label>
              <input
                type="text"
                value={reqCoords}
                onChange={e => setReqCoords(e.target.value)}
                placeholder="Grid / MGRS / опис точки"
                className="mt-1 w-full bg-[#0c0e11] border border-[#2a2f3a] rounded px-3 py-2 text-xs font-mono text-white placeholder-gray-600 focus:outline-none focus:border-orange-500"
              />
            </div>

            <div>
              <label className="text-[10px] text-gray-500 font-mono uppercase tracking-widest mb-2 block">Що потрібно</label>
              <div className="grid grid-cols-2 gap-2">
                {(Object.keys(SUPPLY_LABELS) as SupplyKey[]).map(key => (
                  <button
                    key={key}
                    onClick={() => toggleItem(key)}
                    className={`px-2 py-2 rounded border text-[10px] font-mono transition-colors text-left ${
                      reqItems.includes(key)
                        ? 'border-orange-500 bg-orange-900/20 text-orange-400'
                        : 'border-[#2a2f3a] text-gray-500 hover:border-gray-500 hover:text-gray-300'
                    }`}
                  >
                    {reqItems.includes(key) ? '✓ ' : ''}{SUPPLY_LABELS[key]}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">Примітка</label>
              <input
                type="text"
                value={reqNote}
                onChange={e => setReqNote(e.target.value)}
                placeholder="кількість, пріоритет..."
                className="mt-1 w-full bg-[#0c0e11] border border-[#2a2f3a] rounded px-3 py-2 text-xs font-mono text-white placeholder-gray-600 focus:outline-none focus:border-orange-500"
              />
            </div>

            <button
              onClick={submitRequest}
              disabled={!reqPos || reqItems.length === 0}
              className="w-full py-3 bg-orange-900/40 hover:bg-orange-900/60 border border-orange-900/60 disabled:opacity-30 disabled:cursor-not-allowed text-white font-bold tracking-widest text-xs transition-colors rounded-md"
            >
              НАДІСЛАТИ ЗАПИТ →
            </button>
          </div>

          {/* Status legend */}
          <div className="bg-[#131518] border border-[#1e222a] rounded-md p-4 space-y-3">
            <div className="text-[10px] text-gray-600 font-mono uppercase tracking-widest">СТАТУСИ ЗАПИТУ</div>
            {(Object.keys(DROP_STATUS_CONFIG) as DropStatus[]).map(s => {
              const cfg = DROP_STATUS_CONFIG[s]
              const descs: Record<DropStatus, string> = {
                pending:  'запит отримано',
                accepted: 'дрон готується',
                flying:   'дрон у польоті',
                done:     'скид виконано',
              }
              return (
                <div key={s} className="flex items-center gap-2 text-[10px]">
                  <div className={`w-2 h-2 rounded-full shrink-0 ${cfg.dot}`} />
                  <span className={`font-bold ${cfg.text}`}>{cfg.label}</span>
                  <span className="text-gray-600">— {descs[s]}</span>
                </div>
              )
            })}
            <div className="mt-1 text-[9px] text-gray-700 font-mono border-t border-[#1e222a] pt-2">
              Натисніть статус → переключити на наступний
            </div>
          </div>

          {/* Supply legend */}
          <div className="bg-[#131518] border border-[#1e222a] rounded-md p-4 space-y-2">
            <div className="text-[10px] text-gray-600 font-mono uppercase tracking-widest">РІВНІ ЗАПАСІВ</div>
            <div className="flex items-center gap-2 text-[10px]"><div className="w-2 h-2 rounded-full bg-green-500" /><span className="text-green-400 font-bold">&gt;60%</span><span className="text-gray-600">— достатньо</span></div>
            <div className="flex items-center gap-2 text-[10px]"><div className="w-2 h-2 rounded-full bg-yellow-500" /><span className="text-yellow-400 font-bold">20–60%</span><span className="text-gray-600">— мало</span></div>
            <div className="flex items-center gap-2 text-[10px]"><div className="w-2 h-2 rounded-full bg-red-500" /><span className="text-red-400 font-bold">&lt;20%</span><span className="text-gray-600">— критично</span></div>
            <div className="mt-1 text-[9px] text-gray-700 font-mono border-t border-[#1e222a] pt-2">
              Натисніть карточку позиції щоб редагувати запаси
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
