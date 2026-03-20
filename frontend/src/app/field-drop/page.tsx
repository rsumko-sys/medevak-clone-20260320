'use client'

import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Radio, MapPinned, Package, PlusCircle, MinusCircle, Send, ClipboardList, RefreshCw } from 'lucide-react'
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
  FieldPosition,
  FieldRecommendation,
  FieldRequest,
} from '@/lib/types'

const TRACKED_ITEMS = [
  { key: 'hemostatic', label: 'HEMOSTATIC' },
  { key: 'bandage', label: 'BANDAGE' },
  { key: 'tourniquet', label: 'TOURNIQUET' },
] as const

type TrackedItemKey = (typeof TRACKED_ITEMS)[number]['key']

export default function FieldDropPage() {
  const toast = useToast()

  const [positions, setPositions] = useState<FieldPosition[]>([])
  const [requests, setRequests] = useState<FieldRequest[]>([])
  const [logs, setLogs] = useState<FieldDispatchLog[]>([])
  const [selectedRequestId, setSelectedRequestId] = useState<string>('')
  const [recommendation, setRecommendation] = useState<FieldRecommendation | null>(null)
  const [radioMessages, setRadioMessages] = useState<string[]>([])

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [submittingPosition, setSubmittingPosition] = useState(false)
  const [submittingRequest, setSubmittingRequest] = useState(false)
  const [committing, setCommitting] = useState(false)
  const [inventoryPendingKey, setInventoryPendingKey] = useState<string | null>(null)

  const [positionForm, setPositionForm] = useState({
    name: '',
    x: '0',
    y: '0',
    hemostatic: '0',
    bandage: '0',
    tourniquet: '0',
  })

  const [requestForm, setRequestForm] = useState({
    x: '0',
    y: '0',
    urgency: 'high',
    radius_km: '5',
    hemostatic: '0',
    bandage: '0',
    tourniquet: '0',
  })

  useEffect(() => {
    void loadAll(true)
  }, [])

  useEffect(() => {
    if (!selectedRequestId) {
      setRecommendation(null)
      return
    }
    void loadRecommendation(selectedRequestId)
  }, [selectedRequestId])

  async function loadAll(initial = false) {
    try {
      if (initial) setLoading(true)
      else setRefreshing(true)

      const [positionsData, requestsData, logsData] = await Promise.all([
        listFieldDropPositions(),
        listFieldDropRequests(),
        listFieldDropLogs(20),
      ])

      setPositions(positionsData)
      setRequests(requestsData)
      setLogs(logsData)

      if (requestsData.length === 0) {
        setSelectedRequestId('')
        setRecommendation(null)
      } else if (!selectedRequestId || !requestsData.some((r) => r.id === selectedRequestId)) {
        setSelectedRequestId(requestsData[0].id)
      }
    } catch (error) {
      console.error('Failed to load field-drop data:', error)
      toast.error('Не вдалося завантажити дані польового скиду')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  async function loadRecommendation(requestId: string) {
    try {
      const rec = await getFieldDropRecommendation(requestId)
      setRecommendation(rec)
    } catch (error) {
      console.error('Failed to load recommendation:', error)
      setRecommendation(null)
      toast.error('Не вдалося отримати рекомендацію скиду')
    }
  }

  async function onCreatePosition(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmittingPosition(true)

    try {
      const created = await createFieldDropPosition({
        name: positionForm.name.trim(),
        x: Number(positionForm.x),
        y: Number(positionForm.y),
        inventory: {
          hemostatic: Math.max(0, Number(positionForm.hemostatic)),
          bandage: Math.max(0, Number(positionForm.bandage)),
          tourniquet: Math.max(0, Number(positionForm.tourniquet)),
          meds: {},
        },
      })

      setPositions((prev) => [created, ...prev])
      setPositionForm({
        name: '',
        x: '0',
        y: '0',
        hemostatic: '0',
        bandage: '0',
        tourniquet: '0',
      })
      toast.success('Позицію додано')
    } catch (error) {
      console.error('Failed to create position:', error)
      toast.error('Не вдалося створити позицію')
    } finally {
      setSubmittingPosition(false)
    }
  }

  async function changeInventory(position: FieldPosition, item: TrackedItemKey, delta: number) {
    const currentQty = Math.max(0, Number(position.inventory[item] ?? 0))
    const nextQty = Math.max(0, currentQty + delta)
    const pendingKey = `${position.id}:${item}`
    setInventoryPendingKey(pendingKey)

    try {
      await updateFieldDropInventory(position.id, item, nextQty)
      setPositions((prev) =>
        prev.map((p) =>
          p.id === position.id
            ? {
                ...p,
                inventory: {
                  ...p.inventory,
                  [item]: nextQty,
                },
              }
            : p
        )
      )
    } catch (error) {
      console.error('Failed to update inventory:', error)
      toast.error('Не вдалося оновити інвентар')
    } finally {
      setInventoryPendingKey(null)
    }
  }

  async function onCreateRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmittingRequest(true)

    try {
      const required = TRACKED_ITEMS.map(({ key }) => ({
        item_name: key,
        qty: Math.max(0, Number(requestForm[key])),
      })).filter((item) => item.qty > 0)

      if (required.length === 0) {
        toast.info('Вкажіть хоча б одну позицію для скиду')
        return
      }

      const created = await createFieldDropRequest({
        x: Number(requestForm.x),
        y: Number(requestForm.y),
        urgency: requestForm.urgency,
        radius_km: Math.max(0.5, Number(requestForm.radius_km)),
        required,
      })

      setRequests((prev) => [created, ...prev])
      setSelectedRequestId(created.id)
      setRequestForm((prev) => ({
        ...prev,
        hemostatic: '0',
        bandage: '0',
        tourniquet: '0',
      }))
      toast.success('Запит створено')
    } catch (error) {
      console.error('Failed to create request:', error)
      toast.error('Не вдалося створити запит')
    } finally {
      setSubmittingRequest(false)
    }
  }

  async function onCommitRequest() {
    if (!selectedRequestId) {
      toast.info('Оберіть активний запит')
      return
    }

    setCommitting(true)
    try {
      const commit = await commitFieldDropRequest(selectedRequestId)
      setRadioMessages(commit.messages)
      await loadAll()
      await loadRecommendation(selectedRequestId)
      toast.success('Запит передано в роботу')
    } catch (error) {
      console.error('Failed to commit request:', error)
      toast.error('Не вдалося підтвердити запит')
    } finally {
      setCommitting(false)
    }
  }

  const selectedRequest = useMemo(
    () => requests.find((request) => request.id === selectedRequestId) ?? null,
    [requests, selectedRequestId]
  )

  function formatTime(value?: string | null) {
    if (!value) return 'N/A'
    try {
      return new Date(value).toLocaleString('uk-UA')
    } catch {
      return value
    }
  }

  if (loading) {
    return (
      <div className="flex-1 p-6">
        <div className="wolf-panel p-6 text-sm text-gray-400 uppercase tracking-widest">Завантаження польового скиду...</div>
      </div>
    )
  }

  return (
    <div className="flex-1 p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-widest text-white uppercase mb-1 flex items-center gap-2">
            <Radio className="w-5 h-5 text-amber-400" /> ПОЛЬОВИЙ СКИД
          </h1>
          <p className="text-xs text-gray-500 font-mono tracking-widest uppercase">Логістика позицій, рекомендації та радіоленти в єдиній системі</p>
        </div>
        <button
          onClick={() => void loadAll()}
          disabled={refreshing}
          className="wolf-btn disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} /> ОНОВИТИ
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <section className="wolf-panel p-5 space-y-4">
          <h2 className="wolf-title flex items-center gap-2"><MapPinned className="w-4 h-4 text-amber-400" /> НОВА ПОЗИЦІЯ</h2>
          <form onSubmit={onCreatePosition} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input
              value={positionForm.name}
              onChange={(event) => setPositionForm((prev) => ({ ...prev, name: event.target.value }))}
              placeholder="НАЗВА ПОЗИЦІЇ"
              className="wolf-input md:col-span-2"
              required
            />
            <input
              type="number"
              step="0.1"
              value={positionForm.x}
              onChange={(event) => setPositionForm((prev) => ({ ...prev, x: event.target.value }))}
              placeholder="X"
              className="wolf-input"
              required
            />
            <input
              type="number"
              step="0.1"
              value={positionForm.y}
              onChange={(event) => setPositionForm((prev) => ({ ...prev, y: event.target.value }))}
              placeholder="Y"
              className="wolf-input"
              required
            />
            <input
              type="number"
              min={0}
              value={positionForm.hemostatic}
              onChange={(event) => setPositionForm((prev) => ({ ...prev, hemostatic: event.target.value }))}
              placeholder="HEMOSTATIC"
              className="wolf-input"
            />
            <input
              type="number"
              min={0}
              value={positionForm.bandage}
              onChange={(event) => setPositionForm((prev) => ({ ...prev, bandage: event.target.value }))}
              placeholder="BANDAGE"
              className="wolf-input"
            />
            <input
              type="number"
              min={0}
              value={positionForm.tourniquet}
              onChange={(event) => setPositionForm((prev) => ({ ...prev, tourniquet: event.target.value }))}
              placeholder="TOURNIQUET"
              className="wolf-input md:col-span-2"
            />
            <button type="submit" disabled={submittingPosition} className="wolf-btn md:col-span-2 disabled:opacity-50">
              {submittingPosition ? 'СТВОРЕННЯ...' : 'СТВОРИТИ ПОЗИЦІЮ'}
            </button>
          </form>
        </section>

        <section className="wolf-panel p-5 space-y-4">
          <h2 className="wolf-title flex items-center gap-2"><ClipboardList className="w-4 h-4 text-red-400" /> НОВИЙ ЗАПИТ</h2>
          <form onSubmit={onCreateRequest} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input
              type="number"
              step="0.1"
              value={requestForm.x}
              onChange={(event) => setRequestForm((prev) => ({ ...prev, x: event.target.value }))}
              placeholder="ПООРАНЕНИЙ X"
              className="wolf-input"
              required
            />
            <input
              type="number"
              step="0.1"
              value={requestForm.y}
              onChange={(event) => setRequestForm((prev) => ({ ...prev, y: event.target.value }))}
              placeholder="ПООРАНЕНИЙ Y"
              className="wolf-input"
              required
            />
            <select
              value={requestForm.urgency}
              onChange={(event) => setRequestForm((prev) => ({ ...prev, urgency: event.target.value }))}
              className="wolf-input"
            >
              <option value="critical">CRITICAL</option>
              <option value="high">HIGH</option>
              <option value="medium">MEDIUM</option>
              <option value="low">LOW</option>
            </select>
            <input
              type="number"
              step="0.1"
              min={0.5}
              value={requestForm.radius_km}
              onChange={(event) => setRequestForm((prev) => ({ ...prev, radius_km: event.target.value }))}
              placeholder="РАДІУС (КМ)"
              className="wolf-input"
              required
            />
            <input
              type="number"
              min={0}
              value={requestForm.hemostatic}
              onChange={(event) => setRequestForm((prev) => ({ ...prev, hemostatic: event.target.value }))}
              placeholder="HEMOSTATIC"
              className="wolf-input"
            />
            <input
              type="number"
              min={0}
              value={requestForm.bandage}
              onChange={(event) => setRequestForm((prev) => ({ ...prev, bandage: event.target.value }))}
              placeholder="BANDAGE"
              className="wolf-input"
            />
            <input
              type="number"
              min={0}
              value={requestForm.tourniquet}
              onChange={(event) => setRequestForm((prev) => ({ ...prev, tourniquet: event.target.value }))}
              placeholder="TOURNIQUET"
              className="wolf-input md:col-span-2"
            />
            <button type="submit" disabled={submittingRequest} className="wolf-btn-danger md:col-span-2 disabled:opacity-50">
              {submittingRequest ? 'ФОРМУВАННЯ...' : 'СТВОРИТИ ЗАПИТ'}
            </button>
          </form>
        </section>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <section className="wolf-panel p-5 xl:col-span-2">
          <h2 className="wolf-title mb-4 flex items-center gap-2"><Package className="w-4 h-4 text-blue-400" /> ПОЗИЦІЇ ТА ІНВЕНТАР</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-[#262a30] text-[10px] text-gray-500 uppercase tracking-widest">
                  <th className="py-2 px-2 text-left">ПОЗИЦІЯ</th>
                  <th className="py-2 px-2 text-left">КООРДИНАТИ</th>
                  {TRACKED_ITEMS.map((item) => (
                    <th key={item.key} className="py-2 px-2 text-left">{item.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {positions.map((position) => (
                  <tr key={position.id} className="border-b border-[#262a30]/60 hover:bg-[#1a1d24] transition-colors">
                    <td className="py-3 px-2 font-bold text-white">{position.name}</td>
                    <td className="py-3 px-2 text-gray-400 font-mono text-xs">X:{position.x.toFixed(1)} Y:{position.y.toFixed(1)}</td>
                    {TRACKED_ITEMS.map((item) => {
                      const qty = Number(position.inventory[item.key] ?? 0)
                      const pending = inventoryPendingKey === `${position.id}:${item.key}`
                      return (
                        <td key={item.key} className="py-3 px-2">
                          <div className="inline-flex items-center gap-2 border border-[#2a2e35] bg-[#151820] px-2 py-1 rounded-sm">
                            <button
                              onClick={() => void changeInventory(position, item.key, -1)}
                              disabled={pending}
                              className="text-red-400 hover:text-red-300 disabled:opacity-40"
                              aria-label={`minus-${position.id}-${item.key}`}
                            >
                              <MinusCircle className="w-4 h-4" />
                            </button>
                            <span className="font-mono text-white min-w-6 text-center">{qty}</span>
                            <button
                              onClick={() => void changeInventory(position, item.key, 1)}
                              disabled={pending}
                              className="text-green-400 hover:text-green-300 disabled:opacity-40"
                              aria-label={`plus-${position.id}-${item.key}`}
                            >
                              <PlusCircle className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      )
                    })}
                  </tr>
                ))}
                {positions.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-5 px-2 text-center text-gray-500 uppercase tracking-widest text-xs">Немає польових позицій</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="wolf-panel p-5 space-y-4">
          <h2 className="wolf-title flex items-center gap-2"><ClipboardList className="w-4 h-4 text-amber-400" /> АКТИВНІ ЗАПИТИ</h2>
          <select
            value={selectedRequestId}
            onChange={(event) => setSelectedRequestId(event.target.value)}
            className="wolf-input"
          >
            {requests.length === 0 && <option value="">НЕМАЄ ЗАПИТІВ</option>}
            {requests.map((request) => (
              <option key={request.id} value={request.id}>
                {request.urgency.toUpperCase()} | X:{request.x.toFixed(1)} Y:{request.y.toFixed(1)}
              </option>
            ))}
          </select>

          {selectedRequest && (
            <div className="text-xs text-gray-400 font-mono border border-[#2a2e35] rounded-sm p-3 bg-[#14171d]">
              <div className="mb-1">ID: {selectedRequest.id}</div>
              <div className="mb-1">СТАТУС: {selectedRequest.status}</div>
              <div>СТВОРЕНО: {formatTime(selectedRequest.created_at)}</div>
            </div>
          )}

          <div className="border border-[#2a2e35] rounded-sm p-3 bg-[#14171d]">
            <div className="text-[10px] text-gray-500 uppercase tracking-widest mb-2">РЕКОМЕНДАЦІЯ</div>
            {!recommendation ? (
              <div className="text-xs text-gray-500 uppercase tracking-widest">Немає даних для рекомендації</div>
            ) : (
              <div className="space-y-2 text-xs">
                <div className="text-gray-300 font-mono">ETA: {recommendation.eta_min ?? 'N/A'} - {recommendation.eta_max ?? 'N/A'} хв</div>
                {recommendation.actions.map((action, index) => (
                  <div key={`${action.item_name}-${index}`} className="p-2 border border-[#2a2e35] bg-[#0f1217] rounded-sm">
                    <div className="text-white font-semibold">
                      {action.item_name.toUpperCase()} x{action.qty}
                    </div>
                    <div className="text-gray-500">
                      {action.position ? `${action.position} • ` : ''}{action.status}
                      {action.eta_min ? ` • ETA ${action.eta_min} хв` : ''}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <button
            onClick={() => void onCommitRequest()}
            disabled={committing || !selectedRequestId}
            className="wolf-btn-danger w-full disabled:opacity-50"
          >
            <Send className="w-4 h-4" /> {committing ? 'ВІДПРАВЛЕННЯ...' : 'ВІДПРАВИТИ ЗАПИТ'}
          </button>

          {radioMessages.length > 0 && (
            <div className="border border-amber-700/30 rounded-sm p-3 bg-amber-950/20">
              <div className="text-[10px] text-amber-300 uppercase tracking-widest mb-2">РАДІОПОВІДОМЛЕННЯ</div>
              <ul className="space-y-1 text-xs text-amber-100 font-mono">
                {radioMessages.map((message, index) => (
                  <li key={`${message}-${index}`}>{message}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>

      <section className="wolf-panel p-5">
        <h2 className="wolf-title mb-4 uppercase tracking-widest">ОСТАННІ ЛОГИ ВІДПРАВЛЕНЬ</h2>
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {logs.map((log) => (
            <div key={log.id} className="border border-[#262a30] bg-[#14171d] rounded-sm p-3 text-xs">
              <div className="text-white font-semibold">
                {log.item_name.toUpperCase()} x{log.qty} • {log.status}
              </div>
              <div className="text-gray-500 font-mono mt-1">
                {log.position_name ? `${log.position_name} • ` : ''}
                ETA: {log.eta_min ?? 'N/A'} хв • {formatTime(log.created_at)}
              </div>
            </div>
          ))}
          {logs.length === 0 && (
            <div className="text-xs text-gray-500 uppercase tracking-widest">Логи поки відсутні</div>
          )}
        </div>
      </section>
    </div>
  )
}
