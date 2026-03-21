import test from 'node:test'
import assert from 'node:assert/strict'

import { buildDraftFromForm100, buildPayloadFromDraft } from './form100-ui-sync.js'

test('Form100 UI sync roundtrip keeps canonical nested sections for save/load/display', () => {
  const source = {
    id: 'f100-1',
    case_id: 'case-1',
    document_number: 'F100-UI-01',
    injury_datetime: '2026-03-21T10:15:00Z',
    injury_location: 'Sector D',
    injury_mechanism: 'BLAST',
    diagnosis_summary: 'Polytrauma',
    documented_by: 'Medic-04',
    commander_notified: true,
    notes: 'note',
    stub: {
      issued_at: '2026-03-21T10:20:00Z',
      urgent_care_flag: true,
      sanitary_processing_flag: true,
      isolation_flag: false,
    },
    front_side: {
      injury: {
        injury_or_illness_datetime: '2026-03-21T10:15:00Z',
        diagnosis: 'Polytrauma',
        injury_mechanism: 'BLAST',
        body_diagram_marks: [
          {
            wound_mark_type: 'entry',
            wound_mark_location: 'Left arm',
            wound_mark_notes: 'mark',
          },
        ],
      },
      evacuation: {
        evacuation_transport: 'MEDEVAC',
        evacuation_destination: 'Role 2',
        evacuation_position: 'lying',
        evacuation_priority: 'urgent',
      },
      triage_markers: {
        red_urgent_care: true,
        yellow_sanitary_processing: false,
        black_isolation: true,
        blue_radiation_measures: false,
      },
      body_diagram: {
        placeholder_model: 'TODO:graphic-model-pending',
      },
    },
    back_side: {
      stage_log: [
        { stage_name: 'ROLE_1', result: 'stable' },
        { stage_name: 'ROLE_2', result: 'evacuate' },
      ],
      signature: {
        physician_name: 'Medic-04',
      },
    },
    meta_legal_rules: {
      legal_status: 'official',
      first_eme_completed: true,
      continuity_required: true,
    },
  }

  const draft = buildDraftFromForm100(source)
  assert.equal(draft.document_number, 'F100-UI-01')
  assert.equal(draft.triage_red_urgent_care, true)
  assert.equal(draft.evacuation_destination, 'Role 2')
  assert.ok(draft.stage_log_text.includes('ROLE_2'))

  const payload = buildPayloadFromDraft(draft)
  assert.equal(payload.document_number, 'F100-UI-01')
  assert.equal(payload.front_side.triage_markers.red_urgent_care, true)
  assert.equal(payload.front_side.evacuation.evacuation_destination, 'Role 2')
  assert.equal(Array.isArray(payload.back_side.stage_log), true)
  assert.equal(payload.back_side.stage_log.length, 2)
  assert.equal(payload.meta_legal_rules.continuity_required, true)
})
