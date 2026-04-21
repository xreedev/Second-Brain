import { useRef, useEffect, useState } from 'react'
import { Send, Sparkles, FileText, User } from 'lucide-react'
import MarkdownRenderer from './MarkdownRenderer'
import { sendChat } from '../api/client'

function formatTime(date) {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function ChatView({ messages, setMessages, isLoading, setIsLoading, onSourceClick, activeSource }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  function autoResize(e) {
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 180) + 'px'
  }

  async function handleSend() {
    const q = input.trim()
    if (!q || isLoading) return

    const userMsg = { id: Date.now(), role: 'user', content: q, timestamp: Date.now() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    setIsLoading(true)

    try {
      const data = await sendChat(q)
      const assistantMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.result ?? '',
        sources: data.sources ?? [],
        documents: data.documents ?? [],
        timestamp: Date.now(),
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: `**Error:** ${err.message}`,
        sources: [],
        documents: [],
        timestamp: Date.now(),
      }])
    } finally {
      setIsLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-view">
      <div className="view-header">
        <div className="view-header-left">
          <span className="view-header-title">Research Chat</span>
          <span className="view-header-sub">Ask questions across your ingested knowledge base</span>
        </div>
        <div className="chat-status">
          <span className="status-dot" />
          Ready
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && !isLoading ? (
          <div className="chat-empty">
            <div className="chat-empty-icon"><Sparkles /></div>
            <h3>Start a conversation</h3>
            <p>
              Ask questions about your research papers. The AI will search your knowledge base
              and cite its sources.
            </p>
          </div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className={`message-row ${msg.role}`}>
              <div className="msg-avatar">
                {msg.role === 'user' ? <User /> : <Sparkles />}
              </div>
              <div className="msg-body">
                <div className="msg-name">{msg.role === 'user' ? 'You' : 'Nexus'}</div>
                <div className="msg-content">
                  {msg.role === 'assistant'
                    ? <MarkdownRenderer content={msg.content} />
                    : msg.content
                  }
                </div>
                {msg.sources?.length > 0 && (
                  <div className="msg-sources">
                    <span className="sources-label">Sources:</span>
                    {msg.sources.map((src, i) => (
                      <button
                        key={src + i}
                        className={`source-chip ${activeSource === src ? 'active' : ''}`}
                        onClick={() => onSourceClick(src, msg.documents ?? [])}
                      >
                        <FileText />
                        {src}
                      </button>
                    ))}
                  </div>
                )}
                <div className="msg-time">{formatTime(msg.timestamp)}</div>
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="message-row assistant">
            <div className="msg-avatar"><Sparkles /></div>
            <div className="msg-body">
              <div className="msg-name">Nexus</div>
              <div className="msg-content">
                <div className="thinking">
                  <span /><span /><span />
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        <div className="chat-input-box">
          <textarea
            ref={textareaRef}
            className="chat-textarea"
            rows={1}
            placeholder="Ask a question about your research…"
            value={input}
            onChange={e => { setInput(e.target.value); autoResize(e) }}
            onKeyDown={handleKeyDown}
          />
          <button
            className="chat-send-btn"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
          >
            <Send />
          </button>
        </div>
        <div className="chat-input-hint">Press Enter to send · Shift+Enter for new line</div>
      </div>
    </div>
  )
}
