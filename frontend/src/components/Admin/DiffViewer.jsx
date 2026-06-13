import { useState } from 'react'
import { GitCompare, X, Loader2, AlertCircle, ArrowRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function DiffViewer({ projectId, initialFilename, initialVersionA, initialVersionB, onClose }) {
  const [filename, setFilename] = useState(initialFilename || '')
  const [versionA, setVersionA] = useState(initialVersionA || 1)
  const [versionB, setVersionB] = useState(initialVersionB || 2)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Auto-run if invoked with preset values
  useState(() => {
    if (initialFilename && initialVersionA && initialVersionB) {
      handleCompare()
    }
  })

  async function handleCompare() {
    if (!filename.trim()) {
      setError('Vui lòng nhập tên file')
      return
    }
    if (versionA === versionB) {
      setError('Phải chọn 2 version khác nhau')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const res = await fetch(`${BASE_URL}/api/v1/projects/${projectId}/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: filename.trim(),
          version_a: Number(versionA),
          version_b: Number(versionB),
        })
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Lỗi phân tích')
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <GitCompare size={18} className="text-amber-400" />
            <h2 className="font-semibold text-slate-100">So sánh phiên bản tài liệu</h2>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Controls */}
        <div className="px-6 py-4 border-b border-slate-800 flex-shrink-0">
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="block text-xs text-slate-500 mb-1.5 font-medium">Tên file</label>
              <input
                value={filename}
                onChange={e => setFilename(e.target.value)}
                placeholder="topup_spec.md"
                disabled={loading}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 outline-none focus:border-amber-500/60 font-mono"
              />
            </div>
            <div className="w-24">
              <label className="block text-xs text-slate-500 mb-1.5 font-medium">Version cũ</label>
              <input
                type="number" min={1} value={versionA}
                onChange={e => setVersionA(Number(e.target.value))}
                disabled={loading}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 text-center outline-none focus:border-amber-500/60"
              />
            </div>
            <div className="pb-2 text-slate-600">
              <ArrowRight size={16} />
            </div>
            <div className="w-24">
              <label className="block text-xs text-slate-500 mb-1.5 font-medium">Version mới</label>
              <input
                type="number" min={1} value={versionB}
                onChange={e => setVersionB(Number(e.target.value))}
                disabled={loading}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 text-center outline-none focus:border-amber-500/60"
              />
            </div>
            <button
              onClick={handleCompare}
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm font-medium transition-colors flex items-center gap-2 whitespace-nowrap"
            >
              {loading
                ? <><Loader2 size={14} className="animate-spin" /> Đang phân tích...</>
                : <><GitCompare size={14} /> Phân tích</>
              }
            </button>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-red-400 text-xs mt-3 bg-red-950/30 border border-red-900/40 rounded-lg px-3 py-2">
              <AlertCircle size={13} />
              {error}
            </div>
          )}
        </div>

        {/* Result */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 text-slate-500">
              <Loader2 size={32} className="animate-spin mb-4 text-amber-400" />
              <p className="text-sm">Qwen đang phân tích thay đổi...</p>
              <p className="text-xs mt-1 text-slate-600">Thường mất 5-10 giây</p>
            </div>
          )}

          {!loading && !result && !error && (
            <div className="flex flex-col items-center justify-center py-12 text-slate-600">
              <GitCompare size={40} className="mb-4 opacity-30" />
              <p className="text-sm">Chọn file và 2 version để bắt đầu phân tích</p>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              {/* Version badges */}
              <div className="flex items-center gap-2 text-xs text-slate-500 pb-2 border-b border-slate-800">
                <span className="font-mono bg-slate-800 px-2 py-1 rounded text-slate-400">
                  {result.filename}
                </span>
                <span className="bg-red-950/40 border border-red-900/40 text-red-400 px-2 py-1 rounded font-mono">
                  v{result.version_old}
                </span>
                <ArrowRight size={12} />
                <span className="bg-emerald-950/40 border border-emerald-900/40 text-emerald-400 px-2 py-1 rounded font-mono">
                  v{result.version_new}
                </span>
              </div>

              {/* Analysis markdown */}
              <div className="markdown-content text-sm">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {result.analysis}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
