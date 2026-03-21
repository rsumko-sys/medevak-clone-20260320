import {
  ApiEnvelope,
  AuditEntry,
  CaseDetails,
  CaseItem,
  FieldCommit,
  FieldDispatchLog,
  FieldNeed,
  FieldPosition,
  FieldRecommendation,
  FieldRequest,
  TriageCategory,
} from './types'

const getApiBase = () => {
  if (process.env.NEXT_PUBLIC_API_BASE) return process.env.NEXT_PUBLIC_API_BASE
  if (typeof window !== 'undefined') {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    if (isLocal) {
      return 'http://localhost:8000/api'
    }
  }
  return '/api'
}

const API_BASE = getApiBase()

export type VitalsPayload = {
  heart_rate?: number | string
  respiratory_rate?: number | string
  systolic_bp?: number | string
  diastolic_bp?: number | string
  spo2_percent?: number | string
  temperature_celsius?: number | string
}

export type SyncStats = {
  pending: number
  acked: number
  dead_letter: number
  synced?: number
  failed?: number
}

export type SecurityPolicySettings = {
  private_network_only: boolean
  allow_gps: boolean
  network_mode: 'private_only' | 'open'
  gps_mode: 'enabled' | 'disabled'
}

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  const json: ApiEnvelope<T> = await res.json()
  return json.data
}

async function apiPost<T>(path: string, body: unknown, options?: { headers?: Record<string, string> }): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(options?.headers ?? {}) },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  const json: ApiEnvelope<T> = await res.json()
  return json.data
}

async function apiPatch<T>(path: string, body: unknown, options?: { headers?: Record<string, string> }): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...(options?.headers ?? {}) },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  const json: ApiEnvelope<T> = await res.json()
  return json.data
}

export async function listCases() {
  return apiGet<CaseItem[]>('/cases')
}

export async function updateCase(caseId: string, payload: Partial<CaseItem>) {
  return apiPatch<CaseItem>(`/cases/${caseId}`, payload)
}

export async function createCase(payload: any) {
  return apiPost<CaseItem>('/cases', payload)
}

export async function getCase(caseId: string) {
  return apiGet<CaseDetails>(`/cases/${caseId}`)
}

export async function addInjury(caseId: string, payload: any) {
  return apiPost(`/cases/${caseId}/injuries`, payload)
}

export async function addObservation(caseId: string, payload: VitalsPayload) {
  return apiPost(`/cases/${caseId}/vitals`, payload)
}

export async function addProcedure(caseId: string, payload: { procedure_code: string; notes?: string }) {
  return apiPost(`/cases/${caseId}/procedures`, payload)
}

export async function addMedication(
  case_id: string,
  payload: { medication_code: string; dose_value?: string; dose_unit_code?: string; time_administered?: string }
) {
  return apiPost(`/cases/${case_id}/medications`, payload)
}

export async function addMarch(case_id: string, payload: any) {
  return apiPost(`/cases/${case_id}/march`, payload)
}

export async function upsertEvacuation(case_id: string, payload: any) {
  return apiPost(`/cases/${case_id}/evacuation`, payload)
}

export async function getMistSummary(case_id: string) {
  return apiGet<{ mist_summary: string }>(`/cases/${case_id}/mist`)
}

export async function addEvent(caseId: string, payload: {
  event_type: string
  event_time?: string
  payload?: unknown
}) {
  return apiPost(`/cases/${caseId}/events`, payload)
}

export async function listAudit() {
  return apiGet<AuditEntry[]>('/audit?limit=100')
}

export async function getSyncStats() {
  return apiGet<SyncStats>('/sync/stats')
}

export async function getSyncQueue() {
  return apiGet<any[]>('/sync/queue')
}

export async function transcribeAudio(file: File, whisperApiKey: string) {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${API_BASE}/transcribe`, {
    method: 'POST',
    headers: {
      'X-Whisper-Key': whisperApiKey,
    },
    body: formData,
  })

  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  const json = await res.json()
  return (json?.text || '').toString().trim()
}

export async function getReference() {
  return apiGet<{ triage_codes: string[]; blood_codes: string[] }>('/reference')
}

export async function listDocuments() {
  return apiGet<any[]>('/documents')
}

export async function getSecurityPolicySettings() {
  return apiGet<SecurityPolicySettings>('/settings/security-policy')
}

export async function uploadDocument(caseId: string, documentType: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  if (caseId) formData.append('case_id', caseId)
  formData.append('document_type', documentType)

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  const json = await res.json()
  return json.data
}

export function exportPdfUrl(caseId: string) {
  return `${API_BASE}/exports/${caseId}/pdf`
}

export function exportFhirUrl(caseId: string) {
  return `${API_BASE}/exports/${caseId}/fhir`
}

export function exportQrUrl(caseId: string) {
  return `${API_BASE}/exports/${caseId}/qr`
}

export async function listFieldDropPositions() {
  return apiGet<FieldPosition[]>('/field-drop/positions')
}

export async function createFieldDropPosition(payload: {
  name: string
  x: number
  y: number
  inventory: {
    hemostatic: number
    bandage: number
    tourniquet: number
    meds?: Record<string, number>
  }
}, idempotencyKey?: string) {
  return apiPost<FieldPosition>('/field-drop/positions', {
    ...payload,
    inventory: {
      hemostatic: payload.inventory.hemostatic,
      bandage: payload.inventory.bandage,
      tourniquet: payload.inventory.tourniquet,
      meds: payload.inventory.meds ?? {},
    },
  }, idempotencyKey ? { headers: { 'Idempotency-Key': idempotencyKey } } : undefined)
}

export async function updateFieldDropInventory(
  positionId: string,
  item_name: string,
  qty: number,
  idempotencyKey?: string,
) {
  return apiPatch<{ position_id: string; item_name: string; qty: number }>(
    `/field-drop/positions/${positionId}/inventory`,
    { item_name, qty },
    idempotencyKey ? { headers: { 'Idempotency-Key': idempotencyKey } } : undefined,
  )
}

export async function listFieldDropRequests() {
  return apiGet<FieldRequest[]>('/field-drop/requests')
}

export async function createFieldDropRequest(payload: {
  x: number
  y: number
  urgency: string
  radius_km: number
  required: FieldNeed[]
}, idempotencyKey?: string) {
  return apiPost<FieldRequest>(
    '/field-drop/requests',
    payload,
    idempotencyKey ? { headers: { 'Idempotency-Key': idempotencyKey } } : undefined,
  )
}

export async function getFieldDropRecommendation(requestId: string) {
  return apiGet<FieldRecommendation>(`/field-drop/requests/${requestId}/recommendation`)
}

export async function commitFieldDropRequest(requestId: string, idempotencyKey?: string) {
  return apiPost<FieldCommit>(
    `/field-drop/requests/${requestId}/commit`,
    {},
    idempotencyKey ? { headers: { 'Idempotency-Key': idempotencyKey } } : undefined,
  )
}

export async function listFieldDropLogs(limit = 20) {
  return apiGet<FieldDispatchLog[]>(`/field-drop/logs?limit=${limit}`)
}
