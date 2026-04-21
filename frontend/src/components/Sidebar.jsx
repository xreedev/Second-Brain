import { MessageSquare, BookOpen, Upload, Cpu, FileText } from 'lucide-react'
import { APP_CONFIG } from '../config'

const NAV_ITEMS = [
  { id: 'chat',   label: 'Chat',       icon: MessageSquare },
  { id: 'wiki',   label: 'Knowledge',  icon: BookOpen },
  { id: 'ingest', label: 'Ingest',     icon: Upload },
]

export default function Sidebar({ activeView, setActiveView, messages, ingestedFiles, onSourceClick }) {
  const lastAssistantMsg = [...messages].reverse().find(m => m.role === 'assistant' && m.sources?.length)

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <Cpu />
        </div>
        <div className="sidebar-brand">
          <span className="sidebar-app-name">{APP_CONFIG.name}</span>
          <span className="sidebar-app-tag">{APP_CONFIG.tagline}</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={`nav-item ${activeView === id ? 'active' : ''}`}
            onClick={() => setActiveView(id)}
          >
            <Icon />
            {label}
          </button>
        ))}
      </nav>

      <div className="sidebar-section">
        {activeView === 'chat' && (
          <>
            {messages.length > 0 && (
              <>
                <div className="sidebar-section-label">Conversation</div>
                {messages.filter(m => m.role === 'user').slice(-8).map(m => (
                  <div
                    key={m.id}
                    className="file-list-item"
                    title={m.content}
                  >
                    <MessageSquare />
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {m.content.slice(0, 48)}{m.content.length > 48 ? '…' : ''}
                    </span>
                  </div>
                ))}
              </>
            )}
            {lastAssistantMsg?.sources?.length > 0 && (
              <>
                <div className="sidebar-section-label" style={{ marginTop: 12 }}>Recent Sources</div>
                {lastAssistantMsg.sources.map((src, i) => (
                  <button
                    key={src}
                    className="file-list-item"
                    onClick={() => onSourceClick(src, lastAssistantMsg.documents?.[0] ?? [])}
                  >
                    <FileText />
                    {src}
                  </button>
                ))}
              </>
            )}
            {messages.length === 0 && (
              <div className="sidebar-empty">
                Start a conversation to explore your knowledge base.
              </div>
            )}
          </>
        )}

        {activeView === 'ingest' && (
          <>
            <div className="sidebar-section-label">Ingested Files</div>
            {ingestedFiles.length === 0 ? (
              <div className="sidebar-empty">No files ingested yet. Upload a PDF to begin.</div>
            ) : (
              ingestedFiles.map(f => (
                <div key={f} className="file-list-item" title={f}>
                  <FileText />
                  {f}
                </div>
              ))
            )}
          </>
        )}

        {activeView === 'wiki' && (
          <div className="sidebar-empty">
            Browse and view your generated knowledge base from the main panel.
          </div>
        )}
      </div>
    </aside>
  )
}
