import { useState } from 'react'
import { X, FileText, AlignLeft, ExternalLink } from 'lucide-react'

export default function SourcePanel({ source, onClose }) {
  const [tab, setTab] = useState('text')
  const { name, documents } = source

  // documents is either List[List[str]] or flat List[str]
  const chunks = Array.isArray(documents?.[0])
    ? documents.flat()
    : documents ?? []

  const pdfUrl = `/source-files/${encodeURIComponent(name)}`

  return (
    <aside className="source-panel">
      <div className="source-panel-header">
        <div className="source-panel-title">
          <FileText />
          <span className="source-panel-name" title={name}>{name}</span>
        </div>
        <button className="close-btn" onClick={onClose} title="Close">
          <X />
        </button>
      </div>

      <div className="source-tabs">
        <button className={`src-tab ${tab === 'text' ? 'active' : ''}`} onClick={() => setTab('text')}>
          Excerpts
        </button>
        <button className={`src-tab ${tab === 'pdf' ? 'active' : ''}`} onClick={() => setTab('pdf')}>
          PDF View
        </button>
      </div>

      {tab === 'text' && (
        <div className="source-panel-body">
          {chunks.length === 0 ? (
            <div className="source-empty">No excerpts available for this source.</div>
          ) : (
            chunks.map((chunk, i) => (
              <div key={i} className="source-chunk">
                <div className="source-chunk-num">Excerpt {i + 1}</div>
                <div className="source-chunk-text">{chunk}</div>
              </div>
            ))
          )}
        </div>
      )}

      {tab === 'pdf' && (
        <div className="source-pdf-wrap">
          <div style={{
            padding: '8px 14px',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexShrink: 0,
          }}>
            <span style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>Viewing: {name}</span>
            <a
              href={pdfUrl}
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'flex', alignItems: 'center', gap: 4,
                fontSize: 11.5, color: 'var(--accent-text)', textDecoration: 'none',
              }}
            >
              <ExternalLink size={11} /> Open
            </a>
          </div>
          <iframe
            className="source-pdf-frame"
            src={pdfUrl}
            title={name}
          />
        </div>
      )}
    </aside>
  )
}
