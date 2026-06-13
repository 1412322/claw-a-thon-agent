import { useState, useRef } from 'react'
import { X, Upload, FileText, CheckCircle, AlertCircle, Loader2, FolderPlus, History, GitCompare } from 'lucide-react'
import { uploadDocument, fetchProjects } from '../../services/api'
import { useGlobal } from '../../store/globalContext'
import VersionHistory from './VersionHistory'
import DiffViewer from './DiffViewer'

const ACCEPTED_TYPES = '.pdf,.docx,.doc,.md,.txt'

// ─── Tab enum ────────────────────────────────
const TAB_UPLOAD = 'upload'
const TAB_HISTORY = 'history'

// ─── Dropzone ────────────────────────────────
function FileDropzone({ onFiles }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    onFiles(Array.from(e.dataTransfer.files))
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current.click()}
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
        dragging
          ? 'border-blue-500 bg-blue-950/30'
          : 'border-slate-700 hover:border-slate-600 hover:bg-slate-800/30'
      }`}
    >
      <Upload size={28} className="mx-auto mb-3 text-slate-500" />
      <p className="text-slate-300 text-sm font-medium mb-1">Kéo thả file vào đây</p>
      <p className="text-slate-600 text-xs">hoặc click để chọn file</p>
      <p className="text-slate-700 text-xs mt-2">PDF, DOCX, MD, TXT — tối đa 20MB</p>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED_TYPES}
        className="hidden"
        onChange={(e) => onFiles(Array.from(e.target.files))}
      />
    </div>
  )
}

// ─── Upload item row ──────────────────────────
function UploadItem({ file, status, message, version, isNewVersion }) {
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-slate-800/60 last:border-0">
      <FileText size={15} className="text-slate-500 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-300 truncate">{file.name}</p>
        {message && (
          <p className={`text-xs mt-0.5 ${status === 'error' ? 'text-red-400' : 'text-slate-500'}`}>
            {message}
          </p>
        )}
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        {/* Version badge */}
        {status === 'success' && version && (
          <span className={`text-xs px-2 py-0.5 rounded-full font-mono font-medium ${
            isNewVersion
              ? 'bg-amber-600/20 border border-amber-500/40 text-amber-300'
              : 'bg-blue-600/20 border border-blue-500/40 text-blue-300'
          }`}>
            v{version}{isNewVersion ? ' 🆕' : ''}
          </span>
        )}

        {/* Status icon */}
        {status === 'pending'   && <div className="w-4 h-4 rounded-full border-2 border-slate-700" />}
        {status === 'uploading' && <Loader2 size={16} className="animate-spin text-blue-400" />}
        {status === 'success'   && <CheckCircle size={16} className="text-emerald-400" />}
        {status === 'error'     && <AlertCircle size={16} className="text-red-400" />}
      </div>
    </div>
  )
}

// ─── Main AdminPortal ─────────────────────────
export default function AdminPortal({ onClose }) {
  const { setProjects, selectProject, currentProjectId, currentProjectName } = useGlobal()

  // Tab state
  const [activeTab, setActiveTab] = useState(TAB_UPLOAD)

  // Upload state
  const [projectId, setProjectId]     = useState(currentProjectId || '')
  const [projectName, setProjectName] = useState(currentProjectName || '')
  const [files, setFiles]             = useState([])
  const [uploadItems, setUploadItems] = useState([])
  const [uploading, setUploading]     = useState(false)
  const [done, setDone]               = useState(false)
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0)

  // Diff state
  const [diffConfig, setDiffConfig] = useState(null) // { filename, versionA, versionB }

  // ── Handlers ──────────────────────────────────
  const handleFiles = (newFiles) => {
    setFiles(prev => {
      const existing = new Set(prev.map(f => f.name))
      return [...prev, ...newFiles.filter(f => !existing.has(f.name))]
    })
  }

  const handleUpload = async () => {
    if (!projectId.trim() || !projectName.trim() || files.length === 0) return
    setUploading(true)
    setUploadItems(files.map(f => ({ file: f, status: 'pending', message: '', version: null, isNewVersion: false })))

    for (let i = 0; i < files.length; i++) {
      setUploadItems(prev => {
        const u = [...prev]; u[i] = { ...u[i], status: 'uploading' }; return u
      })
      try {
        const result = await uploadDocument(projectId.trim(), projectName.trim(), files[i])
        setUploadItems(prev => {
          const u = [...prev]
          u[i] = {
            ...u[i],
            status: 'success',
            message: result.message,
            version: result.version,
            isNewVersion: result.is_new_version,
          }
          return u
        })
      } catch (err) {
        setUploadItems(prev => {
          const u = [...prev]; u[i] = { ...u[i], status: 'error', message: err.message }; return u
        })
      }
    }

    // Refresh project list
    try {
      const projects = await fetchProjects()
      setProjects(projects)
      selectProject(projectId.trim(), projectName.trim())
    } catch { /* ignore */ }

    setUploading(false)
    setDone(true)
    setHistoryRefreshKey(k => k + 1)
  }

  const handleCompare = (filename, versionA, versionB) => {
    setDiffConfig({ filename, versionA, versionB })
  }

  const handleSwitchToHistory = () => {
    if (done) {
      setActiveTab(TAB_HISTORY)
      setHistoryRefreshKey(k => k + 1)
    }
  }

  const canUpload = projectId.trim() && projectName.trim() && files.length > 0 && !uploading

  // ── Render ─────────────────────────────────────
  return (
    <>
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl flex flex-col max-h-[90vh]">

          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 flex-shrink-0">
            <div className="flex items-center gap-2.5">
              <FolderPlus size={18} className="text-blue-400" />
              <h2 className="font-semibold text-slate-100">Quản lý tài liệu dự án</h2>
            </div>
            <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
              <X size={18} />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-slate-800 flex-shrink-0">
            {[
              { id: TAB_UPLOAD,  label: 'Upload tài liệu', icon: Upload },
              { id: TAB_HISTORY, label: 'Lịch sử version',  icon: History },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => {
                  setActiveTab(id)
                  if (id === TAB_HISTORY) setHistoryRefreshKey(k => k + 1)
                }}
                className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors ${
                  activeTab === id
                    ? 'text-blue-400 border-b-2 border-blue-500'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                <Icon size={14} />
                {label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">

            {/* ── UPLOAD TAB ── */}
            {activeTab === TAB_UPLOAD && (
              <>
                {/* Project info */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-slate-500 mb-1.5 font-medium">Mã dự án *</label>
                    <input
                      value={projectId}
                      onChange={e => setProjectId(e.target.value.toLowerCase().replace(/\s+/g, '_'))}
                      placeholder="zalopay, ecommerce..."
                      disabled={uploading}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 outline-none focus:border-blue-500/60 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 mb-1.5 font-medium">Tên dự án *</label>
                    <input
                      value={projectName}
                      onChange={e => setProjectName(e.target.value)}
                      placeholder="ZaloPay Super App..."
                      disabled={uploading}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 outline-none focus:border-blue-500/60"
                    />
                  </div>
                </div>

                {/* Dropzone */}
                {!done && <FileDropzone onFiles={handleFiles} />}

                {/* File list */}
                {(files.length > 0 || done) && (
                  <div className="bg-slate-800/40 rounded-xl px-4">
                    {(done ? uploadItems : files.map(f => ({ file: f, status: 'pending', message: '' }))).map((item, i) => (
                      <UploadItem
                        key={i}
                        file={item.file}
                        status={item.status}
                        message={item.message}
                        version={item.version}
                        isNewVersion={item.isNewVersion}
                      />
                    ))}
                  </div>
                )}

                {/* Actions */}
                {!done ? (
                  <button
                    onClick={handleUpload}
                    disabled={!canUpload}
                    className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-sm font-medium transition-all flex items-center justify-center gap-2"
                  >
                    {uploading
                      ? <><Loader2 size={16} className="animate-spin" /> Đang nạp tài liệu...</>
                      : <><Upload size={16} /> Upload & Nạp vào Agent</>
                    }
                  </button>
                ) : (
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setFiles([]); setUploadItems([]); setDone(false)
                      }}
                      className="flex-1 py-2.5 rounded-xl border border-slate-700 text-slate-400 text-sm font-medium hover:bg-slate-800 transition-all"
                    >
                      Upload thêm
                    </button>
                    <button
                      onClick={handleSwitchToHistory}
                      className="flex-1 py-2.5 rounded-xl bg-amber-600/20 border border-amber-500/40 text-amber-300 text-sm font-medium hover:bg-amber-600/30 transition-all flex items-center justify-center gap-2"
                    >
                      <GitCompare size={14} />
                      Xem & So sánh version
                    </button>
                  </div>
                )}

                {!done && (
                  <button
                    onClick={onClose}
                    className="w-full py-2 text-slate-600 text-xs hover:text-slate-400 transition-colors"
                  >
                    Đóng
                  </button>
                )}
              </>
            )}

            {/* ── HISTORY TAB ── */}
            {activeTab === TAB_HISTORY && (
              <>
                {/* Project selector nếu chưa có */}
                {!currentProjectId && (
                  <div>
                    <label className="block text-xs text-slate-500 mb-1.5 font-medium">Mã dự án</label>
                    <input
                      value={projectId}
                      onChange={e => setProjectId(e.target.value.toLowerCase().replace(/\s+/g, '_'))}
                      placeholder="zalopay..."
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 outline-none focus:border-blue-500/60 font-mono"
                    />
                  </div>
                )}

                <VersionHistory
                  projectId={currentProjectId || projectId}
                  onCompare={handleCompare}
                  refreshKey={historyRefreshKey}
                />
              </>
            )}
          </div>
        </div>
      </div>

      {/* DiffViewer modal — on top of AdminPortal */}
      {diffConfig && (
        <DiffViewer
          projectId={currentProjectId || projectId}
          initialFilename={diffConfig.filename}
          initialVersionA={diffConfig.versionA}
          initialVersionB={diffConfig.versionB}
          onClose={() => setDiffConfig(null)}
        />
      )}
    </>
  )
}
