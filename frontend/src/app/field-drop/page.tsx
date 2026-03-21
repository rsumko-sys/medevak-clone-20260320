'use client'

import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  Copy,
  Loader2,
  MapPinned,
  MinusCircle,
  Package,
  PlusCircle,
  Radio,
  RefreshCw,
  Send,
  Wifi,
  WifiOff,
} from 'lucide-react'
import { useToast } from '@/components/Toast'
import {
  commitFieldDropRequest,
  createFieldDropPosition,
  createFieldDropRequest,
  getFieldDropRecommendation,
  listFieldDropLogs,
  listFieldDropPositions,
  listFieldDropRequests,
  updateFieldDropInventory,
} from '@/lib/api'
import {
  FieldDispatchLog,
  FieldInventorySnapshot,
  FieldPosition,
  FieldRecommendation,
  FieldRequest,
} from '@/lib/types'

// ─── Constants ────────────────────────────────────────────────────────────────

const TRACKED_ITEMS = [
  { key: 'hemostatic' as const, label: 'ГЕМОСТАТИК' },
  { key: 'bandage'    as const, label: 'БИНТ'       },
  { key: 'tourniquet' as const, label: 'ДЖГУТ'      },
]
type TrackedKey = 'hemostatic' | 'bandage' | 'tourniquet'

const URGENCY: Record<string, { label: string; row: string; dot: string }> = {
  critical: { label: 'КРИТИЧНО', row: 'text-red-300 bg-red-950 border-red-700',     dot: 'bg-red-400 animate-pulse' },
  high:     { label: 'ВИСОКИЙ',  row: 'text-orange-300 bg-orange-950 border-orange-700', dot: 'bg-orange-400' },
  medium:   { label: 'СЕРЕДНІЙ', row: 'text-amber-300 bg-amber-950 border-amber-700',    dot: 'bg-amber-400'  },
  low:      { label: 'НИЗЬКИЙ',  row: 'text-gray-300 bg-gray-800 border-gray-600',        dot: 'bg-gray-500'   },
}

const STORAGE_QUEUE_KEY = 'field-drop-sync-queue-v1'
const REQUEST_TERMINAL_STATUSES = new Set(['DISPATCHED', 'PARTIAL', 'COMPLETED', 'FAILED'])

type InventoryDeltaAction = {
  id: string
  type: 'inventory_delta'
  createdAt: number
  status: 'pending' | 'failed'
  positionId: string
  item: TrackedKey
  delta: number
}

type CommitRequestAction = {
  id: string
  type: 'commit_request'
  createdAt: number
  status: 'pending' | 'failed'
  requestId: string
}

type PendingAction = InventoryDeltaAction | CommitRequestAction

// ─── Helpers ──────────────────────────────────────────────────────────────────

function qtyClasses(qty: number) {
  if (qty < 5)  return { row: 'text-red-400 border-red-800 bg-red-950/40',     dot: 'bg-red-500' }
  if (qty < 10) return { row: 'text-amber-400 border-amber-800 bg-amber-950/40', dot: 'bg-amber-400' }
  return              { row: 'text-green-400 border-green-800 bg-green-950/30',  dot: 'bg-green-500' }
}

function fmtTime(v?: string | null) {
  if (!v) return '—'
  try { return new Date(v).toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' }) }
  catch { return v }
}

function createOpId(prefix: string) {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `${prefix}:${crypto.randomUUID()}`
  }
  return `${prefix}:${Date.now()}:${Math.random().toString(36).slice(2, 10)}`
}

function statusStyle(status?: string | null) {
  const s = (status ?? '').toUpperCase()
  if (s === 'DISPATCHED' || s === 'COMPLETED') return 'text-green-400 bg-green-950/40 border-green-800'
  if (s === 'PARTIAL') return 'text-amber-300 bg-amber-950/30 border-amber-700'
  if (s === 'FAILED') return 'text-red-300 bg-red-950/30 border-red-700'
  if (s === 'RECOMMENDED') return 'text-blue-300 bg-blue-950/40 border-blue-800'
  return 'text-gray-300 bg-gray-800 border-gray-600'
}

// ─── Connectivity hook ────────────────────────────────────────────────────────

function useOnline() {
  const [online, setOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true)
  useEffect(() => {
    const on  = () => setOnline(true)
    const off = () => setOnline(false)
    window.addEventListener('online',  on)
    window.addEventListener('offline', off)
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off) }
  }, [])
  return online
}

// ─── InventoryCard ────────────────────────────────────────────────────────────

