export type TriageCategory = 'IMMEDIATE' | 'DELAYED' | 'MINIMAL' | 'EXPECTANT' | 'DECEASED'

export type MechanismOfInjury = 'BLAST' | 'GSW' | 'FRAG' | 'BURN' | 'STAB' | 'BLUNT' | 'CRUSH' | 'FALL' | 'MVC' | 'CBRN_CHEM' | 'CBRN_RAD' | 'MULTIPLE' | 'OTHER'

export type BodyRegion =
  // Head/neck
  | 'HEAD'
  | 'FACE'
  | 'NECK'
  // Thorax front/back
  | 'CHEST_ANTERIOR'
  | 'CHEST_POSTERIOR'
  | 'CHEST_LEFT_ANT'
  | 'CHEST_CENTER_ANT'
  | 'CHEST_RIGHT_ANT'
  | 'CHEST_LEFT_POST'
  | 'CHEST_CENTER_POST'
  | 'CHEST_RIGHT_POST'
  // Trunk/pelvis
  | 'ABDOMEN'
  | 'ABDOMEN_LEFT'
  | 'ABDOMEN_RIGHT'
  | 'PELVIS'
  | 'PELVIS_LEFT'
  | 'PELVIS_RIGHT'
  | 'BACK'
  | 'BACK_UPPER_LEFT'
  | 'BACK_UPPER_RIGHT'
  | 'BACK_LOWER_LEFT'
  | 'BACK_LOWER_RIGHT'
  | 'SPINE'
  // Upper limbs
  | 'L_SHOULDER'
  | 'L_UPPER_ARM'
  | 'L_ELBOW'
  | 'L_FOREARM'
  | 'L_WRIST'
  | 'L_HAND'
  | 'R_SHOULDER'
  | 'R_UPPER_ARM'
  | 'R_ELBOW'
  | 'R_FOREARM'
  | 'R_WRIST'
  | 'R_HAND'
  // Lower limbs
  | 'L_THIGH'
  | 'L_KNEE'
  | 'L_LOWER_LEG'
  | 'L_ANKLE'
  | 'L_FOOT'
  | 'R_THIGH'
  | 'R_KNEE'
  | 'R_LOWER_LEG'
  | 'R_ANKLE'
  | 'R_FOOT'

export type InjuryType = 'ENTRY_WOUND' | 'EXIT_WOUND' | 'FRAG_WOUND' | 'MASSIVE_BLEEDING' | 'BLEEDING' | 'BURN' | 'AMPUTATION' | 'OPEN_WOUND' | 'FRACTURE_SUSPECTED' | 'BRUISE_CONTUSION' | 'BLAST_INJURY' | 'CHEST_WOUND' | 'PNEUMOTHORAX_SUSPECTED' | 'OTHER'

export type Severity = 'MINOR' | 'MODERATE' | 'SEVERE' | 'CRITICAL'

export type CaseStatus = 'ACTIVE' | 'STABILIZING' | 'AWAITING_EVAC' | 'IN_TRANSPORT' | 'HANDED_OFF' | 'CLOSED' | 'DECEASED'

export interface ApiEnvelope<T> {
  data: T
  request_id?: string
}

export interface CaseItem {
  id: string
  case_number?: string | null
  callsign: string
  full_name?: string | null
  unit?: string | null
  sex?: 'MALE' | 'FEMALE' | 'UNKNOWN' | null
  approx_age?: number | null
  blood_type?: string | null
  injury_datetime?: string | null
  mechanism_of_injury?: string | null
  mechanism?: string | null
  triage_code?: string | null
  case_status: CaseStatus
  tourniquet_applied: boolean
  tourniquet_time?: string | null
  notes?: string | null
}

export interface InjuryRecord {
  id: string
  case_id?: string
  body_region: BodyRegion
  injury_type: InjuryType
  severity: Severity
  view: 'front' | 'back'
  description?: string
  penetrating?: boolean
}

export interface ObservationItem {
  id: string
  case_id: string
  heart_rate?: number | null
  respiratory_rate?: number | null
  systolic_bp?: number | null
  diastolic_bp?: number | null
  spo2_percent?: number | null
  temperature_celsius?: number | null
  measured_at?: string | null
  observation_type?: string | null
  value?: string | null
}

export interface ProcedureItem {
  id: string
  case_id: string
  procedure_code?: string | null
  notes?: string | null
}

export interface MedicationItem {
  id: string
  case_id: string
  medication_code?: string | null
  dose_value?: string | null
  dose_unit_code?: string | null
  administered_at?: string | null
}

export interface CaseDetails extends CaseItem {
  injuries: InjuryRecord[]
  observations: ObservationItem[]
  procedures: ProcedureItem[]
  sub_medications: MedicationItem[]
}

export interface AuditEntry {
  id: string
  table_name?: string | null
  row_id?: string | null
  action?: string | null
  user_id?: string | null
  created_at?: string | null
}

export interface FieldInventorySnapshot {
  hemostatic: number
  bandage: number
  tourniquet: number
  meds: Record<string, number>
}

export interface FieldPosition {
  id: string
  name: string
  x: number
  y: number
  updated_at: string
  inventory: FieldInventorySnapshot
}

export interface FieldNeed {
  item_name: string
  qty: number
}

export type FieldRequestStatus =
  | 'DRAFT'
  | 'RECOMMENDED'
  | 'DISPATCHED'
  | 'PARTIAL'
  | 'FAILED'
  | 'COMPLETED'

export interface FieldRequest {
  id: string
  x: number
  y: number
  urgency: string
  radius_km: number
  status: FieldRequestStatus
  created_at: string
  required: FieldNeed[]
}

export interface FieldRecommendationRow {
  position_id?: string | null
  position?: string | null
  item_name: string
  qty: number
  distance_km?: number | null
  score?: number | null
  eta_min?: number | null
  status: 'RECOMMENDED' | 'NOT_ENOUGH'
}

export interface FieldRecommendation {
  request_id: string
  urgency: string
  eta_min?: number | null
  eta_max?: number | null
  actions: FieldRecommendationRow[]
}

export interface FieldAppliedRow {
  position_id?: string | null
  position?: string | null
  item_name: string
  qty: number
  distance_km?: number | null
  eta_min?: number | null
  status: 'APPLIED' | 'SKIPPED' | 'FAILED'
}

export interface FieldShortage {
  item_name: string
  missing_qty: number
}

export interface FieldCommit {
  request_id: string
  ok: boolean
  already_committed: boolean
  request_status: FieldRequestStatus
  committed_at?: string | null
  applied: FieldAppliedRow[]
  shortages: FieldShortage[]
  messages: string[]
  logs_created?: number
  log_ids?: string[]
}

export type FieldDispatchLogStatus = 'APPLIED' | 'SKIPPED' | 'FAILED' | 'CREATED'

export interface FieldDispatchLog {
  id: string
  request_id: string
  position_id?: string | null
  position_name?: string | null
  item_name: string
  qty: number
  distance_km?: number | null
  eta_min?: number | null
  status: FieldDispatchLogStatus
  request_status?: FieldRequestStatus | null
  dispatched_by?: string | null
  created_at?: string | null
}
