import { useState, useEffect } from 'react'
import { History, ChevronDown, ChevronUp, Clock, Layers, GitCompare } from 'lucide-react'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function formatDate(iso) {
  const d = new Date(iso)
  return d.toLocaleDateString('vi-VN', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

function VersionBadge({ version, isLatest }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-mono font-medium ${
      isLatest
        ? 'bg-blue-600/20 border border-blue-500/40 text-blue-300'
        : 'bg-slate-700/60 border border-slate-600/40 text-slate-400'
    }`}>
      v{version}
      {isLatest && <span className="text-blue-400 text-[10px]">latest</span>}
    </span>
  )
}

function FileVersionRow({ doc, projectId, onCompare }) {
  const [expanded, setExpanded] = useState(false)
  const [versions, setVersions] = useState([])
  const [loading, setLoading] = useState(false)

  const loadVersions = async () => {
    if (versions.length > 0) {
      setExpanded(!expanded)
      return
    }
    setLoading(true)
    try {
      const res = await fetch(
        `${BASE_URL}/api/v1/projects/${projectId}/versions/${encodeURIComponent(doc.filename)}`
      )
      const data = await res.json()
      setVersions(data)
      setExpanded(true)
    } catch {
      setVersions([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="border border-slate-700/60 rounded-xl overflow-hidden">
      {/* File header */}
      <button
        onClick={loadVersions}
        className="w-full flex items-center justify-between px-4 py-3 bg-slate-800/40 hover:bg-slate-800/70 transition-colors"
      >
        <div className="flex items-center gap-3 min-w-0">
          <History size={15} className="text-slate-500 flex-shrink-0" />
          <span className="text-sm text-slate-200 font-medium truncate">{doc.filename}</span>
          <VersionBadge version={doc.latest_version} isLatest={true} />
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <span className="text-xs text-slate-500 flex items-center gap-1">
            <Layers size={11} />
            {doc.total_versions} version
          </span>
          {loading ? (
            <div className="w-4 h-4 border-2 border-slate-600 border-t-blue-400 rounded-full animate-spin" />
          ) : expanded ? (
            <ChevronUp size={15} className="text-slate-500" />
          ) : (
            <ChevronDown size={15} className="text-slate-500" />
          )}
        </div>
      </button>

      {/* Version list */}
      {expanded && versions.length > 0 && (
        <div className="border-t border-slate-700/60">
          {versions.map((v, i) => (
            <div
              key={v.version}
              className={`flex items-center justify-between px-4 py-2.5 ${
                i < versions.length - 1 ? 'border-b border-slate-800/60' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <VersionBadge version={v.version} isLatest={i === versions.length - 1} />
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <Clock size={10} />
                  {formatDate(v.uploaded_at)}
                </span>
                {v.chunks_count > 0 && (
                  <span className="text-xs text-slate-600">{v.chunks_count} chunks</span>
                )}
              </div>

              {/* Compare button — only show if there's a previous version */}
              {i > 0 && (
                <button
                  onClick={() => onCompare(doc.filename, versions[i - 1].version, v.version)}
                  className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg border border-amber-600/30 text-amber-400 hover:bg-amber-950/30 hover:border-amber-500/50 transition-all"
                >
                  <GitCompare size={12} />
                  So sánh v{versions[i - 1].version} → v{v.version}
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function VersionHistory({ projectId, onCompare, refreshKey }) {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    fetch(`${BASE_URL}/api/v1/projects/${projectId}/versions`)
      .then(r => r.json())
      .then(data => {
        setDocs(Array.isArray(data) ? data : [])
      })
      .catch(() => setDocs([]))
      .finally(() => setLoading(false))
  }, [projectId, refreshKey])

  if (!projectId) return null

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <History size={15} className="text-slate-400" />
        <h3 className="text-sm font-medium text-slate-300">Lịch sử phiên bản tài liệu</h3>
      </div>

      {loading && (
        <p className="text-xs text-slate-600 text-center py-4">Đang tải...</p>
      )}

      {!loading && docs.length === 0 && (
        <p className="text-xs text-slate-600 text-center py-4">
          Chưa có tài liệu nào. Upload file để bắt đầu.
        </p>
      )}

      {docs.map(doc => (
        <FileVersionRow
          key={doc.filename}
          doc={doc}
          projectId={projectId}
          onCompare={onCompare}
        />
      ))}
    </div>
  )
}
