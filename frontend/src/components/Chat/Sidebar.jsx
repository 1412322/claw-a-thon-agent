import { useState, useEffect } from 'react'
import { FolderOpen, Plus, RefreshCw, Code2, TestTube2, ChevronRight, FileText, Layers } from 'lucide-react'
import { useGlobal } from '../../store/globalContext'
import { fetchProjects } from '../../services/api'

function RoleBadge({ role, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
        active
          ? role === 'qc'
            ? 'bg-emerald-600/20 border border-emerald-500/40 text-emerald-400'
            : 'bg-blue-600/20 border border-blue-500/40 text-blue-400'
          : 'border border-transparent text-slate-500 hover:text-slate-300'
      }`}
    >
      {role === 'qc' ? <TestTube2 size={13} /> : <Code2 size={13} />}
      {role === 'qc' ? 'QC' : 'Dev'}
    </button>
  )
}

function ProjectItem({ project, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-3 py-2.5 rounded-lg transition-all group ${
        active
          ? 'bg-blue-600/15 border border-blue-500/30'
          : 'hover:bg-slate-800/60 border border-transparent'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <FolderOpen size={14} className={active ? 'text-blue-400' : 'text-slate-500'} />
          <span className={`text-sm truncate font-medium ${active ? 'text-blue-300' : 'text-slate-300'}`}>
            {project.project_name}
          </span>
        </div>
        <ChevronRight size={12} className={`flex-shrink-0 transition-transform ${active ? 'text-blue-400 rotate-90' : 'text-slate-600'}`} />
      </div>
      <div className="flex items-center gap-3 mt-1 pl-5">
        <span className="text-xs text-slate-600 flex items-center gap-1">
          <FileText size={10} />
          {project.documents.length} file
        </span>
        <span className="text-xs text-slate-600 flex items-center gap-1">
          <Layers size={10} />
          {project.total_chunks} chunks
        </span>
      </div>
    </button>
  )
}

export default function Sidebar({ onAddProject }) {
  const { currentProjectId, userRole, setUserRole, projects, setProjects, selectProject } = useGlobal()
  const [loading, setLoading] = useState(false)

  const loadProjects = async () => {
    setLoading(true)
    try {
      const data = await fetchProjects()
      setProjects(data)
    } catch {
      // Backend may not be running yet in demo
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProjects()
  }, [])

  return (
    <div className="w-64 flex-shrink-0 bg-slate-900/60 border-r border-slate-800 flex flex-col h-full">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-sm">
            🤖
          </div>
          <div>
            <h1 className="text-sm font-semibold text-slate-100">Tech Agent</h1>
            <p className="text-xs text-slate-500">AI Co-Pilot</p>
          </div>
        </div>
      </div>

      {/* Role Switcher */}
      <div className="px-4 py-3 border-b border-slate-800">
        <p className="text-xs text-slate-600 mb-2 uppercase tracking-wider font-medium">Vai trò</p>
        <div className="flex gap-1 bg-slate-800/50 rounded-lg p-1">
          <RoleBadge role="qc" active={userRole === 'qc'} onClick={() => setUserRole('qc')} />
          <RoleBadge role="dev" active={userRole === 'dev'} onClick={() => setUserRole('dev')} />
        </div>
      </div>

      {/* Projects */}
      <div className="flex-1 overflow-y-auto px-3 py-3">
        <div className="flex items-center justify-between mb-2 px-1">
          <p className="text-xs text-slate-600 uppercase tracking-wider font-medium">Dự án</p>
          <button
            onClick={loadProjects}
            className="text-slate-600 hover:text-slate-400 transition-colors"
            title="Làm mới"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        <div className="space-y-1">
          {projects.length === 0 && !loading && (
            <p className="text-xs text-slate-600 px-2 py-4 text-center">
              Chưa có dự án nào.<br />Tạo dự án mới để bắt đầu.
            </p>
          )}

          {projects.map(project => (
            <ProjectItem
              key={project.project_id}
              project={project}
              active={currentProjectId === project.project_id}
              onClick={() => selectProject(project.project_id, project.project_name)}
            />
          ))}
        </div>
      </div>

      {/* Add Project Button */}
      <div className="px-3 pb-4 border-t border-slate-800 pt-3">
        <button
          onClick={onAddProject}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg border border-dashed border-slate-700 text-slate-500 hover:border-blue-500/50 hover:text-blue-400 hover:bg-blue-950/20 transition-all text-sm"
        >
          <Plus size={15} />
          Thêm dự án
        </button>
      </div>
    </div>
  )
}
