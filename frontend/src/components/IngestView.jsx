import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, CheckCircle, XCircle, Loader, FilePlus } from 'lucide-react'
import { ingestPdf } from '../api/client'

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function IngestView({ onIngestComplete }) {
  const [queue, setQueue] = useState([])

  const updateItem = useCallback((id, patch) => {
    setQueue(prev => prev.map(item => item.id === id ? { ...item, ...patch } : item))
  }, [])

  const processFile = useCallback(async (file, id) => {
    updateItem(id, { status: 'uploading', progress: 20 })
    try {
      updateItem(id, { progress: 60 })
      const result = await ingestPdf(file)
      updateItem(id, { status: 'success', progress: 100, result })
      onIngestComplete(result.file_source ?? file.name)
    } catch (err) {
      updateItem(id, { status: 'error', error: err.message, progress: 0 })
    }
  }, [onIngestComplete, updateItem])

  const onDrop = useCallback((accepted) => {
    const newItems = accepted.map(file => ({
      id: `${file.name}-${Date.now()}`,
      file,
      status: 'pending',
      progress: 0,
    }))
    setQueue(prev => [...prev, ...newItems])
    newItems.forEach(item => processFile(item.file, item.id))
  }, [processFile])

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    noClick: true,
    noKeyboard: true,
  })

  return (
    <div className="ingest-view">
      <div className="view-header">
        <div className="view-header-left">
          <span className="view-header-title">Ingest Papers</span>
          <span className="view-header-sub">Upload arXiv PDFs to build your knowledge base</span>
        </div>
      </div>

      <div className="ingest-body">
        <div {...getRootProps()} className={`dropzone ${isDragActive ? 'drag-active' : ''}`}>
          <input {...getInputProps()} />
          <div className="dropzone-icon"><Upload /></div>
          <h3>Drop your PDF here</h3>
          <p>Supports arXiv research papers in PDF format</p>
          <button className="dropzone-btn" onClick={open}>
            <FilePlus size={14} />
            Browse Files
          </button>
        </div>

        {queue.length > 0 && (
          <div>
            <div className="section-label">Upload Queue</div>
            <div className="upload-list" style={{ marginTop: 12 }}>
              {queue.map(item => (
                <UploadItem key={item.id} item={item} />
              ))}
            </div>
          </div>
        )}

        <IngestInfo />
      </div>
    </div>
  )
}

function UploadItem({ item }) {
  const statusMap = {
    pending:   { label: 'Queued',     cls: 'uploading' },
    uploading: { label: 'Processing…', cls: 'uploading' },
    success:   { label: 'Ingested',   cls: 'success' },
    error:     { label: 'Failed',     cls: 'error' },
  }
  const { label, cls } = statusMap[item.status] ?? statusMap.pending

  return (
    <div className={`upload-item ${cls === 'success' ? 'success' : cls === 'error' ? 'error' : ''}`}>
      <div className="upload-item-icon"><FileText /></div>
      <div className="upload-item-info">
        <div className="upload-item-name">{item.file.name}</div>
        <div className="upload-item-sub">{formatBytes(item.file.size)}</div>
        {item.status === 'uploading' && (
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${item.progress}%` }} />
          </div>
        )}
        {item.error && (
          <div className="upload-item-sub" style={{ color: 'var(--error)', marginTop: 2 }}>
            {item.error}
          </div>
        )}
      </div>
      <div className={`upload-status ${cls}`}>
        {item.status === 'uploading' && <><div className="spinner" />{label}</>}
        {item.status === 'success'   && <><CheckCircle size={14} />{label}</>}
        {item.status === 'error'     && <><XCircle size={14} />{label}</>}
        {item.status === 'pending'   && <><Loader size={14} />{label}</>}
      </div>
    </div>
  )
}

function IngestInfo() {
  return (
    <div style={{
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
      padding: '16px 20px',
    }}>
      <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
        What happens during ingestion?
      </div>
      {[
        ['Parse', 'PDF sections are extracted and structured from the arXiv paper.'],
        ['Store', 'Sections are saved to SQLite and embedded into ChromaDB for semantic search.'],
        ['Wiki', 'The AI agent creates or updates knowledge wiki pages based on the content.'],
      ].map(([title, desc]) => (
        <div key={title} style={{ display: 'flex', gap: 10, marginBottom: 8, alignItems: 'flex-start' }}>
          <span style={{
            width: 20, height: 20, background: 'var(--accent-subtle)', borderRadius: 4,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 10, fontWeight: 700, color: 'var(--accent-text)', flexShrink: 0, marginTop: 1,
          }}>{title[0]}</span>
          <span style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            <strong style={{ color: 'var(--text-primary)' }}>{title}:</strong> {desc}
          </span>
        </div>
      ))}
    </div>
  )
}
