export function emptyForm100Draft() {
  return {
    document_number: '',
    injury_datetime: '',
    injury_location: '',
    injury_mechanism: '',
    diagnosis_summary: '',
    documented_by: '',
    treatment_summary: '',
    evacuation_recommendation: '',
    commander_notified: false,
    notes: '',

    stub_issued_at: '',
    stub_isolation_flag: false,
    stub_urgent_care_flag: false,
    stub_sanitary_processing_flag: false,

    triage_red_urgent_care: false,
    triage_yellow_sanitary_processing: false,
    triage_black_isolation: false,
    triage_blue_radiation_measures: false,

    evacuation_transport: '',
    evacuation_destination: '',
    evacuation_position: '',
    evacuation_priority: '',

    body_diagram_placeholder_model: '',
    body_mark_type: '',
    body_mark_location: '',
    body_mark_notes: '',

    stage_log_text: '[]',

    legal_status: '',
    first_eme_completed: false,
    continuity_required: false,
  }
}

function toLocalDatetimeInput(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  return d.toISOString().slice(0, 16)
}

function toIso(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  return d.toISOString()
}

export function buildDraftFromForm100(form100) {
  if (!form100) return emptyForm100Draft()

  const draft = emptyForm100Draft()
  const injury = form100.front_side?.injury || {}
  const treatment = form100.front_side?.treatment || {}
  const evacuation = form100.front_side?.evacuation || {}
  const triage = form100.front_side?.triage_markers || {}
  const body = form100.front_side?.body_diagram || {}
  const bodyMarks = injury.body_diagram_marks || body.body_diagram_marks || []
  const firstMark = Array.isArray(bodyMarks) ? (bodyMarks[0] || {}) : {}
  const signature = form100.back_side?.signature || {}
  const legal = form100.meta_legal_rules || {}
  const stageLog = Array.isArray(form100.back_side?.stage_log) ? form100.back_side.stage_log : []

  draft.document_number = form100.document_number || ''
  draft.injury_datetime = toLocalDatetimeInput(form100.injury_datetime || injury.injury_or_illness_datetime)
  draft.injury_location = form100.injury_location || firstMark.wound_mark_location || ''
  draft.injury_mechanism = form100.injury_mechanism || injury.injury_mechanism || ''
  draft.diagnosis_summary = form100.diagnosis_summary || injury.diagnosis || ''
  draft.documented_by = form100.documented_by || signature.physician_name || ''
  draft.treatment_summary = form100.treatment_summary || treatment.treatment_notes || ''
  draft.evacuation_recommendation = form100.evacuation_recommendation || evacuation.recommendation_notes || ''
  draft.commander_notified = !!form100.commander_notified
  draft.notes = form100.notes || legal.additional_notes || ''

  draft.stub_issued_at = toLocalDatetimeInput(form100.stub?.issued_at)
  draft.stub_isolation_flag = !!form100.stub?.isolation_flag
  draft.stub_urgent_care_flag = !!form100.stub?.urgent_care_flag
  draft.stub_sanitary_processing_flag = !!form100.stub?.sanitary_processing_flag

  draft.triage_red_urgent_care = !!triage.red_urgent_care
  draft.triage_yellow_sanitary_processing = !!triage.yellow_sanitary_processing
  draft.triage_black_isolation = !!triage.black_isolation
  draft.triage_blue_radiation_measures = !!triage.blue_radiation_measures

  draft.evacuation_transport = evacuation.evacuation_transport || ''
  draft.evacuation_destination = evacuation.evacuation_destination || ''
  draft.evacuation_position = evacuation.evacuation_position || ''
  draft.evacuation_priority = evacuation.evacuation_priority || ''

  draft.body_diagram_placeholder_model = body.placeholder_model || ''
  draft.body_mark_type = firstMark.wound_mark_type || ''
  draft.body_mark_location = firstMark.wound_mark_location || ''
  draft.body_mark_notes = firstMark.wound_mark_notes || ''

  draft.stage_log_text = JSON.stringify(stageLog, null, 2)

  draft.legal_status = legal.legal_status || ''
  draft.first_eme_completed = !!legal.first_eme_completed
  draft.continuity_required = !!legal.continuity_required

  return draft
}

export function buildPayloadFromDraft(draft) {
  let parsedStageLog = []
  if (draft.stage_log_text && draft.stage_log_text.trim()) {
    try {
      const candidate = JSON.parse(draft.stage_log_text)
      parsedStageLog = Array.isArray(candidate) ? candidate : []
    } catch {
      parsedStageLog = []
    }
  }

  const mark = {
    wound_mark_type: draft.body_mark_type || undefined,
    wound_mark_location: draft.body_mark_location || undefined,
    wound_mark_notes: draft.body_mark_notes || undefined,
  }
  const hasMark = !!(mark.wound_mark_type || mark.wound_mark_location || mark.wound_mark_notes)
  const injuryDatetimeIso = toIso(draft.injury_datetime)
  const issuedAtIso = toIso(draft.stub_issued_at)

  return {
    document_number: draft.document_number,
    injury_datetime: injuryDatetimeIso,
    injury_location: draft.injury_location,
    injury_mechanism: draft.injury_mechanism,
    diagnosis_summary: draft.diagnosis_summary,
    documented_by: draft.documented_by,
    treatment_summary: draft.treatment_summary || undefined,
    evacuation_recommendation: draft.evacuation_recommendation || undefined,
    commander_notified: !!draft.commander_notified,
    notes: draft.notes || undefined,
    stub: {
      issued_at: issuedAtIso || undefined,
      isolation_flag: !!draft.stub_isolation_flag,
      urgent_care_flag: !!draft.stub_urgent_care_flag,
      sanitary_processing_flag: !!draft.stub_sanitary_processing_flag,
    },
    front_side: {
      injury: {
        injury_or_illness_datetime: injuryDatetimeIso || undefined,
        diagnosis: draft.diagnosis_summary || undefined,
        injury_mechanism: draft.injury_mechanism || undefined,
        body_diagram_marks: hasMark ? [mark] : [],
      },
      treatment: {
        treatment_notes: draft.treatment_summary || undefined,
      },
      evacuation: {
        evacuation_transport: draft.evacuation_transport || undefined,
        evacuation_destination: draft.evacuation_destination || undefined,
        evacuation_position: draft.evacuation_position || undefined,
        evacuation_priority: draft.evacuation_priority || undefined,
        recommendation_notes: draft.evacuation_recommendation || undefined,
      },
      triage_markers: {
        red_urgent_care: !!draft.triage_red_urgent_care,
        yellow_sanitary_processing: !!draft.triage_yellow_sanitary_processing,
        black_isolation: !!draft.triage_black_isolation,
        blue_radiation_measures: !!draft.triage_blue_radiation_measures,
      },
      body_diagram: {
        placeholder_model: draft.body_diagram_placeholder_model || undefined,
        body_diagram_marks: hasMark ? [mark] : [],
      },
    },
    back_side: {
      stage_log: parsedStageLog,
      signature: {
        physician_name: draft.documented_by || undefined,
      },
    },
    meta_legal_rules: {
      legal_status: draft.legal_status || undefined,
      first_eme_completed: !!draft.first_eme_completed,
      continuity_required: !!draft.continuity_required,
      commander_notified: !!draft.commander_notified,
      additional_notes: draft.notes || undefined,
    },
  }
}
