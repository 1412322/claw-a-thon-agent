import { useState, useRef, useEffect } from 'react'
import { Send, AlertCircle } from 'lucide-react'
import { useGlobal } from '../../store/globalContext'
import { streamChat } from '../../services/api'
import MessageBubble from './MessageBubble'
import QuickPrompts from './QuickPrompts'

function TypingIndicator() {
  return (
    <div className="flex justify-start fade-in-up">
      <div className="w-7 h-7 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-xs mr-2 mt-1">
        🤖
      </div>
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex gap-1.5 items-center h-4">
          <div className="w-1.5 h-1.5 rounded-full bg-blue-400 dot-1" />
          <div className="w-1.5 h-1.5 rounded-full bg-blue-400 dot-2" />
          <div className="w-1.5 h-1.5 rounded-full bg-blue-400 dot-3" />
        </div>
      </div>
    </div>
  )
}

export default function ChatWindow() {
  const { currentProjectId, currentProjectName, userRole } = useGlobal()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Reset chat when project changes
  useEffect(() => {
    setMessages([])
    setError('')
  }, [currentProjectId])

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || isStreaming) return

    if (!currentProjectId) {
      setError('Vui lòng chọn dự án trước khi chat.')
      return
    }

    setError('')
    const userMsg = { role: 'user', content: trimmed }
    const history = [...messages]
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsStreaming(true)

    const assistantMsg = { role: 'assistant', content: '' }
    setMessages(prev => [...prev, assistantMsg])

    await streamChat({
      projectId: currentProjectId,
      userRole,
      message: trimmed,
      history,
      onChunk: (chunk) => {
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: updated[updated.length - 1].content + chunk,
          }
          return updated
        })
      },
      onDone: () => setIsStreaming(false),
      onError: (err) => {
        setIsStreaming(false)
        setError(`Lỗi: ${err.message}`)
        setMessages(prev => prev.slice(0, -1)) // Remove empty assistant message
      },
    })
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleQuickPrompt = (template) => {
    setInput(template)
    textareaRef.current?.focus()
  }

  const noProject = !currentProjectId

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          {noProject ? (
            <p className="text-slate-500 text-sm">← Chọn một dự án để bắt đầu</p>
          ) : (
            <div>
              <h2 className="font-semibold text-slate-100">{currentProjectName}</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {messages.filter(m => m.role === 'user').length} câu hỏi trong phiên này
              </p>
            </div>
          )}
        </div>

        {!noProject && (
          <button
            onClick={() => setMessages([])}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors px-2 py-1 rounded hover:bg-slate-800"
          >
            Xóa lịch sử
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && !noProject && (
          <div className="flex flex-col items-center justify-center h-full text-center fade-in-up">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-slate-300 font-medium mb-2">
              Agent sẵn sàng — dự án <span className="text-blue-400">{currentProjectName}</span>
            </h3>
            <p className="text-slate-500 text-sm max-w-sm">
              Sử dụng các phím tắt bên dưới hoặc gõ câu hỏi trực tiếp.
              Tài liệu đặc tả dự án đã được nạp vào bộ nhớ.
            </p>
          </div>
        )}

        {noProject && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-5xl mb-4">📂</div>
            <h3 className="text-slate-400 font-medium mb-2">Chưa chọn dự án</h3>
            <p className="text-slate-600 text-sm">
              Chọn dự án từ sidebar hoặc tạo dự án mới và upload tài liệu
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            isStreaming={isStreaming && i === messages.length - 1 && msg.role === 'assistant'}
          />
        ))}

        {isStreaming && messages[messages.length - 1]?.content === '' && (
          <TypingIndicator />
        )}

        {error && (
          <div className="flex items-center gap-2 text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded-lg px-4 py-3">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts */}
      {!noProject && (
        <QuickPrompts role={userRole} onSelect={handleQuickPrompt} />
      )}

      {/* Input */}
      <div className="px-4 pb-4 pt-2">
        <div className={`flex gap-2 items-end bg-slate-800/60 border rounded-xl px-4 py-3 transition-colors ${
          noProject ? 'border-slate-800 opacity-50' : 'border-slate-700 focus-within:border-blue-500/50'
        }`}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={noProject ? 'Chọn dự án trước...' : `Hỏi Agent về dự án ${currentProjectName}... (Enter để gửi)`}
            disabled={noProject || isStreaming}
            rows={1}
            className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-600 resize-none outline-none min-h-[24px] max-h-[120px] leading-6"
            style={{ height: 'auto' }}
            onInput={e => {
              e.target.style.height = 'auto'
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming || noProject}
            className="w-8 h-8 flex items-center justify-center rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white transition-colors flex-shrink-0"
          >
            <Send size={15} />
          </button>
        </div>
        <p className="text-center text-xs text-slate-700 mt-2">
          Shift+Enter để xuống dòng · Agent chỉ trả lời dựa trên tài liệu đặc tả đã nạp
        </p>
      </div>
    </div>
  )
}
