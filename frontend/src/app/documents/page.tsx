'use client'

import { useEffect, useState, useRef } from 'react'
import { FileText, UploadCloud, FileImage, File, Trash2, ShieldCheck } from 'lucide-react'
import { listDocuments, uploadDocument, listCases } from '@/lib/api'
import { CaseItem } from '@/lib/types'

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<any[]>([])
  const [cases, setCases] = useState<CaseItem[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  
  const [selectedCase, setSelectedCase] = useState('')
  const [selectedType, setSelectedType] = useState('DD_1380_CARD')
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    load()
  }, [])

  async function load() {
    try {
      setLoading(true)
      const [docsData, casesData] = await Promise.all([
        listDocuments(),
        listCases()
      ])
      setDocuments(docsData)
      setCases(casesData)
    } catch (e) {
      console.error('Failed to load documents/cases:', e)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      setUploading(true)
      await uploadDocument(selectedCase, selectedType, file)
      await load()
      // Reset form
      if (fileInputRef.current) fileInputRef.current.value = ''
      alert('Документ успішно завантажено в зашифроване сховище!')
    } catch (err) {
      console.error(err)
      alert('Помилка завантаження документу.')
    } finally {
      setUploading(false)
    }
  }

  const triggerUpload = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-xl font-bold tracking-widest text-white uppercase mb-1">ЗАХИЩЕНИЙ АРХІВ ДОКУМЕНТІВ</h1>
          <p className="text-xs text-gray-500 font-mono tracking-widest uppercase">E2E Шифрування Фото та Сканів</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form */}
        <div className="lg:col-span-1 space-y-4">
          <div className="wolf-panel p-5">
            <h3 className="text-sm font-bold tracking-widest uppercase text-white mb-6 flex items-center gap-2">
              <UploadCloud className="w-4 h-4 text-blue-500" /> Джерело Завантаження
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-[10px] tracking-widest text-gray-500 uppercase font-bold mb-2">Прив'язка до кейсу (Опціонально)</label>
                <select 
                  value={selectedCase} 
                  onChange={(e) => setSelectedCase(e.target.value)}
                  className="w-full bg-[#1a1d24] border border-[#262a30] text-gray-300 rounded-md p-2 text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="">Без прив'язки (Загальний архів)</option>
                  {cases.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.case_number || c.callsign || c.id.substring(0,8)} - {c.triage_code}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] tracking-widest text-gray-500 uppercase font-bold mb-2">Тип документа</label>
                <select 
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="w-full bg-[#1a1d24] border border-[#262a30] text-gray-300 rounded-md p-2 text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="DD_1380_CARD">Картка пораненого (DD Form 1380)</option>
                  <option value="ID_SCAN">Скан військового квитка</option>
                  <option value="INJURY_PHOTO">Фотографія травми</option>
                  <option value="XRAY">Знімок (X-Ray / MRI)</option>
                  <option value="OTHER">Інше</option>
                </select>
              </div>

              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileUpload} 
                className="hidden" 
                accept="image/*,.pdf"
              />

              <button 
                onClick={triggerUpload}
                disabled={uploading}
                className={`w-full py-4 mt-2 border border-dashed rounded-lg flex flex-col items-center justify-center gap-2 transition-colors ${uploading ? 'bg-blue-900/20 border-blue-900 text-blue-500' : 'bg-[#1a1d24] border-[#262a30] text-gray-400 hover:text-white hover:border-blue-500 hover:bg-blue-900/10'}`}
              >
                <UploadCloud className={`w-6 h-6 ${uploading ? 'animate-bounce' : ''}`} />
                <span className="text-xs font-bold tracking-widest uppercase">
                  {uploading ? 'ШИФРУВАННЯ ТА ВІДПРАВКА...' : 'ВИБРАТИ ФАЙЛ ТА ЗАВАНТАЖИТИ'}
                </span>
                <span className="text-[10px] text-gray-500">JPG, PNG, PDF до 10MB</span>
              </button>
            </div>
            
            <div className="mt-4 p-3 bg-green-900/10 border border-green-900/30 rounded-md flex gap-2">
              <ShieldCheck className="w-4 h-4 text-green-500 shrink-0" />
              <p className="text-[10px] text-green-500/80 leading-relaxed uppercase tracking-wider">
                Усі файли повністю шифруються перед завантаженням у хмарний архів та доступні лише авторизованому медичному персоналу.
              </p>
            </div>
          </div>
        </div>

        {/* Existing Documents List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="wolf-panel p-5 h-full">
            <h3 className="text-sm font-bold tracking-widest uppercase text-white mb-6 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-500" /> БАЗА ДОКУМЕНТІВ
            </h3>

            <div className="space-y-3">
              {loading ? (
                <div className="text-center text-sm text-gray-500 py-8">Завантаження архіву...</div>
              ) : documents.length === 0 ? (
                <div className="text-center text-sm text-gray-500 py-12 border border-dashed border-[#262a30] rounded bg-[#1a1d24]">
                  Архів документів порожній
                </div>
              ) : (
                documents.map(doc => (
                  <div key={doc.id} className="p-3 bg-[#1a1d24] border border-[#262a30] hover:border-blue-900/50 transition-colors rounded flex items-center justify-between group">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-[#0f1217] rounded flex items-center justify-center border border-[#262a30]">
                        {doc.file_path && doc.file_path.includes('.pdf') ? <FileText className="w-5 h-5 text-red-400" /> : <FileImage className="w-5 h-5 text-blue-400" />}
                      </div>
                      <div>
                        <div className="font-bold text-white text-sm">{doc.file_name}</div>
                        <div className="text-xs text-gray-400 flex items-center gap-2 mt-1">
                          <span className="px-2 py-0.5 bg-[#0f1217] rounded text-[9px] uppercase tracking-widest border border-[#262a30]">
                            {doc.document_type}
                          </span>
                          <span>• {doc.case_id ? `КЕЙС ID: ${doc.case_id.substring(0,8)}` : 'ЗАГАЛЬНИЙ АРХІВ'}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => alert('Перегляд файлу у вбудованому вікні буде додано в наступному релізі.')}
                        className="p-2 bg-blue-900/20 text-blue-400 rounded hover:bg-blue-600 hover:text-white transition-colors"
                      >
                        <File className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => alert('Видалення документів буде доступне після додавання журналу відновлення.')}
                        className="p-2 bg-red-900/20 text-red-400 rounded hover:bg-red-600 hover:text-white transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
