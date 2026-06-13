import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Copy, Check } from 'lucide-react'
import { useState } from 'react'

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleCopy}
      className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-200"
      title="Copy"
    >
      {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
    </button>
  )
}

export default function MessageBubble({ message, isStreaming }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} fade-in-up`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-xs mr-2 mt-1 flex-shrink-0">
          🤖
        </div>
      )}

      <div className={`max-w-[85%] ${isUser ? 'order-1' : 'order-2'}`}>
        <div
          className={`
            rounded-2xl px-4 py-3 text-sm leading-relaxed group relative
            ${isUser
              ? 'bg-blue-600 text-white rounded-tr-sm'
              : 'bg-slate-800/80 border border-slate-700/60 text-slate-200 rounded-tl-sm'
            }
          `}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <>
              <div className="absolute top-2 right-2">
                <CopyButton text={message.content} />
              </div>
              <div className={`markdown-content ${isStreaming ? 'typing-cursor' : ''}`}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            </>
          )}
        </div>
      </div>

      {isUser && (
        <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center text-xs ml-2 mt-1 flex-shrink-0">
          👤
        </div>
      )}
    </div>
  )
}
