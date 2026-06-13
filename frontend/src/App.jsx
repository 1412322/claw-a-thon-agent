import { useState } from 'react'
import { GlobalProvider } from './store/globalContext'
import Sidebar from './components/Chat/Sidebar'
import ChatWindow from './components/Chat/ChatWindow'
import APITesting from './components/APITesting'
import AdminPortal from './components/Admin/AdminPortal'

function AppContent() {
  const [showAdmin, setShowAdmin] = useState(false)
  const [activeTab, setActiveTab] = useState('chat') // 'chat' or 'api-testing'

  return (
    <div className="flex h-screen bg-[#0d0f12] overflow-hidden">
      <Sidebar onAddProject={() => setShowAdmin(true)} />

      <main className="flex-1 flex flex-col min-w-0">
        {activeTab === 'chat' ? (
          <ChatWindow />
        ) : (
          <APITesting />
        )}
      </main>

      {/* Tab Switcher */}
      <div className="fixed top-4 left-64 right-4 z-50 flex justify-center">
        <div className="bg-slate-800/80 backdrop-blur rounded-full p-1 border border-slate-700">
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
              activeTab === 'chat'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            💬 Chat
          </button>
          <button
            onClick={() => setActiveTab('api-testing')}
            className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
              activeTab === 'api-testing'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            🧪 API Testing
          </button>
        </div>
      </div>

      {showAdmin && (
        <AdminPortal onClose={() => setShowAdmin(false)} />
      )}
    </div>
  )
}

export default function App() {
  return (
    <GlobalProvider>
      <AppContent />
    </GlobalProvider>
  )
}
