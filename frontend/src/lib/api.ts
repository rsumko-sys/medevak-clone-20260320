import { ApiEnvelope, AuditEntry, BloodInventoryItem, CaseDetails, CaseItem, TriageCategory } from './types'

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

// ── Auth token management ──────────────────────────────────────────────────
const TOKEN_KEY = 'medevak_access_token'
const REFRESH_KEY = 'medevak_refresh_token'

function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null
  return (
    localStorage.getItem(TOKEN_KEY) ||
    localStorage.getItem('syncAuthToken') ||
    sessionStorage.getItem('syncAuthToken') ||
    null
  )
}

function buildAuthHeaders(): Record<string, string> {
  const token = getAccessToken()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) {
    headers['Authorization'] = token.startsWith('Bearer ') ? token : `Bearer ${token}`
  }
  return headers
}

async function tryRefreshToken(): Promise<boolean> {
  if (typeof window === 'undefined') return false
  const refresh = localStorage.getItem(REFRESH_KEY)
  if (!refresh) return false
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    })
    if (!res.ok) return false
    const json = await res.json()
    const newToken: string | undefined = json.data?.access_token
    if (newToken) {
      localStorage.setItem(TOKEN_KEY, newToken)
      return true
    }
    return false
  } catch {
    return false
  }
}

function buildUploadAuthHeaders(): Record<string, string> {
  const token = getAccessToken()
  if (!token) return {}
  return { Authorization: token.startsWith('Bearer ') ? token : `Bearer ${token}` }
}

// Public auth helpers (used by login page, navbar, etc.)
export async function login(email: string, password: string): Promise<{ id: string; email: string; role: string }> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as any)?.detail || `${res.status} ${res.statusText}`)
  }
  const json = await res.json()
  const { access_token, refresh_token, user } = json.data
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, access_token)
    if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token)
    // Session indicator for middleware (not the JWT itself)
    document.cookie = 'medevak_auth=1; path=/; SameSite=Strict'
  }
  return user
}

export function logout(): void {
  if (typeof window !== 'undefined') {
    const refreshToken = localStorage.getItem(REFRESH_KEY)
    // Blacklist the refresh token server-side (fire-and-forget)
    if (refreshToken) {
      const accessToken = localStorage.getItem(TOKEN_KEY)
      fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      }).catch(() => {/* best-effort — proceed with local cleanup regardless */})
    }
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
    document.cookie = 'medevak_auth=; path=/; max-age=0; SameSite=Strict'
  }
}

export function isAuthenticated(): boolean {
  return !!getAccessToken()
}
// ───────────────────────────────────────────────────────────────────────────

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
  let res = await fetch(`${API_BASE}${path}`, { cache: 'no-store', headers: buildAuthHeaders() })
  if (res.status === 401) {
    const refreshed = await tryRefreshToken()
    if (!refreshed) {
      logout()
      if (typeof window !== 'undefined') window.location.href = '/login'
      throw new Error('401 Session expired — please log in again')
    }
    res = await fetch(`${API_BASE}${path}`, { cache: 'no-store', headers: buildAuthHeaders() })
  }
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  const json: ApiEnvelope<T> = await res.json()
  return json.data
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  let res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: buildAuthHeaders(),
    body: JSON.stringify(body),
  })
  if (res.status === 401) {
    const refreshed = await tryRefreshToken()
    if (!refreshed) {
      logout()
      if (typeof window !== 'undefined') window.location.href = '/login'
      throw new Error('401 Session expired — please log in again')
    }
    res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: buildAuthHeaders(),
      body: JSON.stringify(body),
    })
  }
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  const json: ApiEnvelope<T> = await res.json()
  return json.data
}

async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  let res = await fetch(`${API_BASE}${path}`, {
    method: 'PATCH',
    headers: buildAuthHeaders(),
    body: JSON.stringify(body),
  })
  if (res.status === 401) {
    const refreshed = await tryRefreshToken()
    if (!refreshed) {
      logout()
      if (typeof window !== 'undefined') window.location.href = '/login'
      throw new Error('401 Session expired — please log in again')
    }
    res = await fetch(`${API_BASE}${path}`, {
      method: 'PATCH',
      headers: buildAuthHeaders(),
      body: JSON.stringify(body),
    })
  }
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

export async function getBloodInventory() {
  return apiGet<BloodInventoryItem[]>('/blood')
}

export async function adjustBloodInventory(bloodType: string, payload: { delta: number; reason: string; case_id?: string }) {
  return apiPatch<BloodInventoryItem>(`/blood/${encodeURIComponent(bloodType)}`, payload)
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
    headers: buildUploadAuthHeaders(),
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
