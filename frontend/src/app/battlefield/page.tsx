'use client'

import { useEffect, useRef, useState } from 'react'
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

export default function BattlefieldPage() {
  const toast = useToast()
  const [activeTab, setActiveTab] = useState('S1')
  const [isRecording, setIsRecording] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [recordingLabel, setRecordingLabel] = useState('')
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
    m_tourniquets_applied: 0,
    a_airway_open: true,
    a_airway_intervention: 'INTACT',
    c_radial_pulse: 'Radial'
  })
  const [vitalsData, setVitalsData] = useState<any>({})
  const [evacData, setEvacData] = useState<any>({ evacuation_priority: 'ROUTINE' })
  const [mistSummary, setMistSummary] = useState('')
  const [savedCaseId, setSavedCaseId] = useState<string | null>(null)
  const [quickMedications, setQuickMedications] = useState<string[]>([])
  const [quickProcedures, setQuickProcedures] = useState<string[]>([])
  const [pendingVoiceEvents, setPendingVoiceEvents] = useState<string[]>([])

  // CPR / cardiac stopwatch — 1: start, 2: stop, 3: reset
  const [swState, setSwState] = useState<'idle' | 'running' | 'stopped'>('idle')
  const [swMs, setSwMs] = useState(0)
  const swStartRef = useRef<number>(0)
  const swRafRef = useRef<number>(0)

  const tickSw = () => {
    setSwMs(performance.now() - swStartRef.current)
    swRafRef.current = requestAnimationFrame(tickSw)
  }

  const handleSwClick = () => {
    if (swState === 'idle') {
      swStartRef.current = performance.now()
      swRafRef.current = requestAnimationFrame(tickSw)
      setSwState('running')
    } else if (swState === 'running') {
      cancelAnimationFrame(swRafRef.current)
      setSwState('stopped')
    } else {
      setSwMs(0)
      setSwState('idle')
    }
  }

  useEffect(() => () => cancelAnimationFrame(swRafRef.current), [])

  const formatSw = (ms: number) => {
    const totalMs = Math.floor(ms)
    const h = Math.floor(totalMs / 3600000)
    const m = Math.floor((totalMs % 3600000) / 60000)
    const s = Math.floor((totalMs % 60000) / 1000)
    const cs = Math.floor((totalMs % 1000) / 10)
    return `${h > 0 ? String(h).padStart(2,'0') + ':' : ''}${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}.${String(cs).padStart(2,'0')}`
  }

  const tabIds = TABS.map((t) => t.id)
  const currentTabIndex = tabIds.indexOf(activeTab)
  const canGoPrev = currentTabIndex > 0
  const canGoNext = currentTabIndex >= 0 && currentTabIndex < tabIds.length - 1

  const goPrevTab = () => {
    if (!canGoPrev) return
    setActiveTab(tabIds[currentTabIndex - 1])
  }

  const goNextTab = () => {
    if (!canGoNext) return
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
      setMarchData(draft.marchData || {
        m_tourniquets_applied: 0,
        a_airway_open: true,
        a_airway_intervention: 'INTACT',
        c_radial_pulse: 'Radial'
      })
      setVitalsData(draft.vitalsData || {})
      setEvacData(draft.evacData || { evacuation_priority: 'ROUTINE' })
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
    if (!selectedZoneId) return
    const newInjury: InjuryRecord = {
      id: Math.random().toString(36).substr(2, 9),
      body_region: selectedZoneId,
      injury_type: sheetInjuryType,
      severity: sheetSeverity,
      view: activeView,
      penetrating: false
    }
    setInjuries([...injuries, newInjury])
    setSelectedZoneId(null)
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
          const whisperKey = sessionStorage.getItem('whisperApiKey') || ''
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
          if (!whisperKey) {
            setRecordingLabel('Whisper ключ відсутній у сесії')
            toast.info('Додайте whisperApiKey у сесію налаштувань')
            return
          }

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
    setMarchData({
      m_tourniquets_applied: 0,
      a_airway_open: true,
      a_airway_intervention: 'INTACT',
      c_radial_pulse: 'Radial'
    })
    setEvacData({ evacuation_priority: 'ROUTINE' })
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
          const results = await Promise.allSettled(extras)
          const failed = results.filter(r => r.status === 'rejected')
          if (failed.length > 0) {
            console.warn(`${failed.length}/${results.length} parallel saves failed, but case created`)
          }
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

  return (
    <div className="h-screen bg-[#0b0d10] text-[#a0a5b0] flex flex-col font-sans relative overflow-hidden">
      <header className="grid grid-cols-3 items-center p-4 border-b border-[#1c1f26] bg-[#0f1217]">
        <div className="flex items-center gap-4">
          <Link href="/" className="p-2 bg-[#1c1f26] rounded-md hover:bg-[#2a2f3a] transition-colors border border-[#2a2f3a]">
            <ArrowLeft className="w-5 h-5 text-gray-400" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-widest text-red-600 uppercase">БОЙОВИЙ РЕЖИМ</h1>
            <p className="text-[10px] uppercase tracking-[0.2em] font-mono text-gray-500">АЗОВ • МЕДИЧНИЙ ПІДРОЗДІЛ</p>
          </div>
        </div>

        {/* CPR stopwatch — truly centered */}
        <div className="flex justify-center">
          <button
            onClick={handleSwClick}
            className={`flex items-center gap-3 px-4 py-2 rounded-lg border font-mono transition-all select-none ${
              swState === 'running'
                ? 'bg-red-950/30 border-red-900/60'
                : swState === 'stopped'
                ? 'bg-[#1a1d24] border-yellow-900/50'
                : 'bg-[#12151a] border-[#252930] hover:border-[#3a3f4a]'
            }`}
            title={swState === 'idle' ? 'КПР: старт' : swState === 'running' ? 'КПР: стоп' : 'КПР: скинути'}
          >
            <span className={`text-[8px] uppercase tracking-[0.2em] font-bold ${
              swState === 'running' ? 'text-red-700' : swState === 'stopped' ? 'text-yellow-700' : 'text-gray-600'
            }`}>
              {swState === 'idle' ? '▶ КПР' : swState === 'running' ? '█ СТОП' : '↺ СКИНУТИ'}
            </span>
            <span className={`text-2xl font-bold tabular-nums tracking-widest ${
              swState === 'running' ? 'text-red-600' : swState === 'stopped' ? 'text-yellow-600' : 'text-gray-600'
            }`}>
              {formatSw(swMs)}
            </span>
            {swState === 'running' && (
              <span className="text-[7px] text-red-800 uppercase tracking-[0.1em] animate-pulse">●</span>
            )}
          </button>
        </div>

        <div className="flex items-center gap-3 justify-end">
          <button
            onClick={startNewDraft}
            className="h-12 px-4 rounded-md border border-[#2a2f3a] bg-[#1a1d24] text-white font-bold text-sm"
            aria-label="Швидко додати новий запис"
          >
            +
          </button>
          <button onClick={handleMicClick} className={`w-12 h-12 rounded-full flex items-center justify-center border-4 transition-all duration-300 ${isRecording ? 'bg-red-600 border-red-400 animate-[pulse_2s_infinite] text-white shadow-[0_0_20px_rgba(220,38,38,0.7)]' : 'bg-[#2a1a1a] border-[#5a1a1a] text-red-500 hover:bg-red-900/40'}`}>
            <Mic className="w-5 h-5" />
          </button>
        </div>
      </header>
      {recordingLabel && (
        <div className="px-4 py-2 text-[10px] font-bold uppercase tracking-[0.1em] text-red-300 bg-[#181013] border-b border-[#3a1f24]">
          {recordingLabel}
        </div>
      )}

      {/* TABS */}
      <div className="flex flex-wrap border-b border-[#1c1f26] bg-[#0f1217]">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 md:px-6 py-4 text-xs font-bold tracking-[0.1em] uppercase whitespace-nowrap border-b-2 transition-colors min-w-[170px] flex-1 ${activeTab === tab.id ? 'border-red-600 text-white bg-[#1a1c22]' : 'border-transparent text-gray-500 hover:text-gray-300 hover:bg-[#15181e]'}`}
          >
            {tab.name}
          </button>
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
                  onChange={e => setCallsign(e.target.value)}
                  maxLength={100}
                  className="w-full bg-transparent border-b-2 border-[#2a2f3a] text-2xl lg:text-3xl text-white placeholder-gray-700 py-3 uppercase focus:outline-none focus:border-red-500 transition-colors tracking-widest"
                />
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
                     onClick={() => toggleMechanism(m.code as MechanismOfInjury)}
                     className={`px-4 py-3 border rounded text-xs font-bold tracking-widest uppercase transition-colors ${mechanisms.includes(m.code as MechanismOfInjury) ? 'bg-[#3b4252] border-[#4c566a] text-white' : 'bg-[#181b21] border-[#262a30] text-gray-500 hover:text-gray-300 hover:bg-[#1f232b]'}`}
                   >
                     {m.label}
                   </button>
                 ))}
               </div>
            </section>

            <section className="wolf-panel p-6 border border-[#262a30] bg-[#14171b] rounded-md flex items-center justify-between">
               <div>
                 <h2 className="text-[10px] uppercase tracking-[0.2em] text-gray-500 font-bold mb-1">ТУРНІКЕТ НАКЛАДЕНО?</h2>
                 <p className="text-xs text-gray-600 font-mono">Швидка позначка для первинного огляду</p>
               </div>
               <div className="flex gap-2">
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
              </div>
            </section>

            <button onClick={() => setActiveTab('S2')} className="w-full py-5 bg-red-900 border border-red-700 hover:bg-red-800 text-white font-bold tracking-[0.2em] rounded transition-colors shadow-lg">
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

                           <button onClick={saveMarker} className="w-full py-4 mt-2 bg-red-600 hover:bg-red-500 text-white font-bold text-xs tracking-widest uppercase rounded shadow-[0_0_15px_rgba(220,38,38,0.4)]">
                             ОК - ЗБЕРЕГТИ МАРКЕР
                           </button>
                        </div>
                     </div>
                  )}

                  <div className="bg-[#14171b] border border-[#262a30] rounded-md p-5 flex-1 max-h-[500px] overflow-y-auto">
                    <h3 className="text-gray-400 text-[10px] font-bold tracking-[0.2em] uppercase mb-4 flex justify-between items-center">
                       <span>ЖУРНАЛ ТРАВМ ({activeView === 'front' ? 'ФРОНТ' : 'ТИЛ'})</span>
                       <span className="text-red-500">{injuries.filter(i => i.view === activeView).length} всього</span>
                    </h3>
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
            onChange={setEvacData} 
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
              setMarchData({
                m_tourniquets_applied: 0,
                a_airway_open: true,
                a_airway_intervention: 'INTACT',
                c_radial_pulse: 'Radial'
              })
              setEvacData({ evacuation_priority: 'ROUTINE' })
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
