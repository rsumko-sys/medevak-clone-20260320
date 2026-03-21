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

export interface Form100Stub {
  issued_at?: string | null
  isolation_flag?: boolean | null
  urgent_care_flag?: boolean | null
  sanitary_processing_flag?: boolean | null
}

export interface Form100FrontSideIdentity {
  rank?: string | null
  unit_name?: string | null
  full_name?: string | null
  identity_document?: string | null
  personal_number?: string | null
  sex?: string | null
}

export interface Form100BodyDiagramMark {
  wound_mark_type?: string | null
  wound_mark_location?: string | null
  wound_mark_notes?: string | null
}

export interface Form100FrontSideInjury {
  injury_or_illness_datetime?: string | null
  sanitary_loss_type?: string | null
  injury_category_codes?: string[] | null
  tourniquet_applied_at?: string | null
  diagnosis?: string | null
  injury_mechanism?: string | null
  body_diagram_marks?: Form100BodyDiagramMark[] | null
}

export interface Form100FrontSideTreatment {
  antibiotic?: string | null
  serum_pps_pgs?: string | null
  anatoxin?: string | null
  antidote?: string | null
  painkiller?: string | null
  blood_transfusion?: string | null
  blood_substitutes?: string | null
  immobilization?: string | null
  bandaging?: string | null
  sanitary_processing_type?: string | null
  treatment_notes?: string | null
}

export interface Form100FrontSideEvacuation {
  evacuation_transport?: string | null
  evacuation_destination?: string | null
  evacuation_position?: string | null
  evacuation_priority?: string | null
  recommendation_notes?: string | null
}

export interface Form100FrontSideTriageMarkers {
  red_urgent_care?: boolean | null
  yellow_sanitary_processing?: boolean | null
  black_isolation?: boolean | null
  blue_radiation_measures?: boolean | null
}

export interface Form100FrontSideBodyDiagram {
  body_diagram_marks?: Form100BodyDiagramMark[] | null
  placeholder_model?: string | null
}

export interface Form100FrontSide {
  identity?: Form100FrontSideIdentity | null
  injury?: Form100FrontSideInjury | null
  treatment?: Form100FrontSideTreatment | null
  evacuation?: Form100FrontSideEvacuation | null
  triage_markers?: Form100FrontSideTriageMarkers | null
  body_diagram?: Form100FrontSideBodyDiagram | null
}

export interface Form100BackSideStageEntry {
  arrived_at?: string | null
  stage_name?: string | null
  physician_notes?: string | null
  refined_diagnosis?: string | null
  self_exited?: boolean | null
  carried_by?: string | null
  care_provided?: string | null
  time_after_injury?: string | null
  first_aid_provided?: string | null
  evacuate_to_when?: string | null
  result?: string | null
}

export interface Form100BackSideSignature {
  physician_name?: string | null
  physician_signature?: string | null
  signed_at?: string | null
}

export interface Form100BackSide {
  stage_log?: Form100BackSideStageEntry[] | null
  signature?: Form100BackSideSignature | null
}

export interface Form100MetaLegalRules {
  legal_status?: string | null
  first_eme_completed?: boolean | null
  continuity_required?: boolean | null
  commander_notified?: boolean | null
  additional_notes?: string | null
}

export interface Form100Record {
  id: string
  case_id: string
  document_number: string
  injury_datetime: string
  injury_location: string
  injury_mechanism: string
  diagnosis_summary: string
  documented_by: string
  treatment_summary?: string | null
  evacuation_recommendation?: string | null
  commander_notified?: boolean | null
  notes?: string | null
  stub?: Form100Stub | null
  front_side?: Form100FrontSide | null
  back_side?: Form100BackSide | null
  meta_legal_rules?: Form100MetaLegalRules | null
  created_at?: string | null
  updated_at?: string | null
}

export interface CaseDetails extends CaseItem {
  injuries: InjuryRecord[]
  observations: ObservationItem[]
  procedures: ProcedureItem[]
  sub_medications: MedicationItem[]
  form100?: Form100Record | null
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

export type FieldFinalizeMethod = 'RADIO' | 'DISCORD' | 'VOICE' | 'MANUAL'

export interface FieldFinalizeResponse {
  request_id: string
  ok: boolean
  previous_status: FieldRequestStatus
  request_status: 'COMPLETED'
  finalized_at: string | null
  finalized_by: string | null
  method: FieldFinalizeMethod
  note?: string | null
}

export interface FieldRequest {
  id: string
  x: number
  y: number
  urgency: string
  radius_km: number
  status: FieldRequestStatus
  created_at: string
  required: FieldNeed[]
  finalized_at?: string | null
  finalized_by?: string | null
  finalize_method?: string | null
  finalize_note?: string | null
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
