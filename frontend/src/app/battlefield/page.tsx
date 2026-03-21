'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import Link from 'next/link'
import { Mic, ArrowLeft, Save, X } from 'lucide-react'
import { createCase, addMarch, addObservation, upsertEvacuation, getMistSummary, addMedication, addProcedure, addEvent, transcribeAudio, VitalsPayload } from '@/lib/api'
import { MechanismOfInjury, TriageCategory, BodyRegion, InjuryType, Severity, InjuryRecord } from '@/lib/types'
import { useToast } from '@/components/Toast'
import BodyMap from '@/components/BodyMap'
import { BODY_ZONES, INJURY_ICONS } from '@/lib/constants'
import MarchForm from '@/components/MarchForm'
import VitalsForm from '@/components/VitalsForm'
import EvacForm from '@/components/EvacForm'

const TABS = [
  { id: 'S1', name: '1. ВВЕДЕННЯ' },
  { id: 'S2', name: '2. КАРТА ТІЛА' },
  { id: 'S3', name: '3. M.A.R.C.H' },
  { id: 'S4', name: '4. ДІЇ / ВІТАЛЬНІ' },
  { id: 'S5', name: '5. ЕВАК' }
]

const MARCH_DEFAULT = {
  m_tourniquets_applied: 0,
  a_airway_open: true,
  a_airway_intervention: 'INTACT',
  c_radial_pulse: 'Radial',
}

const EVAC_DEFAULT = { evacuation_priority: 'ROUTINE' }

type StepProgressState = 'not_started' | 'in_progress' | 'done'

const STEP_STATE_META: Record<StepProgressState, { label: string; dotClass: string; textClass: string }> = {
  not_started: {
    label: 'не розпочато',
    dotClass: 'bg-gray-600',
    textClass: 'text-gray-500',
  },
  in_progress: {
    label: 'в процесі',
    dotClass: 'bg-amber-500 animate-pulse',
    textClass: 'text-amber-400',
  },
  done: {
    label: 'завершено',
    dotClass: 'bg-green-500',
    textClass: 'text-green-400',
  },
}