function InventoryCard({
  position,
  pendingKey,
  queuedKeys,
  onChange,
}: {
  position: FieldPosition
  pendingKey: string | null
  queuedKeys: Set<string>
  onChange: (pos: FieldPosition, item: TrackedKey, delta: number) => void
}) {
  return (
    <div className="bg-[#0f1117] border border-[#1e232b] rounded-sm p-3 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-white font-bold text-sm">{position.name}</span>
        <span className="text-[9px] text-gray-600 font-mono">
          {position.x.toFixed(2)}, {position.y.toFixed(2)}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-1.5">
        {TRACKED_ITEMS.map(({ key, label }) => {
          const qty     = Number((position.inventory as FieldInventorySnapshot)[key] ?? 0)
          const pending = pendingKey === `${position.id}:${key}`
          const queued = queuedKeys.has(`${position.id}:${key}`)
          const { row, dot } = qtyClasses(qty)
          return (
            <div key={key} className={`border rounded-sm px-2 py-1.5 ${row}`}>
              <div className="text-[9px] uppercase tracking-widest opacity-70 mb-1 flex items-center gap-1 justify-between">
                <span className="inline-flex items-center gap-1">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dot}`} />
                {label}
                </span>
                {queued && <span className="text-[8px] text-amber-400 tracking-wider">PENDING</span>}
              </div>
              <div className="flex items-center justify-between gap-0.5">
                <button
                  onClick={() => onChange(position, key, -1)}
                  disabled={pending || qty <= 0}
                  className="opacity-60 hover:opacity-100 disabled:opacity-20 transition-opacity"
                  aria-label={`-${label}`}
                >
                  {pending ? <Loader2 className="w-3 h-3 animate-spin" /> : <MinusCircle className="w-4 h-4" />}
                </button>
                <span className="font-mono font-bold text-base min-w-[1.5rem] text-center">{qty}</span>
                <button
                  onClick={() => onChange(position, key, 1)}
                  disabled={pending}
                  className="opacity-60 hover:opacity-100 disabled:opacity-20 transition-opacity"
                  aria-label={`+${label}`}
                >
                  <PlusCircle className="w-4 h-4" />
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── Action Center ────────────────────────────────────────────────────────────

function ActionCenter({
  request,
  recommendation,
  recLoading,
  committing,
  commitQueued,
  radioMessages,
  radioDelivered,
  onCommit,
  onCopyShort,
  onCopyFull,
  onMarkRadioDelivered,
}: {
  request: FieldRequest | null
  recommendation: FieldRecommendation | null
  recLoading: boolean
  committing: boolean
  commitQueued: boolean
  radioMessages: string[]
  radioDelivered: boolean
  onCommit: () => void
  onCopyShort: () => void
  onCopyFull: () => void
  onMarkRadioDelivered: () => void
}) {
  // Empty state: prompt to create a request
  if (!request) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[260px] border border-dashed border-[#2a2e35] rounded-sm p-8 text-center space-y-3">
        <Radio className="w-8 h-8 text-gray-700" />
        <p className="text-xs text-gray-500 uppercase tracking-widest">Активного запиту немає</p>
        <p className="text-[10px] text-gray-600">Розгорніть форму нижче та створіть запит на скид</p>
      </div>
    )
  }

  const urgencyMeta = URGENCY[request.urgency] ?? URGENCY.low
  const requestStatus = request.status.toUpperCase()
  const committed   = REQUEST_TERMINAL_STATUSES.has(requestStatus)
  const hasGap      = recommendation?.actions.some(a => a.status === 'NOT_ENOUGH') ?? false
  const missingRows = recommendation?.actions.filter(a => a.status === 'NOT_ENOUGH') ?? []

  return (
    <div className="space-y-3">

      {/* ① CASE */}
      <div className="flex items-start justify-between gap-3 p-3 bg-[#0f1117] border border-[#1e232b] rounded-sm">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm border text-[10px] font-bold tracking-widest ${urgencyMeta.row}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${urgencyMeta.dot}`} />
              {urgencyMeta.label}
            </span>
            <span className="text-[10px] text-gray-600 font-mono">R: {request.radius_km} КМ</span>
          </div>
          <div className="font-mono text-sm text-gray-300 tracking-widest">
            X: {request.x.toFixed(3)}&ensp;Y: {request.y.toFixed(3)}
          </div>
        </div>
        <span className={`text-[9px] font-bold tracking-widest px-2 py-1 rounded-sm border shrink-0 ${statusStyle(requestStatus)}`}>
          {request.status}
        </span>
      </div>

      {!recLoading && missingRows.length > 0 && (
        <div className="border border-amber-700/50 bg-amber-950/20 rounded-sm px-3 py-2 text-[11px] text-amber-200">
          <span className="font-semibold">Часткове покриття:</span> бракує {missingRows.map(r => `${r.item_name.toUpperCase()} ×${r.qty}`).join(', ')}.
        </div>
      )}

      {/* ② NEEDS */}
      {request.required?.length > 0 && (
        <div className="grid grid-cols-3 gap-1.5">
          {request.required.map(need => (
            <div key={need.item_name} className="bg-[#0f1117] border border-[#1e232b] rounded-sm px-3 py-2 text-center">
              <div className="text-[9px] uppercase tracking-widest text-gray-500 mb-1">{need.item_name}</div>
              <div className="text-white font-mono font-bold text-2xl">{need.qty}</div>
            </div>
          ))}
        </div>
      )}

      {/* ③ RECOMMENDATION */}
      <div className="bg-[#080b0f] border border-[#1a1f28] rounded-sm p-4 space-y-2">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <span className="text-[10px] text-gray-500 uppercase tracking-widest flex items-center gap-1.5">
            {recLoading
              ? <Loader2 className="w-3 h-3 animate-spin" />
              : <CheckCircle2 className="w-3 h-3 text-blue-500" />
            }
            РЕКОМЕНДАЦІЯ МАРШРУТУ
          </span>
          {recommendation && (
            <span className="text-[10px] font-mono text-amber-300 border border-amber-800/40 bg-amber-950/20 px-2 py-0.5 rounded-sm">
              ETA: {recommendation.eta_min ?? '?'}–{recommendation.eta_max ?? '?'} ХВ
            </span>
          )}
        </div>

        {recLoading && (
          <p className="text-xs text-gray-600 animate-pulse">Розраховую найближчі позиції...</p>
        )}

        {!recLoading && !recommendation && (
          <p className="text-xs text-gray-600">Позиції в зоні не знайдено. Збільшіть радіус пошуку.</p>
        )}

        {!recLoading && recommendation && (
          <div className="space-y-1.5">
            {recommendation.actions.map((action, i) => {
              const gap = action.status === 'NOT_ENOUGH'
              return (
                <div
                  key={`${action.item_name}-${i}`}
                  className={`flex items-center justify-between gap-3 px-3 py-2.5 rounded-sm border text-xs ${
                    gap
                      ? 'border-red-800/60 bg-red-950/20 text-red-300'
                      : 'border-blue-900/40 bg-blue-950/10 text-blue-100'
                  }`}
                >
                  <div className="flex items-center gap-2 font-semibold">
                    {action.position && (
                      <>
                        <span className="text-amber-300 font-bold tracking-widest">{action.position}</span>
                        <span className="text-gray-600">→</span>
                      </>
                    )}
                    <span>
                      {action.item_name.toUpperCase()}{' '}
                      <span className="font-mono text-base font-bold">×{action.qty}</span>
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[10px] opacity-70 shrink-0">
                    {action.eta_min   != null && <span>{action.eta_min} хв</span>}
                    {action.distance_km != null && <span>{action.distance_km.toFixed(1)} км</span>}
                    {gap && (
                      <span className="flex items-center gap-1 text-red-400">
                        <AlertTriangle className="w-3 h-3" /> ДЕФІЦИТ
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* ④ DISPATCH */}
      {!committed && (
        <button
          onClick={onCommit}
          disabled={committing || commitQueued || recLoading || !recommendation}
          className={`
            w-full flex items-center justify-center gap-3 px-6 py-4
            font-bold tracking-[0.2em] text-sm uppercase rounded-sm border
            transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500
            disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none
            ${!committing && recommendation
              ? hasGap
                ? 'bg-amber-900/40 hover:bg-amber-800/50 border-amber-700 text-amber-100 shadow-[0_0_18px_rgba(180,130,0,0.2)] hover:shadow-[0_0_28px_rgba(180,130,0,0.4)]'
                : 'bg-red-900/50 hover:bg-red-800/60 border-red-700 text-white shadow-[0_0_20px_rgba(185,28,28,0.3)] hover:shadow-[0_0_35px_rgba(185,28,28,0.5)]'
              : 'bg-gray-900 border-gray-700 text-gray-500'
            }
          `}
          aria-live="polite"
        >
          {committing
            ? <><Loader2 className="w-5 h-5 animate-spin" /> ВІДПРАВЛЕННЯ...</>
            : commitQueued
              ? <><Loader2 className="w-5 h-5 animate-spin" /> В ЧЕРЗІ СИНХР.</>
              : <><Send className="w-5 h-5" /> ПІДТВЕРДИТИ СКИД</>
          }
        </button>
      )}

      {/* ⑤ RADIO — feedback after dispatch */}
      {radioMessages.length > 0 && (
        <div className="border border-amber-700/40 bg-amber-950/20 rounded-sm p-3 space-y-1">
          <div className="text-[10px] text-amber-400 uppercase tracking-widest mb-2 flex items-center justify-between gap-2">
            <span className="inline-flex items-center gap-1.5"><Radio className="w-3 h-3" /> РАДІОПОВІДОМЛЕННЯ</span>
            <div className="flex items-center gap-1">
              <button onClick={onCopyShort} className="wolf-btn text-[10px] px-2 py-1" type="button">
                <Copy className="w-3 h-3" /> КОРОТКИЙ
              </button>
              <button onClick={onCopyFull} className="wolf-btn text-[10px] px-2 py-1" type="button">
                <Copy className="w-3 h-3" /> ПОВНИЙ
              </button>
              <button onClick={onMarkRadioDelivered} className="wolf-btn text-[10px] px-2 py-1" type="button">
                <Check className="w-3 h-3" /> {radioDelivered ? 'ПЕРЕДАНО' : 'ПОЗНАЧИТИ'}
              </button>
            </div>
          </div>
          {radioMessages.map((msg, i) => (
            <div key={i} className="text-xs text-amber-100 font-mono pl-3 border-l border-amber-700/40">{msg}</div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Grouped logs ─────────────────────────────────────────────────────────────

function GroupedLogs({ logs }: { logs: FieldDispatchLog[] }) {
  // Normalize logs for stable grouping after refresh.
  const groups = useMemo(() => {
    const sorted = [...logs].sort(
      (a, b) => new Date(b.created_at ?? 0).getTime() - new Date(a.created_at ?? 0).getTime(),
    )
    const seen = new Set<string>()
    const deduped: FieldDispatchLog[] = []
    for (const log of sorted) {
      if (seen.has(log.id)) continue
      seen.add(log.id)
      deduped.push(log)
    }

    const map = new Map<string, FieldDispatchLog[]>()
    for (const log of deduped) {
      if (!map.has(log.request_id)) map.set(log.request_id, [])
      map.get(log.request_id)!.push(log)
    }
    return Array.from(map.entries())
  }, [logs])

  if (groups.length === 0) {
    return <p className="text-xs text-gray-600 uppercase tracking-widest py-4 text-center">Журнал пустий</p>
  }

  return (
    <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
      {groups.map(([reqId, items]) => {
        // Group items inside the request by position
        const byPos = new Map<string, FieldDispatchLog[]>()
        for (const l of items) {
          const k = l.position_name ?? '—'
          if (!byPos.has(k)) byPos.set(k, [])
          byPos.get(k)!.push(l)
        }
        const status   = (items[0]?.request_status ?? items[0]?.status ?? '—').toUpperCase()
        const time     = fmtTime(items[0]?.created_at)
        const by       = items[0]?.dispatched_by
        return (
          <div key={reqId} className="border border-[#1a1f28] bg-[#080b0f] rounded-sm overflow-hidden">
            {/* Request header */}
            <div className="flex items-center justify-between px-3 py-2 bg-[#0f1217] border-b border-[#1a1f28]">
              <span className="text-[10px] font-mono text-gray-500">
                ЗАПИТ #{reqId.slice(-6).toUpperCase()}
              </span>
              <div className="flex items-center gap-2">
                {by && <span className="text-[10px] text-gray-500 font-mono">OP: {by}</span>}
                <span className="text-[10px] text-gray-600 font-mono">{time}</span>
                <span className={`text-[9px] font-bold tracking-widest px-1.5 py-0.5 rounded-sm border ${statusStyle(status)}`}>{status}</span>
              </div>
            </div>
            {/* Items by position */}
            <div className="p-3 space-y-2">
              {Array.from(byPos.entries()).map(([pos, posLogs]) => (
                <div key={pos}>
                  <div className="text-[9px] text-amber-400 uppercase tracking-widest mb-1">{pos}</div>
                  {posLogs.map((log: FieldDispatchLog) => (
                    <div key={log.id} className="flex items-center justify-between text-xs pl-2 py-0.5">
                      <span className="text-gray-300">
                        {log.item_name.toUpperCase()}&ensp;
                        <span className="font-mono font-bold text-white">×{log.qty}</span>
                      </span>
                      {log.eta_min != null && (
                        <span className="text-gray-600 font-mono text-[10px]">{log.eta_min} хв</span>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function FieldDropPage() {
  const toast  = useToast()
  const online = useOnline()

  const [positions,        setPositions]        = useState<FieldPosition[]>([])
  const [requests,         setRequests]         = useState<FieldRequest[]>([])
  const [logs,             setLogs]             = useState<FieldDispatchLog[]>([])
  const [selectedId,       setSelectedId]       = useState<string>('')
  const [recommendation,   setRecommendation]   = useState<FieldRecommendation | null>(null)
  const [radioMessages,    setRadioMessages]    = useState<string[]>([])
  const [radioDelivered,   setRadioDelivered]   = useState(false)
  const [pendingQueue,     setPendingQueue]     = useState<PendingAction[]>([])
  const [flushingQueue,    setFlushingQueue]    = useState(false)

  // Loading states
  const [loading,          setLoading]          = useState(true)
  const [refreshing,       setRefreshing]       = useState(false)
  const [recLoading,       setRecLoading]       = useState(false)
  const [submittingPos,    setSubmittingPos]    = useState(false)
  const [submittingReq,    setSubmittingReq]    = useState(false)
  const [committing,       setCommitting]       = useState(false)
  const [invPendingKey,    setInvPendingKey]    = useState<string | null>(null)

  // Race guards and mutable refs for async flows
  const selectedIdRef      = useRef<string>('')
  const loadAllSeqRef      = useRef(0)
  const loadRecSeqRef      = useRef(0)
  const mutationCountRef   = useRef(0)
  const commitInFlightRef  = useRef(false)
  const flushInFlightRef   = useRef(false)

  // Forms
  const [posForm, setPosForm] = useState({ name: '', x: '48.006', y: '37.760' })
  const [reqForm, setReqForm] = useState({
    x: '48.006', y: '37.760', urgency: 'high', radius_km: '5',
    hemostatic: '0', bandage: '0', tourniquet: '0',
  })

  // Initial load
  useEffect(() => { void loadAll(true) }, [])

  // Keep ref synchronized to avoid stale closures inside async handlers
  useEffect(() => {
    selectedIdRef.current = selectedId
  }, [selectedId])

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_QUEUE_KEY)
      if (!raw) return
      const parsed = JSON.parse(raw) as PendingAction[]
      if (Array.isArray(parsed)) setPendingQueue(parsed)
    } catch {
      setPendingQueue([])
    }
  }, [])

  useEffect(() => {
    localStorage.setItem(STORAGE_QUEUE_KEY, JSON.stringify(pendingQueue))
  }, [pendingQueue])

  // Load recommendation when active request changes
  useEffect(() => {
    if (!selectedId) { setRecommendation(null); return }
    void loadRec(selectedId)
  }, [selectedId])

  // Auto-refresh every 30 s when online
  useEffect(() => {
    if (!online) return
    const id = setInterval(() => void loadAll(false, 'auto'), 30_000)
    return () => clearInterval(id)
  }, [online])

  useEffect(() => {
    if (!online) return
    if (!pendingQueue.some(a => a.status === 'pending')) return
    void flushPendingQueue()
  }, [online, pendingQueue.length])

  const pendingInventoryKeys = useMemo(() => {
    const set = new Set<string>()
    for (const action of pendingQueue) {
      if (action.status === 'pending' && action.type === 'inventory_delta') {
        set.add(`${action.positionId}:${action.item}`)
      }
    }
    return set
  }, [pendingQueue])

  const pendingCommitRequestIds = useMemo(() => {
    const set = new Set<string>()
    for (const action of pendingQueue) {
      if (action.status === 'pending' && action.type === 'commit_request') {
        set.add(action.requestId)
      }
    }
    return set
  }, [pendingQueue])

  // ── Data loaders ──────────────────────────────────────────────────────────

  async function loadAll(initial = false, source: 'auto' | 'manual' | 'postAction' = 'manual') {
    if (source === 'auto' && mutationCountRef.current > 0) return

    const seq = ++loadAllSeqRef.current
    try {
      if (initial) setLoading(true)
      else if (source === 'manual') setRefreshing(true)

      const [pos, reqs, lg] = await Promise.all([
        listFieldDropPositions(),
        listFieldDropRequests(),
        listFieldDropLogs(40),
      ])

      // Ignore stale response that returned out of order.
      if (seq !== loadAllSeqRef.current) return
      if (source === 'auto' && mutationCountRef.current > 0) return

      setPositions(pos)
      setRequests(reqs)
      setLogs(lg)

      if (reqs.length === 0) {
        setSelectedId('')
        selectedIdRef.current = ''
        setRecommendation(null)
        loadRecSeqRef.current += 1
        setRecLoading(false)
      } else if (!selectedIdRef.current || !reqs.some(r => r.id === selectedIdRef.current)) {
        setSelectedId(reqs[0].id)
      }
    } catch {
      toast.error('Помилка завантаження. Перевірте з\'єднання та оновіть сторінку.')
    } finally {
      if (seq === loadAllSeqRef.current) {
        setLoading(false)
        if (source === 'manual') setRefreshing(false)
      }
    }
  }

  async function loadRec(reqId: string) {
    const seq = ++loadRecSeqRef.current
    setRecLoading(true)
    try {
      const rec = await getFieldDropRecommendation(reqId)
      if (seq !== loadRecSeqRef.current) return
      if (selectedIdRef.current !== reqId) return
      setRecommendation(rec)
    } catch {
      if (seq === loadRecSeqRef.current && selectedIdRef.current === reqId) {
        setRecommendation(null)
      }
    } finally {
      if (seq === loadRecSeqRef.current) setRecLoading(false)
    }
  }

  function enqueueAction(action: PendingAction) {
    setPendingQueue(prev => [...prev, action])
  }

  async function flushPendingQueue() {
    if (!online || flushInFlightRef.current) return

    const queue = pendingQueue
      .filter(a => a.status === 'pending')
      .sort((a, b) => a.createdAt - b.createdAt)

    if (queue.length === 0) return

    flushInFlightRef.current = true
    setFlushingQueue(true)
    mutationCountRef.current += 1

    try {
      const latestPositions = await listFieldDropPositions()
      const positionById = new Map(latestPositions.map(p => [p.id, p]))

      for (const action of queue) {
        try {
          if (action.type === 'inventory_delta') {
            const pos = positionById.get(action.positionId)
            if (!pos) throw new Error('Position not found during queue replay')
            const currentQty = Math.max(0, Number((pos.inventory as FieldInventorySnapshot)[action.item] ?? 0))
            const nextQty = Math.max(0, currentQty + action.delta)
            await updateFieldDropInventory(action.positionId, action.item, nextQty, action.id)
            positionById.set(action.positionId, {
              ...pos,
              inventory: { ...pos.inventory, [action.item]: nextQty },
            })
          }

          if (action.type === 'commit_request') {
            const commit = await commitFieldDropRequest(action.requestId, action.id)
            if (commit.request_id !== action.requestId) {
              throw new Error('Commit request_id mismatch during queue replay')
            }
            if (selectedIdRef.current === action.requestId && commit.messages.length > 0) {
              setRadioMessages(commit.messages)
            }
          }

          setPendingQueue(prev => prev.filter(p => p.id !== action.id))
        } catch {
          setPendingQueue(prev => prev.map(p => (p.id === action.id ? { ...p, status: 'failed' } : p)))
        }
      }

      await loadAll(false, 'postAction')
      if (selectedIdRef.current) void loadRec(selectedIdRef.current)
    } finally {
      mutationCountRef.current -= 1
      setFlushingQueue(false)
      flushInFlightRef.current = false
    }
  }

  function buildShortRadioMessage() {
    const rid = selectedIdRef.current ? selectedIdRef.current.slice(-6).toUpperCase() : 'N/A'
    const groups = new Map<string, string[]>()
    for (const line of radioMessages) {
      const [pos, rest] = line.split(':')
      if (!groups.has(pos)) groups.set(pos, [])
      groups.get(pos)!.push(rest?.replace('send', '').replace('to grid', '').trim() ?? line)
    }
    const compact = Array.from(groups.entries()).map(([pos, rows]) => `${pos.trim()} ${rows.join(', ')}`)
    return `${compact.join('; ')}, кейс ${rid}`
  }

  function buildFullRadioMessage() {
    return radioMessages.join('\n')
  }

  async function copyToClipboard(text: string, label: string) {
    try {
      await navigator.clipboard.writeText(text)
      toast.success(`${label} скопійовано`)
    } catch {
      toast.error('Не вдалося скопіювати повідомлення')
    }
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  async function onCreatePosition(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSubmittingPos(true)
    mutationCountRef.current += 1
    try {
      const opId = createOpId('position')
      const created = await createFieldDropPosition({
        name: posForm.name.trim(),
        x: Number(posForm.x), y: Number(posForm.y),
        inventory: { hemostatic: 0, bandage: 0, tourniquet: 0, meds: {} },
      }, opId)
      setPositions(p => [created, ...p])
      setPosForm(f => ({ ...f, name: '' }))
      toast.success(`Позиція «${created.name}» додана`)
      void loadAll(false, 'postAction')
    } catch {
      toast.error('Не вдалося створити позицію. Спробуйте ще раз.')
    } finally {
      mutationCountRef.current -= 1
      setSubmittingPos(false)
    }
  }

  async function changeInventory(pos: FieldPosition, item: TrackedKey, delta: number) {
    const cur  = Math.max(0, Number((pos.inventory as FieldInventorySnapshot)[item] ?? 0))
    const next = Math.max(0, cur + delta)
    const key  = `${pos.id}:${item}`

    if (!online) {
      setPositions(ps => ps.map(p =>
        p.id === pos.id ? { ...p, inventory: { ...p.inventory, [item]: next } } : p
      ))
      enqueueAction({
        id: createOpId('inv'),
        type: 'inventory_delta',
        status: 'pending',
        createdAt: Date.now(),
        positionId: pos.id,
        item,
        delta,
      })
      toast.info('Офлайн: зміна інвентарю додана в чергу синхронізації')
      return
    }

    setInvPendingKey(key)
    mutationCountRef.current += 1
    try {
      await updateFieldDropInventory(pos.id, item, next, createOpId('inv'))
      setPositions(ps => ps.map(p =>
        p.id === pos.id ? { ...p, inventory: { ...p.inventory, [item]: next } } : p
      ))
      void loadAll(false, 'postAction')
    } catch {
      toast.error(`Не вдалося оновити ${item}. Спробуйте ще раз.`)
    } finally {
      mutationCountRef.current -= 1
      setInvPendingKey(null)
    }
  }

  async function onCreateRequest(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const required = TRACKED_ITEMS
      .map(({ key }) => ({ item_name: key, qty: Math.max(0, Number(reqForm[key])) }))
      .filter(i => i.qty > 0)
    if (required.length === 0) { toast.info('Вкажіть хоча б один предмет для скиду'); return }
    setSubmittingReq(true)
    mutationCountRef.current += 1
    try {
      const opId = createOpId('request')
      const created = await createFieldDropRequest({
        x: Number(reqForm.x), y: Number(reqForm.y),
        urgency: reqForm.urgency,
        radius_km: Math.max(0.5, Number(reqForm.radius_km)),
        required,
      }, opId)
      setRequests(rs => [created, ...rs])
      setSelectedId(created.id)
      setReqForm(f => ({ ...f, hemostatic: '0', bandage: '0', tourniquet: '0' }))
      toast.success('Запит створено — розраховую рекомендації')
      void loadAll(false, 'postAction')
    } catch {
      toast.error('Не вдалося створити запит. Перевірте з\'єднання.')
    } finally {
      mutationCountRef.current -= 1
      setSubmittingReq(false)
    }
  }

  async function onCommit() {
    if (!selectedId) return
    if (commitInFlightRef.current) return

    if (!online) {
      if (pendingCommitRequestIds.has(selectedId)) {
        toast.info('Цей commit вже у черзі синхронізації')
        return
      }
      enqueueAction({
        id: createOpId('commit'),
        type: 'commit_request',
        status: 'pending',
        createdAt: Date.now(),
        requestId: selectedId,
      })
      toast.info('Офлайн: commit доданий у чергу синхронізації')
      return
    }

    commitInFlightRef.current = true
    setCommitting(true)
    mutationCountRef.current += 1
    try {
      const commit = await commitFieldDropRequest(selectedId, createOpId('commit'))
      if (commit.request_id !== selectedId) {
        throw new Error('Commit request_id mismatch')
      }
      setRadioMessages(commit.messages)
      setRadioDelivered(false)
      await loadAll(false, 'postAction')
      void loadRec(selectedId)
      if (commit.already_committed) {
        // Treat as successful completion — the request was already dispatched
        toast.success('Запит вже підтверджений — синхронізацію завершено')
      } else {
        toast.success('Скид підтверджено — радіоповідомлення надіслані')
      }
    } catch {
      toast.error('Помилка підтвердження скиду. Перевірте з\'єднання та спробуйте ще раз.')
    } finally {
      mutationCountRef.current -= 1
      setCommitting(false)
      commitInFlightRef.current = false
    }
  }

  const selectedRequest = useMemo(
    () => requests.find(r => r.id === selectedId) ?? null,
    [requests, selectedId],
  )

  const selectedCommitQueued = selectedId ? pendingCommitRequestIds.has(selectedId) : false
  const pendingCount = pendingQueue.filter(a => a.status === 'pending').length
  const failedCount = pendingQueue.filter(a => a.status === 'failed').length

  function retryFailedQueue() {
    setPendingQueue(prev => prev.map(a => (a.status === 'failed' ? { ...a, status: 'pending' } : a)))
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-7 h-7 text-amber-400 animate-spin" />
          <p className="text-xs text-gray-500 uppercase tracking-widest">Завантаження бойового контуру...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 p-4 md:p-6 space-y-4">

      {/* ── HEADER ── */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h1 className="text-lg font-bold tracking-widest text-white uppercase flex items-center gap-2">
          <Radio className="w-5 h-5 text-amber-400" /> ПОЛЬОВИЙ СКИД
        </h1>
        <div className="flex items-center gap-2">
          {/* Online pill */}
          <div className={`flex items-center gap-1.5 text-[10px] font-bold tracking-widest uppercase border rounded-sm px-2 py-1 ${
            online
              ? 'text-green-400 border-green-900/60 bg-green-950/20'
              : 'text-red-400 border-red-900/60 bg-red-950/30'
          }`}>
            {online ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            {online ? 'ОНЛАЙН' : 'ОФЛАЙН'}
          </div>
          {/* Offline warning banner */}
          {!online && (
            <div className="text-[10px] text-red-300 bg-red-950/40 border border-red-800 rounded-sm px-2 py-1 tracking-widest uppercase">
              Офлайн: дії йдуть у чергу та синхронізуються після reconnect
            </div>
          )}
          <button
            onClick={() => void loadAll(false, 'manual')}
            disabled={refreshing}
            className="wolf-btn disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'ОНОВЛЕННЯ' : 'ОНОВИТИ'}
          </button>
        </div>
      </div>

      {(pendingCount > 0 || failedCount > 0 || flushingQueue) && (
        <div className="wolf-panel p-3 border-amber-800/40 bg-amber-950/10">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="text-[10px] uppercase tracking-widest text-amber-300">
              Pending Sync Queue: {pendingCount} pending, {failedCount} failed {flushingQueue ? '• SYNCING...' : ''}
            </div>
            <div className="flex items-center gap-2">
              {failedCount > 0 && (
                <button onClick={retryFailedQueue} className="wolf-btn text-[10px] px-2 py-1" type="button">
                  Retry Failed
                </button>
              )}
              <button onClick={() => void flushPendingQueue()} className="wolf-btn text-[10px] px-2 py-1" type="button" disabled={!online || flushingQueue}>
                Flush Now
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── MAIN GRID: Action Center (2/3) + Inventory (1/3) ── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">

        {/* LEFT: Action Center */}
        <div className="xl:col-span-2 space-y-4">

          {/* Request selector */}
          {requests.length > 0 && (
            <div className="wolf-panel p-3 flex items-center gap-3">
              <span className="text-[10px] text-gray-500 uppercase tracking-widest shrink-0">
                АКТИВНИЙ ЗАПИТ
              </span>
              <select
                value={selectedId}
                onChange={e => setSelectedId(e.target.value)}
                className="wolf-input flex-1 text-xs"
              >
                {requests.map(r => (
                  <option key={r.id} value={r.id}>
                    {(URGENCY[r.urgency]?.label ?? r.urgency.toUpperCase())} · X:{r.x.toFixed(2)} Y:{r.y.toFixed(2)} · {r.status}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Action Center */}
          <div className="wolf-panel p-4 xl:sticky xl:top-4">
            <div className="text-[10px] text-gray-500 uppercase tracking-widest mb-3 flex items-center gap-2">
              <Send className="w-3 h-3 text-red-400" /> ЦЕНТР ДІЙ
            </div>
            <ActionCenter
              request={selectedRequest}
              recommendation={recommendation}
              recLoading={recLoading}
              committing={committing}
              commitQueued={selectedCommitQueued}
              radioMessages={radioMessages}
              radioDelivered={radioDelivered}
              onCommit={onCommit}
              onCopyShort={() => void copyToClipboard(buildShortRadioMessage(), 'Короткий формат')}
              onCopyFull={() => void copyToClipboard(buildFullRadioMessage(), 'Повний формат')}
              onMarkRadioDelivered={() => {
                setRadioDelivered(v => !v)
                toast.success('Статус передачі по рації оновлено')
              }}
            />
          </div>

          {/* New Request (collapsible — secondary action) */}
          <div className="wolf-panel p-4">
            <details>
              <summary className="text-[10px] text-gray-500 uppercase tracking-widest cursor-pointer select-none list-none flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <ClipboardList className="w-3 h-3 text-red-400" /> НОВИЙ ЗАПИТ НА СКИД
                </span>
                <ChevronDown className="w-3 h-3" />
              </summary>
              <form onSubmit={onCreateRequest} className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                <input
                  type="number" step="0.001" required
                  value={reqForm.x}
                  onChange={e => setReqForm(f => ({ ...f, x: e.target.value }))}
                  placeholder="X координата"
                  className="wolf-input text-xs"
                />
                <input
                  type="number" step="0.001" required
                  value={reqForm.y}
                  onChange={e => setReqForm(f => ({ ...f, y: e.target.value }))}
                  placeholder="Y координата"
                  className="wolf-input text-xs"
                />
                <select
                  value={reqForm.urgency}
                  onChange={e => setReqForm(f => ({ ...f, urgency: e.target.value }))}
                  className="wolf-input text-xs"
                >
                  <option value="critical">КРИТИЧНО</option>
                  <option value="high">ВИСОКИЙ</option>
                  <option value="medium">СЕРЕДНІЙ</option>
                  <option value="low">НИЗЬКИЙ</option>
                </select>
                <input
                  type="number" step="0.5" min="0.5" required
                  value={reqForm.radius_km}
                  onChange={e => setReqForm(f => ({ ...f, radius_km: e.target.value }))}
                  placeholder="Радіус (км)"
                  className="wolf-input text-xs"
                />
                {TRACKED_ITEMS.map(({ key, label }) => (
                  <div key={key} className="flex items-center gap-2 col-span-1">
                    <span className="text-[9px] text-gray-500 uppercase tracking-widest w-20 shrink-0">{label}</span>
                    <input
                      type="number" min="0"
                      value={reqForm[key]}
                      onChange={e => setReqForm(f => ({ ...f, [key]: e.target.value }))}
                      className="wolf-input text-xs flex-1 min-w-0"
                    />
                  </div>
                ))}
                <button
                  type="submit"
                  disabled={submittingReq}
                  className="wolf-btn-danger col-span-2 md:col-span-1 disabled:opacity-50 text-xs flex items-center justify-center gap-2"
                >
                  {submittingReq
                    ? <><Loader2 className="w-3 h-3 animate-spin" /> ФОРМУВАННЯ</>
                    : 'СТВОРИТИ ЗАПИТ'
                  }
                </button>
              </form>
            </details>
          </div>

        </div>

        {/* RIGHT: Inventory positions */}
        <div className="space-y-4">
          <div className="wolf-panel p-4">
            <div className="text-[10px] text-gray-500 uppercase tracking-widest mb-3 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Package className="w-3 h-3 text-blue-400" /> ЗАПАСИ ПОЗИЦІЙ
              </span>
              <span className="text-gray-600">{positions.length}</span>
            </div>
            <div className="space-y-2 max-h-[480px] overflow-y-auto pr-0.5">
              {positions.map(pos => (
                <InventoryCard
                  key={pos.id}
                  position={pos}
                  pendingKey={invPendingKey}
                  queuedKeys={pendingInventoryKeys}
                  onChange={changeInventory}
                />
              ))}
              {positions.length === 0 && (
                <p className="text-xs text-gray-600 uppercase tracking-widest py-4 text-center">
                  Позицій немає
                </p>
              )}
            </div>
          </div>

          {/* New Position (collapsible — secondary action) */}
          <div className="wolf-panel p-4">
            <details>
              <summary className="text-[10px] text-gray-500 uppercase tracking-widest cursor-pointer select-none list-none flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <MapPinned className="w-3 h-3 text-amber-400" /> НОВА ПОЗИЦІЯ
                </span>
                <ChevronDown className="w-3 h-3" />
              </summary>
              <form onSubmit={onCreatePosition} className="mt-4 space-y-2">
                <input
                  value={posForm.name}
                  onChange={e => setPosForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="НАЗВА (АЛЬФА-1, БРАВО-2...)"
                  className="wolf-input text-xs w-full"
                  required
                />
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="number" step="0.001"
                    value={posForm.x}
                    onChange={e => setPosForm(f => ({ ...f, x: e.target.value }))}
                    placeholder="X"
                    className="wolf-input text-xs"
                    required
                  />
                  <input
                    type="number" step="0.001"
                    value={posForm.y}
                    onChange={e => setPosForm(f => ({ ...f, y: e.target.value }))}
                    placeholder="Y"
                    className="wolf-input text-xs"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={submittingPos}
                  className="wolf-btn w-full text-xs disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {submittingPos
                    ? <><Loader2 className="w-3 h-3 animate-spin" /> СТВОРЕННЯ</>
                    : 'ДОДАТИ ПОЗИЦІЮ'
                  }
                </button>
              </form>
            </details>
          </div>
        </div>

      </div>

      {/* ── LOGS ── */}
      <div className="wolf-panel p-4">
        <div className="text-[10px] text-gray-500 uppercase tracking-widest mb-3 flex items-center gap-2">
          <ClipboardList className="w-3 h-3" /> ЖУРНАЛ СКИДІВ
        </div>
        <GroupedLogs logs={logs} />
      </div>

    </div>
  )
}
