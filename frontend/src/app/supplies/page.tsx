'use client'

import { Package, AlertCircle, PlusCircle, MinusCircle, RefreshCw } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useToast } from '@/components/Toast'

type SuppliesSortKey = 'name_asc' | 'qty_asc' | 'qty_desc' | 'deficit_desc'

const SUPPLIES_FILTERS_KEY = 'suppliesTableFilters:v1'

function readSavedFilters() {
  if (typeof window === 'undefined') {
    return { search: '', category: 'all', stock: 'all', sort: 'deficit_desc' as SuppliesSortKey }
  }
  try {
    const raw = window.localStorage.getItem(SUPPLIES_FILTERS_KEY)
    if (!raw) return { search: '', category: 'all', stock: 'all', sort: 'deficit_desc' as SuppliesSortKey }
    const parsed = JSON.parse(raw) as { search?: string; category?: string; stock?: string; sort?: SuppliesSortKey }
    return {
      search: parsed.search || '',
      category: parsed.category || 'all',
      stock: parsed.stock || 'all',
      sort: parsed.sort || 'deficit_desc',
    }
  } catch {
    return { search: '', category: 'all', stock: 'all', sort: 'deficit_desc' as SuppliesSortKey }
  }
}

export default function SuppliesPage() {
  const initialFilters = readSavedFilters()
  const toast = useToast()
  const [supplies, setSupplies] = useState([
    { id: 1, name: 'Турнікет CAT (Gen 7)', category: 'HEMOSTATIC', qty: 45, min: 20 },
    { id: 2, name: 'Гемостатичний бинт QuikClot', category: 'HEMOSTATIC', qty: 18, min: 25 },
    { id: 3, name: 'Оклюзійна наліпка Asherman', category: 'AIRWAY', qty: 30, min: 15 },
    { id: 4, name: 'Декомпресійна голка 14G', category: 'AIRWAY', qty: 12, min: 20 },
    { id: 5, name: 'Кетамін ампули', category: 'MEDICATION', qty: 8, min: 10 },
    { id: 6, name: 'Фентаніл (льодяники)', category: 'MEDICATION', qty: 25, min: 5 },
    { id: 7, name: 'Транексамова кислота (TXA)', category: 'HEMOSTATIC', qty: 40, min: 15 },
    { id: 8, name: 'Кристалоїди (NaCl 0.9%)', category: 'FLUIDS', qty: 50, min: 30 },
  ])
  const [search, setSearch] = useState(initialFilters.search)
  const [filterCategory, setFilterCategory] = useState(initialFilters.category)
  const [filterStock, setFilterStock] = useState(initialFilters.stock)
  const [sortBy, setSortBy] = useState<SuppliesSortKey>(initialFilters.sort)

  function updateQty(id: number, delta: number) {
    setSupplies(prev => prev.map(s => s.id === id ? { ...s, qty: Math.max(0, s.qty + delta) } : s))
  }

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(
      SUPPLIES_FILTERS_KEY,
      JSON.stringify({ search, category: filterCategory, stock: filterStock, sort: sortBy }),
    )
  }, [search, filterCategory, filterStock, sortBy])

  function syncSupplies() {
    toast.success('Список запасів оновлено')
  }

  function createRequisition() {
    if (criticalItems.length === 0) {
      toast.info('Критичної нестачі немає')
      return
    }

    const createdAt = new Date().toLocaleString('uk-UA')
    const lines = [
      'ЗАЯВКА НА ПОПОВНЕННЯ МЕДЗАПАСІВ',
      `Дата: ${createdAt}`,
      '',
      'Позиції:',
      ...criticalItems.map((item, index) => {
        const deficit = Math.max(0, item.min - item.qty)
        return `${index + 1}. ${item.name} | Категорія: ${item.category} | Залишок: ${item.qty} | Мінімум: ${item.min} | Дозамовити: ${deficit}`
      }),
    ]

    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `zayavka_medzapasy_${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    toast.success('Заявку сформовано і завантажено')
  }

  const criticalItems = supplies.filter(s => s.qty < s.min)

  const categories = useMemo(() => {
    const set = new Set<string>()
    for (const item of supplies) set.add(item.category)
    return Array.from(set).sort((a, b) => a.localeCompare(b, 'uk'))
  }, [supplies])

  const tableItems = useMemo(() => {
    const filtered = supplies.filter((item) => {
      const q = search.trim().toLowerCase()
      const matchesSearch = !q || item.name.toLowerCase().includes(q) || item.category.toLowerCase().includes(q)
      const matchesCategory = filterCategory === 'all' || item.category === filterCategory
      const isCritical = item.qty < item.min
      const matchesStock = filterStock === 'all' || (filterStock === 'critical' ? isCritical : !isCritical)
      return matchesSearch && matchesCategory && matchesStock
    })

    return filtered.sort((a, b) => {
      const deficitA = Math.max(0, a.min - a.qty)
      const deficitB = Math.max(0, b.min - b.qty)
      if (sortBy === 'name_asc') return a.name.localeCompare(b.name, 'uk')
      if (sortBy === 'qty_asc') return a.qty - b.qty
      if (sortBy === 'qty_desc') return b.qty - a.qty
      if (deficitA !== deficitB) return deficitB - deficitA
      return a.name.localeCompare(b.name, 'uk')
    })
  }, [supplies, search, filterCategory, filterStock, sortBy])

  return (
    <div className="flex-1 p-4 md:p-6 overflow-y-auto">
      <div className="flex justify-between items-start mb-4 md:mb-6">
        <div>
          <h1 className="text-xl font-bold tracking-widest text-white uppercase mb-1">МЕДИЧНІ ЗАПАСИ</h1>
          <p className="text-xs text-gray-500 font-mono tracking-widest uppercase">Інвентаризація ROLE-1 / СТАБПУНКТ</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4 md:mb-6">
        <div className="wolf-panel p-5 relative overflow-hidden md:col-span-3">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3 mb-4">
            <h2 className="text-sm font-bold tracking-widest uppercase text-white mb-2 flex items-center gap-2">
              <Package className="w-4 h-4 text-blue-500" /> НОМЕНКЛАТУРА ТА ЗАЛИШКИ
            </h2>
            <button
              onClick={syncSupplies}
              className="text-xs font-bold tracking-widest text-gray-400 hover:text-white uppercase flex items-center gap-2 border border-[#262a30] px-3 py-1 rounded bg-[#1a1d24]"
            >
              <RefreshCw className="w-3 h-3" /> СИНХРОНІЗУВАТИ
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-3">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Пошук по назві/категорії"
              className="wolf-input text-xs md:col-span-2"
            />
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="wolf-input text-xs"
            >
              <option value="all">Всі категорії</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
            <select
              value={filterStock}
              onChange={(e) => setFilterStock(e.target.value)}
              className="wolf-input text-xs"
            >
              <option value="all">Весь stock</option>
              <option value="critical">Тільки критичні</option>
              <option value="ok">Тільки в нормі</option>
            </select>
          </div>

          <div className="mb-3">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SuppliesSortKey)}
              className="wolf-input text-xs w-full md:w-80"
            >
              <option value="deficit_desc">Сортування: найбільший дефіцит</option>
              <option value="qty_asc">Сортування: залишок (зростання)</option>
              <option value="qty_desc">Сортування: залишок (спадання)</option>
              <option value="name_asc">Сортування: назва A-Z</option>
            </select>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left border-collapse mt-4">
              <thead>
                <tr className="border-b border-[#262a30] text-[10px] text-gray-500 uppercase tracking-widest">
                  <th className="py-2 px-2 font-medium">НАЙМЕНУВАННЯ</th>
                  <th className="py-2 px-2 font-medium">КАТЕГОРІЯ</th>
                  <th className="py-2 px-2 font-medium">МІНІМУМ</th>
                  <th className="py-2 px-2 font-medium">ЗАЛИШОК</th>
                  <th className="py-2 px-2 font-medium text-right">РУХ</th>
                </tr>
              </thead>
              <tbody>
                {tableItems.map(item => (
                  <tr key={item.id} className="border-b border-[#262a30]/50 hover:bg-[#1a1d24] transition-colors text-sm">
                    <td className="py-3 px-2 font-bold text-white">{item.name}</td>
                    <td className="py-3 px-2">
                      <span className="text-[10px] tracking-widest uppercase px-2 py-1 bg-[#0f1217] border border-[#262a30] text-gray-400 rounded-sm">
                        {item.category}
                      </span>
                    </td>
                    <td className="py-3 px-2 text-gray-500">{item.min}</td>
                    <td className="py-3 px-2">
                      <span className={`font-bold ${item.qty < item.min ? 'text-red-500' : 'text-green-500'}`}>
                        {item.qty}
                      </span>
                    </td>
                    <td className="py-3 px-2 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button onClick={() => updateQty(item.id, -1)} className="p-1 hover:bg-red-900/30 text-red-500 rounded"><MinusCircle className="w-4 h-4" /></button>
                        <button onClick={() => updateQty(item.id, 1)} className="p-1 hover:bg-green-900/30 text-green-500 rounded"><PlusCircle className="w-4 h-4" /></button>
                      </div>
                    </td>
                  </tr>
                ))}
                {tableItems.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-sm text-gray-500">Немає позицій за поточними фільтрами</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="wolf-panel p-5 relative overflow-hidden h-fit border-b-2 border-b-red-900/50">
          <h2 className="text-sm font-bold tracking-widest uppercase text-white mb-4 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500" /> КРИТИЧНА НЕСТАЧА
          </h2>
          {criticalItems.length === 0 ? (
            <div className="text-xs text-gray-500 mt-4 text-center">Запаси в нормі</div>
          ) : (
            <div className="space-y-3">
              {criticalItems.map(item => (
                <div key={item.id} className="p-2 border border-red-900/30 bg-red-900/10 rounded flex justify-between items-center">
                  <span className="text-xs font-bold text-red-400">{item.name}</span>
                  <span className="text-xs font-mono font-bold text-gray-400">{item.qty}/{item.min}</span>
                </div>
              ))}
              <button
                onClick={createRequisition}
                className="w-full mt-4 py-2 bg-orange-900/30 border border-orange-900 text-orange-400 text-[10px] tracking-widest uppercase font-bold rounded-sm hover:bg-orange-600 hover:text-white transition-colors"
              >
                ФОРМУВАТИ ЗАЯВКУ
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