export default function BattlefieldPage() {
  const toast = useToast()
  const [activeTab, setActiveTab] = useState('S1')
  const [isRecording, setIsRecording] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [recordingLabel, setRecordingLabel] = useState('')
  const [isWhisperConfigured, setIsWhisperConfigured] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<BlobPart[]>([])
  
  // S1 State
  const [callsign, setCallsign] = useState('')
  const [fullName, setFullName] = useState('')
  const [unit, setUnit] = useState('')
  const [injuryTime, setInjuryTime] = useState('')
  const [triageCat, setTriageCat] = useState<TriageCategory>('IMMEDIATE')
  const [mechanisms, setMechanisms] = useState<MechanismOfInjury[]>([])
  const [tourniquetApplied, setTourniquetApplied] = useState(false)
  const [tourniquetTime, setTourniquetTime] = useState('')
  const [intakeNotes, setIntakeNotes] = useState('')

  // S2 State
  const [activeView, setActiveView] = useState<'front' | 'back'>('front')
  const [injuries, setInjuries] = useState<InjuryRecord[]>([])
  const [selectedZoneId, setSelectedZoneId] = useState<BodyRegion | null>(null)
  
  // Sheet Form State
  const [sheetInjuryType, setSheetInjuryType] = useState<InjuryType>('ENTRY_WOUND')
  const [sheetSeverity, setSheetSeverity] = useState<Severity>('MODERATE')

  // S3-S5 State
  const [marchData, setMarchData] = useState<any>({
    ...MARCH_DEFAULT,
  })
  const [vitalsData, setVitalsData] = useState<any>({})
  const [evacData, setEvacData] = useState<any>({ ...EVAC_DEFAULT })
  const [mistSummary, setMistSummary] = useState('')
  const [savedCaseId, setSavedCaseId] = useState<string | null>(null)
  const [quickMedications, setQuickMedications] = useState<string[]>([])
  const [quickProcedures, setQuickProcedures] = useState<string[]>([])
  const [pendingVoiceEvents, setPendingVoiceEvents] = useState<string[]>([])
  const [isMarkerSaving, setIsMarkerSaving] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  const tabIds = TABS.map((t) => t.id)
  const currentTabIndex = tabIds.indexOf(activeTab)
  const canGoPrev = currentTabIndex > 0
  const canGoNext = currentTabIndex >= 0 && currentTabIndex < tabIds.length - 1

  const goPrevTab = () => {
    if (!canGoPrev) return
    setActiveTab(tabIds[currentTabIndex - 1])
  }

  const validateStep = (stepId: string): { valid: boolean; error: string } => {
    const nextFieldErrors: Record<string, string> = {}
    const clearedFields: Record<string, string> = {}
    let stepError = ''

    if (stepId === 'S1') {
      clearedFields.callsign = ''
      clearedFields.mechanisms = ''
      if (!callsign.trim()) {
        nextFieldErrors.callsign = 'Вкажіть позивний'
      }
      if (mechanisms.length === 0) {
        nextFieldErrors.mechanisms = 'Оберіть хоча б один механізм травми'
      }
      if (Object.keys(nextFieldErrors).length > 0) {
        stepError = 'Заповніть обовʼязкові поля на кроці 1'
      }
    }

    if (stepId === 'S2' && injuries.length === 0) {
      clearedFields.injuries = ''
      nextFieldErrors.injuries = 'Додайте щонайменше одну травму на карті тіла'
      stepError = 'Додайте травму перед переходом далі'
    }

    if (stepId === 'S2' && injuries.length > 0) {
      clearedFields.injuries = ''
    }

    if (stepId === 'S5' && !evacData.destination?.trim()) {
      clearedFields.destination = ''
      nextFieldErrors.destination = 'Вкажіть пункт призначення'
      stepError = 'Заповніть пункт призначення'
    }

    if (stepId === 'S5' && evacData.destination?.trim()) {
      clearedFields.destination = ''
    }

    setFieldErrors((prev) => ({ ...prev, ...clearedFields, ...nextFieldErrors }))
    return { valid: stepError === '', error: stepError }
  }

  const goToTab = (tabId: string) => {
    const targetIndex = tabIds.indexOf(tabId)
    if (targetIndex === -1) return
    if (targetIndex <= currentTabIndex) {
      setActiveTab(tabId)
      return
    }

    for (let index = currentTabIndex; index < targetIndex; index += 1) {
      const gateStep = tabIds[index]
      const validation = validateStep(gateStep)
      if (!validation.valid) {
        setActiveTab(gateStep)
        toast.error(validation.error || 'Заповніть обовʼязкові поля перед переходом')
        return
      }
    }

    setActiveTab(tabId)
  }

  const goNextTab = () => {
    if (!canGoNext) return
    const validation = validateStep(activeTab)
    if (!validation.valid) {
      toast.error(validation.error || 'Заповніть обовʼязкові поля перед переходом')
      return
    }
    setActiveTab(tabIds[currentTabIndex + 1])
  }

  useEffect(() => {
    if (typeof window === 'undefined') return
    const raw = window.localStorage.getItem('battlefieldDraft')
    if (!raw) return
    try {
      const draft = JSON.parse(raw)
      setCallsign(draft.callsign || '')
      setFullName(draft.fullName || '')
      setUnit(draft.unit || '')
      setInjuryTime(draft.injuryTime || '')
      setTriageCat(draft.triageCat || 'IMMEDIATE')
      setMechanisms(Array.isArray(draft.mechanisms) ? draft.mechanisms : [])
      setTourniquetApplied(!!draft.tourniquetApplied)
      setTourniquetTime(draft.tourniquetTime || '')
      setIntakeNotes(draft.intakeNotes || '')
      setInjuries(Array.isArray(draft.injuries) ? draft.injuries : [])
      setMarchData(draft.marchData || { ...MARCH_DEFAULT })
      setVitalsData(draft.vitalsData || {})
      setEvacData(draft.evacData || { ...EVAC_DEFAULT })
      setQuickMedications(Array.isArray(draft.quickMedications) ? draft.quickMedications : [])
      setQuickProcedures(Array.isArray(draft.quickProcedures) ? draft.quickProcedures : [])
    } catch {
      window.localStorage.removeItem('battlefieldDraft')
    }
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const draft = {
      callsign,
      fullName,
      unit,
      injuryTime,
      triageCat,
      mechanisms,
      tourniquetApplied,
      tourniquetTime,
      intakeNotes,
      injuries,
      marchData,
      vitalsData,
      evacData,
      quickMedications,
      quickProcedures,
    }
    window.localStorage.setItem('battlefieldDraft', JSON.stringify(draft))
  }, [
    callsign,
    fullName,
    unit,
    injuryTime,
    triageCat,
    mechanisms,
    tourniquetApplied,
    tourniquetTime,
    intakeNotes,
    injuries,
    marchData,
    vitalsData,
    evacData,
    quickMedications,
    quickProcedures,
  ])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const refreshWhisperConfig = () => {
      const key = (window.sessionStorage.getItem('whisperApiKey') || '').trim()
      setIsWhisperConfigured(Boolean(key))
    }

    refreshWhisperConfig()
    window.addEventListener('focus', refreshWhisperConfig)
    return () => window.removeEventListener('focus', refreshWhisperConfig)
  }, [])

  const toggleMechanism = (mech: MechanismOfInjury) => {
    if (mechanisms.includes(mech)) {
      setMechanisms(mechanisms.filter(m => m !== mech))
    } else {
      setMechanisms([...mechanisms, mech])
    }
  }

  const handleZoneClick = (zoneId: BodyRegion) => {
    setSelectedZoneId(zoneId)
  }

  const saveMarker = () => {
    if (!selectedZoneId || isMarkerSaving) return
    setIsMarkerSaving(true)
    const newInjury: InjuryRecord = {
      id: Math.random().toString(36).substr(2, 9),
      body_region: selectedZoneId,
      injury_type: sheetInjuryType,
      severity: sheetSeverity,
      view: activeView,
      penetrating: false
    }
    setInjuries((prev) => [...prev, newInjury])
    setSelectedZoneId(null)
    toast.success('Маркер збережено')
    window.setTimeout(() => setIsMarkerSaving(false), 250)
  }

  const handleAddAction = (type: 'medication' | 'procedure', code: string) => {
    if (type === 'medication') {
      setQuickMedications((prev) => [...prev, code])
    } else {
      setQuickProcedures((prev) => [...prev, code])
    }
    toast.success(`Позначено: ${code}`)
  }

  const applyTriageHintsFromTranscript = (text: string) => {
    const normalized = text.toLowerCase()
    if (normalized.includes('невідклад') || normalized.includes('критич') || normalized.includes('red')) {
      setTriageCat('IMMEDIATE')
      return
    }
    if (normalized.includes('відстроч') || normalized.includes('yellow')) {
      setTriageCat('DELAYED')
      return
    }
    if (normalized.includes('мінім') || normalized.includes('green')) {
      setTriageCat('MINIMAL')
      return
    }
    if (normalized.includes('очікуван') || normalized.includes('black')) {
      setTriageCat('EXPECTANT')
    }
  }

  const handleMicClick = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop()
      setIsRecording(false)
      setRecordingLabel('Обробка транскрипції...')
      return
    }

    const whisperKey = (typeof window !== 'undefined' ? (sessionStorage.getItem('whisperApiKey') || '').trim() : '')
    if (!whisperKey) {
      setIsWhisperConfigured(false)
      setRecordingLabel('Whisper ключ не налаштовано')
      toast.info('Щоб увімкнути голосовий ввід, додайте whisperApiKey у Налаштуваннях')
      return
    }
    setIsWhisperConfigured(true)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      audioChunksRef.current = []

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      recorder.onstop = async () => {
        try {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })

          const audioFile = new File([audioBlob], `voice-${Date.now()}.webm`, { type: 'audio/webm' })
          const transcript = await transcribeAudio(audioFile, whisperKey)
          if (transcript) {
            setIntakeNotes((prev) => (prev ? `${prev}\n${transcript}` : transcript))
            setPendingVoiceEvents((prev) => [...prev, transcript])
            applyTriageHintsFromTranscript(transcript)
            toast.success('Голосовий запис транскрибовано')
          } else {
            toast.info('Порожня транскрипція')
          }
        } catch (error) {
          console.error(error)
          toast.error('Помилка транскрипції')
        } finally {
          setRecordingLabel('')
          stream.getTracks().forEach((track) => track.stop())
        }
      }

      mediaRecorderRef.current = recorder
      recorder.start()
      setIsRecording(true)
      setRecordingLabel('Йде запис...')
    } catch (error) {
      console.error(error)
      toast.error('Не вдалося розпочати аудіозапис')
    }
  }

  const normalizeVitalsPayload = (rawVitals: any): VitalsPayload => {
    const toNumber = (value: unknown) => {
      if (value === '' || value === null || value === undefined) return undefined
      const parsed = Number(value)
      return Number.isFinite(parsed) ? parsed : undefined
    }

    return {
      heart_rate: toNumber(rawVitals.heart_rate),
      respiratory_rate: toNumber(rawVitals.respiratory_rate),
      systolic_bp: toNumber(rawVitals.systolic_bp),
      diastolic_bp: toNumber(rawVitals.diastolic_bp),
      spo2_percent: toNumber(rawVitals.spo2_percent),
      temperature_celsius: toNumber(rawVitals.temperature_celsius),
    }
  }

  const startNewDraft = () => {
    setCallsign('')
    setFullName('')
    setUnit('')
    setInjuryTime('')
    setTourniquetApplied(false)
    setTourniquetTime('')
    setIntakeNotes('')
    setInjuries([])
    setVitalsData({})
    setMarchData({ ...MARCH_DEFAULT })
    setEvacData({ ...EVAC_DEFAULT })
    setQuickMedications([])
    setQuickProcedures([])
    setPendingVoiceEvents([])
    setSavedCaseId(null)
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('battlefieldDraft')
    }
    setActiveTab('S1')
    toast.success('Нова чернетка кейсу створена')
  }

  const handleGenerateMist = async () => {
    if (!savedCaseId) {
      toast.info('Спочатку збережіть кейс, щоб згенерувати MIST')
      return
    }
    try {
      const res = await getMistSummary(savedCaseId)
      setMistSummary(res.mist_summary)
      toast.success('MIST оновлено')
    } catch (e) {
      toast.error('Помилка генерації MIST')
    }
  }

  const handleSaveCase = async () => {
    if (isSaving) return
    try {
      setIsSaving(true)
      
      // 1. Save main Case + Injuries
      const newCase = await createCase({
        callsign: callsign.trim() || 'НЕВІДОМИЙ',
        full_name: fullName.trim() || undefined,
        unit: unit.trim() || undefined,
        incident_time: injuryTime || undefined,
        triage_code: triageCat,
        mechanism_of_injury: mechanisms.join(', '),
        tourniquet_applied: tourniquetApplied,
        tourniquet_time: tourniquetTime || undefined,
        notes: intakeNotes.trim() || 'Створено через бойовий режим',
        injuries: injuries.map(inj => ({
          body_region: inj.body_region,
          injury_type: inj.injury_type,
          severity: inj.severity,
          view: inj.view,
          penetrating: inj.penetrating || false,
        }))
      })

      if (newCase?.id) {
        setSavedCaseId(newCase.id)
        
        // 2. Parallel saves for MARCH, Vitals, Evac
        const extras: Promise<unknown>[] = []
        
        // Only save if data was touched (simple check)
        if (Object.keys(marchData).length > 0) {
          extras.push(addMarch(newCase.id, marchData))
        }
        const vitalsPayload = normalizeVitalsPayload(vitalsData)
        if (Object.values(vitalsPayload).some((value) => value !== undefined)) {
          extras.push(addObservation(newCase.id, vitalsPayload))
        }
        if (evacData.evacuation_priority) {
          extras.push(upsertEvacuation(newCase.id, evacData))
        }
        for (const code of quickMedications) {
          extras.push(addMedication(newCase.id, {
            medication_code: code,
            time_administered: new Date().toISOString(),
          }))
        }
        for (const code of quickProcedures) {
          extras.push(addProcedure(newCase.id, {
            procedure_code: code.toUpperCase().replace(/\s+/g, '_'),
            notes: `Швидка дія: ${code}`,
          }))
        }
        extras.push(addEvent(newCase.id, {
          event_type: 'case_created',
          event_time: new Date().toISOString(),
          payload: {
            source: 'battlefield',
            triage: triageCat,
            callsign: callsign.trim() || 'НЕВІДОМИЙ',
          },
        }))
        for (const transcript of pendingVoiceEvents) {
          extras.push(addEvent(newCase.id, {
            event_type: 'voice',
            event_time: new Date().toISOString(),
            payload: {
              transcript,
            },
          }))
        }

        if (extras.length > 0) {
          await Promise.all(extras)
        }

        setQuickMedications([])
        setQuickProcedures([])
        setPendingVoiceEvents([])
        if (typeof window !== 'undefined') {
          window.localStorage.removeItem('battlefieldDraft')
        }

        toast.success(`✓ Все збережено! ID: ${newCase.id.slice(0, 8).toUpperCase()}`)
      }
    } catch (err: any) {
      const msg = err?.message?.includes('Failed to fetch')
        ? 'Немає зв\'язку з сервером. Перевірте мережу.'
        : `Помилка збереження: ${err?.message || 'Невідома помилка'}`
      toast.error(msg)
      console.error(err)
    } finally {
      setIsSaving(false)
    }
  }

  const selectedZoneData = BODY_ZONES.find(z => z.id === selectedZoneId)

  const stepProgressById = useMemo<Record<string, StepProgressState>>(() => {
    const s1Done = callsign.trim().length > 0 && mechanisms.length > 0
    const s1Touched = s1Done || [fullName, unit, injuryTime, tourniquetTime, intakeNotes].some((value) => value.trim().length > 0) || tourniquetApplied

    const s2Done = injuries.length > 0
    const s2Touched = s2Done || selectedZoneId !== null

    const marchTouched = Object.keys(marchData || {}).some((key) => {
      const current = marchData?.[key]
      const baseline = (MARCH_DEFAULT as Record<string, unknown>)[key]
      if (baseline !== undefined) return current !== baseline
      if (typeof current === 'boolean') return current
      if (typeof current === 'number') return current > 0
      if (typeof current === 'string') return current.trim().length > 0
      return Boolean(current)
    })

    const s3Done = Boolean(
      marchData?.m_massive_bleeding ||
      Number(marchData?.m_tourniquets_applied || 0) > 0 ||
      (marchData?.a_airway_intervention && marchData?.a_airway_intervention !== 'INTACT') ||
      marchData?.r_chest_seal_applied ||
      marchData?.r_needle_d_performed ||
      marchData?.r_chest_tube ||
      marchData?.c_iv_access ||
      marchData?.c_pelvic_binder ||
      marchData?.h_hypothermia_prevented ||
      marchData?.h_active_warming
    )
    const s3Touched = s3Done || marchTouched

    const hasVitals = Object.values(vitalsData || {}).some((value) => value !== '' && value !== null && value !== undefined)
    const s4Done = hasVitals || quickMedications.length > 0 || quickProcedures.length > 0
    const s4Touched = s4Done

    const destination = (evacData?.destination || '').trim()
    const s5Done = destination.length > 0
    const s5Touched = s5Done || (evacData?.transport_type && evacData.transport_type !== '') || ((evacData?.evacuation_priority || EVAC_DEFAULT.evacuation_priority) !== EVAC_DEFAULT.evacuation_priority)

    const toState = (done: boolean, touched: boolean): StepProgressState => {
      if (done) return 'done'
      if (touched) return 'in_progress'
      return 'not_started'
    }

    return {
      S1: toState(s1Done, s1Touched),
      S2: toState(s2Done, s2Touched),
      S3: toState(s3Done, s3Touched),
      S4: toState(s4Done, s4Touched),
      S5: toState(s5Done, s5Touched),
    }
  }, [
    callsign,
    fullName,
    unit,
    injuryTime,
    tourniquetTime,
    intakeNotes,
    mechanisms,
    tourniquetApplied,
    injuries,
    selectedZoneId,
    marchData,
    vitalsData,
    quickMedications,
    quickProcedures,
    evacData,
  ])

  return (
    <div className="h-screen bg-[#0b0d10] text-[#a0a5b0] flex flex-col font-sans relative overflow-hidden">
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 md:p-4 border-b border-[#1c1f26] bg-[#0f1217]">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-2 bg-[#1c1f26] rounded-md hover:bg-[#2a2f3a] transition-colors border border-[#2a2f3a]">
            <ArrowLeft className="w-5 h-5 text-gray-400" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-widest text-red-600 uppercase">БОЙОВИЙ РЕЖИМ</h1>
            <p className="text-[10px] uppercase tracking-[0.2em] font-mono text-gray-500">АЗОВ · Медична служба CCRM</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={startNewDraft}
            className="h-12 px-4 rounded-md border border-[#2a2f3a] bg-[#1a1d24] text-white font-bold text-sm"
            aria-label="Швидко додати новий запис"
          >
            +
          </button>
          <div className="flex flex-col items-center gap-1">
            <button
              onClick={handleMicClick}
              title={isWhisperConfigured ? 'Whisper: натисніть для старту/стопу запису' : 'Whisper: спочатку додайте API ключ у Налаштуваннях'}
              aria-label="Whisper голосовий ввід"
              className={`w-12 h-12 rounded-full flex items-center justify-center border-4 transition-all duration-300 ${isRecording ? 'bg-red-600 border-red-400 animate-[pulse_2s_infinite] text-white shadow-[0_0_20px_rgba(220,38,38,0.7)]' : 'bg-[#2a1a1a] border-[#5a1a1a] text-red-500 hover:bg-red-900/40'}`}
            >
              <Mic className="w-5 h-5" />
            </button>
            <span className={`text-[9px] uppercase tracking-widest ${isWhisperConfigured ? 'text-gray-500' : 'text-amber-400'}`}>
              {isWhisperConfigured ? 'WHISPER READY' : 'WHISPER KEY MISSING'}
            </span>
          </div>
        </div>
      </header>
      {recordingLabel && (
        <div className="px-4 py-2 text-[10px] font-bold uppercase tracking-[0.1em] text-red-300 bg-[#181013] border-b border-[#3a1f24]">
          {recordingLabel}
        </div>
      )}

      {/* TABS */}
      <div className="flex overflow-x-auto md:flex-wrap border-b border-[#1c1f26] bg-[#0f1217]">
        {TABS.map(tab => (
          (() => {
            const stepState = stepProgressById[tab.id] || 'not_started'
            const stepMeta = STEP_STATE_META[stepState]
            return (
          <button
            key={tab.id}
            onClick={() => goToTab(tab.id)}
            className={`px-4 md:px-6 py-3 text-xs font-bold tracking-[0.1em] uppercase whitespace-nowrap border-b-2 transition-colors min-w-[170px] flex-none md:flex-1 ${activeTab === tab.id ? 'border-red-600 text-white bg-[#1a1c22]' : 'border-transparent text-gray-500 hover:text-gray-300 hover:bg-[#15181e]'}`}
          >
            <div className="flex items-center justify-center gap-2">
              <span>{tab.name}</span>
              <span className={`w-2 h-2 rounded-full ${stepMeta.dotClass}`} />
            </div>
            <div className={`mt-1 text-[9px] tracking-[0.15em] ${stepMeta.textClass}`}>{stepMeta.label}</div>
          </button>
            )
          })()
        ))}
      </div>

      <main className="flex-1 p-4 lg:p-6 overflow-y-auto w-full max-w-7xl mx-auto pb-32 pb-safe-area">
        {activeTab === 'S1' && (
          <div className="max-w-3xl mx-auto space-y-6">
            <section className="wolf-panel p-6 border border-[#262a30] bg-[#14171b] rounded-md">
               <h2 className="text-[10px] uppercase tracking-[0.2em] text-gray-500 font-bold mb-4">ІДЕНТИФІКАЦІЯ</h2>
              <div className="space-y-4">
                <input 
                  type="text" 
                  placeholder="ПОЗИВНИЙ"
                  value={callsign}
                  onChange={e => {
                    setCallsign(e.target.value)
                    if (e.target.value.trim()) {
                      setFieldErrors((prev) => ({ ...prev, callsign: '' }))
                    }
                  }}
                  maxLength={100}
                  className={`w-full bg-transparent border-b-2 text-2xl lg:text-3xl text-white placeholder-gray-700 py-3 uppercase focus:outline-none focus:border-red-500 transition-colors tracking-widest ${fieldErrors.callsign ? 'border-red-500' : 'border-[#2a2f3a]'}`}
                />
                {fieldErrors.callsign && <p className="text-[10px] font-bold uppercase tracking-widest text-red-400">{fieldErrors.callsign}</p>}
                <input
                  type="text"
                  placeholder="ПОВНЕ ІМ'Я"
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  maxLength={140}
                  className="w-full bg-[#181b21] border border-[#2a2f3a] p-3 text-sm text-white rounded"
                />
                <input
                  type="text"
                  placeholder="ПІДРОЗДІЛ"
                  value={unit}
                  onChange={e => setUnit(e.target.value)}
                  maxLength={80}
                  className="w-full bg-[#181b21] border border-[#2a2f3a] p-3 text-sm text-white rounded uppercase"
                />
              </div>
            </section>

            <section className="wolf-panel p-6 border border-[#262a30] bg-[#14171b] rounded-md">
               <h2 className="text-[10px] uppercase tracking-[0.2em] text-gray-500 font-bold mb-4">СОРТУВАННЯ</h2>
               <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
                 {[
                   { code: 'IMMEDIATE', label: 'НЕВІДКЛАДНО', cls: 'bg-red-900/20 border-red-500 text-red-500 hover:bg-red-900/40' },
                   { code: 'DELAYED', label: 'ВІДСТРОЧЕНО', cls: 'bg-yellow-900/20 border-yellow-500 text-yellow-500 hover:bg-yellow-900/40' },
                   { code: 'MINIMAL', label: 'МІНІМАЛЬНА', cls: 'bg-green-900/20 border-green-500 text-green-500 hover:bg-green-900/40' },
                   { code: 'EXPECTANT', label: 'ОЧІКУВАННЯ', cls: 'bg-[#2a1a1a] border-[#5a5a5a] text-gray-400 hover:bg-[#3a2a2a]' },
                   { code: 'DECEASED', label: 'ЗАГИБЛИЙ', cls: 'bg-black border-gray-800 text-gray-600 hover:bg-[#111]' }
                 ].map(t => (
                   <button
                     key={t.code}
                     onClick={() => setTriageCat(t.code as TriageCategory)}
                     className={`flex flex-col items-center justify-center p-4 border-2 rounded-md font-bold text-[10px] tracking-widest uppercase transition-all ${triageCat === t.code ? t.cls + ' shadow-[0_0_15px_rgba(255,255,255,0.05)]' : 'bg-[#181b21] border-[#262a30] text-gray-600'}`}
                   >
                     {t.label}
                   </button>
                 ))}
               </div>
            </section>

            <section className="wolf-panel p-6 border border-[#262a30] bg-[#14171b] rounded-md">
               <h2 className="text-[10px] uppercase tracking-[0.2em] text-gray-500 font-bold mb-4">МЕХАНІЗМ ТРАВМИ</h2>
               <div className="flex flex-wrap gap-2">
                 {[
                   { code: 'BLAST', label: 'МІННО-ВИБУХОВА' },
                   { code: 'GSW', label: 'ВОГНЕПАЛЬНА' },
                   { code: 'FRAG', label: 'УЛАМКОВА' },
                   { code: 'BURN', label: 'ОПІК' },
                   { code: 'BLUNT', label: 'ТУПА ТРАВМА' },
                 ].map(m => (
                   <button
                     key={m.code}
                     onClick={() => {
                      toggleMechanism(m.code as MechanismOfInjury)
                      setFieldErrors((prev) => ({ ...prev, mechanisms: '' }))
                     }}
                     className={`px-4 py-3 border rounded text-xs font-bold tracking-widest uppercase transition-colors ${mechanisms.includes(m.code as MechanismOfInjury) ? 'bg-[#3b4252] border-[#4c566a] text-white' : 'bg-[#181b21] border-[#262a30] text-gray-500 hover:text-gray-300 hover:bg-[#1f232b]'}`}
                   >
                     {m.label}
                   </button>
                 ))}
               </div>
               {fieldErrors.mechanisms && <p className="mt-3 text-[10px] font-bold uppercase tracking-widest text-red-400">{fieldErrors.mechanisms}</p>}
            </section>

            <section className="wolf-panel p-6 border border-[#262a30] bg-[#14171b] rounded-md flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
               <div>
                 <h2 className="text-[10px] uppercase tracking-[0.2em] text-gray-500 font-bold mb-1">ТУРНІКЕТ НАКЛАДЕНО?</h2>
                 <p className="text-xs text-gray-600 font-mono">Швидка позначка для первинного огляду</p>
               </div>
               <div className="flex gap-2 w-full sm:w-auto">
                 <button onClick={() => setTourniquetApplied(true)} className={`px-6 py-3 font-bold text-sm tracking-widest border rounded transition-colors ${tourniquetApplied ? 'bg-red-900/50 border-red-500 text-red-500' : 'bg-[#181b21] border-[#262a30] text-gray-500 hover:bg-[#1f232b]'}`}>ТАК</button>
                 <button onClick={() => setTourniquetApplied(false)} className={`px-6 py-3 font-bold text-sm tracking-widest border rounded transition-colors ${!tourniquetApplied ? 'bg-[#3b4252] border-[#4c566a] text-white' : 'bg-[#181b21] border-[#262a30] text-gray-500 hover:bg-[#1f232b]'}`}>НІ</button>
               </div>
            </section>

            <section className="wolf-panel p-6 border border-[#262a30] bg-[#14171b] rounded-md grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-2">ЧАС ПОРАНЕННЯ</label>
                <input
                  type="datetime-local"
                  value={injuryTime}
                  onChange={(e) => setInjuryTime(e.target.value)}
                  className="w-full bg-[#181b21] border border-[#2a2f3a] p-3 text-sm text-white rounded"
                />
              </div>
              <div>
                <label className="block text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-2">ЧАС ТУРНІКЕТУ</label>
                <input
                  type="datetime-local"
                  value={tourniquetTime}
                  onChange={(e) => setTourniquetTime(e.target.value)}
                  className="w-full bg-[#181b21] border border-[#2a2f3a] p-3 text-sm text-white rounded"
                />
              </div>
              <div className="lg:col-span-2">
                <label className="block text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-2">Нотатки</label>
                <textarea
                  value={intakeNotes}
                  onChange={(e) => setIntakeNotes(e.target.value)}
                  rows={4}
                  className="w-full bg-[#181b21] border border-[#2a2f3a] p-3 text-sm text-white rounded"
                  placeholder="Короткі клінічні нотатки, зокрема з голосового вводу"
                />
                <div className="mt-3 p-3 border border-[#2a2f3a] rounded bg-[#11151b]">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div>
                      <p className="text-[10px] font-bold tracking-widest uppercase text-gray-300">ГОЛОСОВИЙ ВВІД WHISPER AI</p>
                      <p className="text-[10px] text-gray-500 mt-1">Натисніть кнопку, продиктуйте клінічний стан і зупиніть запис для автотранскрипції.</p>
                    </div>
                    <button
                      type="button"
                      onClick={handleMicClick}
                      className={`w-full sm:w-auto px-4 py-2 border rounded text-[10px] font-bold tracking-widest uppercase transition-colors ${isRecording ? 'bg-red-900/40 border-red-500 text-red-300' : 'bg-[#1a1d24] border-[#2a2f3a] text-gray-300 hover:border-gray-500'}`}
                    >
                      {isRecording ? 'ЗАВЕРШИТИ ЗАПИС' : 'ПОЧАТИ ГОЛОСОВИЙ ВВІД'}
                    </button>
                  </div>
                  {!isWhisperConfigured && (
                    <p className="mt-2 text-[10px] text-amber-300">
                      Ключ Whisper не знайдено в сесії. Додайте його у <Link href="/settings" className="underline">Налаштуваннях</Link>, поле "WHISPER API КЛЮЧ (СЕСІЯ)".
                    </p>
                  )}
                </div>
              </div>
            </section>

            <button onClick={() => goToTab('S2')} className="w-full py-5 bg-red-900 border border-red-700 hover:bg-red-800 text-white font-bold tracking-[0.2em] rounded transition-colors shadow-lg">
              ДАЛІ → S2 КАРТА ТІЛА
            </button>
          </div>
        )}

        {activeTab === 'S2' && (
          <div className="w-full mx-auto flex flex-col gap-6">
             {/* View Toggle */}
             <div className="grid grid-cols-2 rounded-t-md overflow-hidden bg-[#14171b] border border-[#262a30]">
               <button onClick={() => setActiveView('front')} className={`py-4 text-xs font-bold tracking-[0.1em] uppercase transition-colors ${activeView === 'front' ? 'bg-[#1f242d] text-white border-b-2 border-red-500' : 'text-gray-500 hover:bg-[#1a1d24]'}`}>ФРОНТ</button>
               <button onClick={() => setActiveView('back')} className={`py-4 text-xs font-bold tracking-[0.1em] uppercase transition-colors ${activeView === 'back' ? 'bg-[#1f242d] text-white border-b-2 border-red-500' : 'text-gray-500 hover:bg-[#1a1d24]'}`}>ТИЛ</button>
             </div>

             <div className="flex flex-col lg:flex-row gap-6 items-start h-full">
               
               {/* Body Canvas Area */}
               <BodyMap 
                 activeView={activeView} 
                 injuries={injuries} 
                 selectedZone={selectedZoneId} 
                 onZoneClick={handleZoneClick} 
               />

                  {!selectedZoneId && (
                     <p className="absolute bottom-6 left-0 right-0 text-center text-gray-500 font-mono text-[10px] uppercase tracking-[0.2em] pointer-events-none animate-pulse">
                       Натисніть на зону тіла щоб додати травму
                     </p>
                  )}
               
               {/* Right Side: Log or S2-BS Form */}
               <div className="w-full lg:w-1/3 flex flex-col gap-4">
                  
                  {/* Bottom Sheet Modeled as a Side Panel for Desktop / Inline for Mobile */}
                  {selectedZoneData && (
                     <div className="bg-[#181b21] border border-red-500/50 rounded-md p-6 shadow-[0_0_30px_rgba(239,68,68,0.1)] relative">
                        <button onClick={() => setSelectedZoneId(null)} className="absolute top-4 right-4 text-gray-500 hover:text-white bg-[#262a30] rounded-full p-1"><X className="w-4 h-4"/></button>
                        
                        <h3 className="text-red-500 font-bold tracking-widest text-lg uppercase mb-1">Зона: {selectedZoneData.name}</h3>
                        <p className="text-gray-500 text-[10px] mb-6 uppercase tracking-widest">{activeView === 'front' ? 'ФРОНТ' : 'ТИЛ'}</p>
                        
                        <div className="space-y-6">
                           <div>
                             <label className="text-[10px] text-gray-400 font-bold tracking-[0.2em] uppercase block mb-3">ТИП УШКОДЖЕННЯ</label>
                             <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
                               {[
                                 {id: 'ENTRY_WOUND', name: 'ВХІДНЕ'}, {id: 'EXIT_WOUND', name: 'ВИХІДНЕ'},
                                 {id: 'FRAG_WOUND', name: 'УЛАМКОВЕ'}, {id: 'MASSIVE_BLEEDING', name: 'КРОВОТЕЧА'},
                                 {id: 'BURN', name: 'ОПІК'}, {id: 'AMPUTATION', name: 'АМПУТАЦІЯ'},
                                 {id: 'FRACTURE_SUSPECTED', name: 'ПЕРЕЛОМ'}, {id: 'OPEN_WOUND', name: 'РАНА'},
                                 {id: 'BLAST_INJURY', name: 'ВИБУХОВА'}
                               ].map(type => (
                                 <button 
                                  key={type.id} 
                                  onClick={() => setSheetInjuryType(type.id as InjuryType)} 
                                  className={`cursor-pointer px-2 py-3 border text-[9px] font-bold tracking-[0.1em] uppercase rounded text-center transition-all ${sheetInjuryType === type.id ? 'bg-red-900 border-red-500 text-white shadow-inner' : 'bg-[#111317] border-[#2a2f3a] text-gray-400 hover:bg-[#1a1d22]'}`}
                                 >
                                   <div className="text-lg mb-1 leading-none">{INJURY_ICONS[type.id as InjuryType]}</div>
                                   {type.name}
                                 </button>
                               ))}
                             </div>
                           </div>

                           <div>
                             <label className="text-[10px] text-gray-400 font-bold tracking-[0.2em] uppercase block mb-3">СЕРЙОЗНІСТЬ</label>
                             <div className="flex bg-[#111317] rounded border border-[#2a2f3a] overflow-hidden">
                                {[
                                  {id: 'MINOR', l: 'МІН'}, {id: 'MODERATE', l: 'СЕР'}, 
                                  {id: 'SEVERE', l: 'ВАЖК'}, {id: 'CRITICAL', l: 'КРИТ'}
                                ].map(sev => (
                                  <button 
                                    key={sev.id} 
                                    onClick={() => setSheetSeverity(sev.id as Severity)} 
                                    className={`flex-1 py-3 text-[10px] font-bold tracking-wider uppercase border-r border-[#2a2f3a] last:border-0 transition-colors ${sheetSeverity === sev.id ? 'bg-orange-900 text-orange-200' : 'text-gray-500 hover:bg-[#1a1d22]'}`}
                                  >
                                    {sev.l}
                                  </button>
                                ))}
                             </div>
                           </div>

                           <button
                             onClick={saveMarker}
                             disabled={isMarkerSaving}
                             className="w-full py-4 mt-2 bg-red-600 hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-xs tracking-widest uppercase rounded shadow-[0_0_15px_rgba(220,38,38,0.4)]"
                           >
                             {isMarkerSaving ? 'ЗБЕРЕЖЕННЯ...' : 'ОК - ЗБЕРЕГТИ МАРКЕР'}
                           </button>
                        </div>
                     </div>
                  )}

                  <div className="bg-[#14171b] border border-[#262a30] rounded-md p-5 flex-1 max-h-[500px] overflow-y-auto">
                    <h3 className="text-gray-400 text-[10px] font-bold tracking-[0.2em] uppercase mb-4 flex justify-between items-center">
                       <span>ЖУРНАЛ ТРАВМ ({activeView === 'front' ? 'ФРОНТ' : 'ТИЛ'})</span>
                       <span className="text-red-500">{injuries.filter(i => i.view === activeView).length} всього</span>
                    </h3>
                      {fieldErrors.injuries && <p className="mb-3 text-[10px] font-bold uppercase tracking-widest text-red-400">{fieldErrors.injuries}</p>}
                    <div className="space-y-3">
                       {injuries.filter(i => i.view === activeView).length === 0 && (
                         <div className="flex flex-col items-center justify-center py-10 text-gray-600 border border-dashed border-[#262a30] rounded">
                           <p className="text-[10px] font-mono uppercase">Травм не відмічено</p>
                         </div>
                       )}
                       {injuries.filter(i => i.view === activeView).map(inj => (
                         <div key={inj.id} className="p-3 bg-[#1a1c22] border border-[#2a2f3a] rounded flex justify-between items-start animate-in slide-in-from-left-2">
                            <div className="flex gap-4">
                              <span className="text-red-500 font-bold text-lg mt-0.5">{INJURY_ICONS[inj.injury_type]}</span>
                              <div>
                                <p className="text-gray-100 text-xs font-bold uppercase tracking-wider mb-1">{BODY_ZONES.find(z => z.id === inj.body_region)?.name || inj.body_region}</p>
                                <div className="flex items-center gap-2">
                                  <span className="bg-[#2a1a1a] text-red-400 rounded px-1.5 py-0.5 text-[8px] uppercase">{inj.injury_type.replace(/_/g,' ')}</span>
                                  <span className="bg-[#111] text-gray-400 border border-[#333] rounded px-1.5 py-0.5 text-[8px] uppercase">{inj.severity}</span>
                                </div>
                              </div>
                            </div>
                            <button onClick={() => setInjuries(injuries.filter(i => i.id !== inj.id))} className="text-gray-600 hover:text-red-500 bg-[#111] border border-[#222] rounded p-1.5 transition-colors">
                              <X className="w-3 h-3"/>
                            </button>
                         </div>
                       ))}
                    </div>
                  </div>
               </div>

             </div>
          </div>
        )}

        {activeTab === 'S3' && <MarchForm data={marchData} onChange={setMarchData} />}
        
        {activeTab === 'S4' && (
          <VitalsForm 
            vitals={vitalsData} 
            onVitalsChange={setVitalsData} 
            onAddAction={handleAddAction} 
          />
        )}

        {activeTab === 'S5' && (
          <EvacForm 
            data={evacData} 
            mist={mistSummary} 
            onChange={(nextData) => {
              setEvacData(nextData)
              if (nextData?.destination?.trim()) {
                setFieldErrors((prev) => ({ ...prev, destination: '' }))
              }
            }} 
            destinationError={fieldErrors.destination}
            onGenerateMist={handleGenerateMist} 
          />
        )}

        <div className="mt-6 p-3 border border-[#262a30] bg-[#14171b] rounded-md flex items-center justify-between gap-3">
          <button
            onClick={goPrevTab}
            disabled={!canGoPrev}
            className="px-4 py-2 text-xs font-bold uppercase tracking-widest border border-[#2a2f3a] bg-[#1a1d24] text-gray-300 rounded disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ← Назад
          </button>

          <div className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">
            Крок {currentTabIndex + 1} / {tabIds.length}
          </div>

          <button
            onClick={goNextTab}
            disabled={!canGoNext}
            className="px-4 py-2 text-xs font-bold uppercase tracking-widest border border-red-700 bg-red-900 text-white rounded disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Далі →
          </button>
        </div>
      </main>

      {/* Floating Action / Save Bar */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-[#0f1217]/95 backdrop-blur-sm border-t border-[#1c1f26] flex justify-between items-center z-50">
        <div className="text-gray-500 font-mono text-[10px] uppercase hidden md:flex items-center gap-4">
           <span className="px-3 py-1 bg-[#1a1d24] rounded-full border border-[#2a2f3a] text-gray-300">ПЦ: {callsign || 'НЕВІДОМИЙ'}</span>
            <span className="text-yellow-600 flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-yellow-600 animate-pulse"></span> ШВИДКІ ПРЕПАРАТИ {quickMedications.length}</span>
            <span className="text-blue-500">ШВИДКІ ПРОЦЕДУРИ {quickProcedures.length}</span>
        </div>
        <div className="flex gap-4 w-full md:w-auto">
          <button
            onClick={() => {
              setCallsign('')
              setFullName('')
              setUnit('')
              setInjuryTime('')
              setTourniquetApplied(false)
              setTourniquetTime('')
              setIntakeNotes('')
              setInjuries([])
              setVitalsData({})
              setMarchData({ ...MARCH_DEFAULT })
              setEvacData({ ...EVAC_DEFAULT })
              setQuickMedications([])
              setQuickProcedures([])
              setPendingVoiceEvents([])
              if (typeof window !== 'undefined') {
                window.localStorage.removeItem('battlefieldDraft')
              }
              setActiveTab('S1')
                              toast.info('Чернетку скасовано')
            }}
            className="flex-1 md:flex-none px-6 py-4 bg-[#1a202c] hover:bg-[#252d3d] border border-[#2d3748] rounded text-gray-300 font-bold tracking-[0.1em] text-[10px] md:text-xs uppercase transition-colors"
          >
            СКАСУВАТИ
          </button>
          <button 
            onClick={handleSaveCase} 
            disabled={isSaving}
            className={`flex-1 md:flex-none px-8 py-4 bg-[#8f3d3d] hover:bg-red-800 border border-red-900 rounded text-white font-bold tracking-[0.1em] text-[10px] md:text-xs uppercase flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(220,38,38,0.2)] transition-colors ${isSaving ? 'opacity-50 cursor-not-allowed' : ''}`}>
            <Save className="w-4 h-4" /> {isSaving ? 'ЗБЕРЕЖЕННЯ...' : 'ЗБЕРЕГТИ КЕЙС'}
          </button>
        </div>
      </div>
    </div>
  )
}
