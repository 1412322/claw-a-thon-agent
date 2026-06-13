import { createContext, useContext, useState } from 'react'

const GlobalContext = createContext(null)

export function GlobalProvider({ children }) {
  const [currentProjectId, setCurrentProjectId] = useState('')
  const [currentProjectName, setCurrentProjectName] = useState('')
  const [userRole, setUserRole] = useState('qc') // 'qc' | 'dev'
  const [projects, setProjects] = useState([])

  const selectProject = (id, name) => {
    setCurrentProjectId(id)
    setCurrentProjectName(name)
  }

  return (
    <GlobalContext.Provider value={{
      currentProjectId,
      currentProjectName,
      userRole,
      setUserRole,
      projects,
      setProjects,
      selectProject,
    }}>
      {children}
    </GlobalContext.Provider>
  )
}

export function useGlobal() {
  return useContext(GlobalContext)
}
