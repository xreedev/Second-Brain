import { useState, useEffect, useCallback } from 'react'
import { BookOpen, FileText, RefreshCw, Folder, ChevronRight } from 'lucide-react'
import MarkdownRenderer from './MarkdownRenderer'
import { fetchWikiFiles, fetchWikiContent } from '../api/client'

function groupByFolder(files) {
  const folders = {}
  for (const f of files) {
    const parts = f.split('/')
    const folder = parts.length > 1 ? parts[0] : '__root__'
    const name   = parts[parts.length - 1]
    if (!folders[folder]) folders[folder] = []
    folders[folder].push({ path: f, name })
  }
  return folders
}

export default function WikiView() {
  const [files, setFiles]       = useState([])
  const [selected, setSelected] = useState(null)
  const [content, setContent]   = useState('')
  const [loading, setLoading]   = useState(false)
  const [fileLoading, setFileLoading] = useState(false)
  const [error, setError]       = useState(null)

  const loadFiles = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const list = await fetchWikiFiles()
      const mdFiles = list.filter(f => f.endsWith('.md'))
      setFiles(mdFiles)
    } catch (e) {
      setError('Could not connect to wiki. Make sure the backend server is running.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadFiles() }, [loadFiles])

  async function selectFile(path) {
    setSelected(path)
    setFileLoading(true)
    setContent('')
    try {
      const text = await fetchWikiContent(path)
      setContent(text)
    } catch {
      setContent('*Failed to load file content.*')
    } finally {
      setFileLoading(false)
    }
  }

  const grouped = groupByFolder(files)
  const filename = selected ? selected.split('/').pop() : ''
  const folder   = selected && selected.includes('/') ? selected.split('/')[0] : null

  return (
    <div className="wiki-view">
      <div className="wiki-tree">
        <div className="wiki-tree-header">
          <span className="wiki-tree-title">Knowledge Base</span>
          <button className="refresh-btn" onClick={loadFiles} title="Refresh">
            <RefreshCw size={11} style={loading ? { animation: 'spin 0.7s linear infinite' } : {}} />
          </button>
        </div>

        <div className="wiki-tree-body">
          {error && (
            <div style={{ padding: '12px 10px', color: 'var(--error)', fontSize: 12, lineHeight: 1.6 }}>
              {error}
            </div>
          )}

          {!error && files.length === 0 && !loading && (
            <div style={{ padding: '14px 10px', color: 'var(--text-muted)', fontSize: 12, lineHeight: 1.7, textAlign: 'center' }}>
              No wiki files yet. Ingest a PDF to generate knowledge articles.
            </div>
          )}

          {Object.entries(grouped).map(([folder, items]) => (
            <div key={folder} className="wiki-folder-group">
              {folder !== '__root__' && (
                <div className="wiki-folder-label">
                  <Folder />
                  {folder}
                </div>
              )}
              {items.map(({ path, name }) => (
                <button
                  key={path}
                  className={`wiki-file-btn ${selected === path ? 'active' : ''}`}
                  onClick={() => selectFile(path)}
                >
                  <FileText />
                  {name.replace('.md', '')}
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>

      <div className="wiki-content">
        {selected ? (
          <>
            <div className="wiki-content-header">
              <div>
                <div className="wiki-breadcrumb">
                  <BookOpen />
                  {folder && <><span>{folder}</span><ChevronRight size={10} /></>}
                  <span className="wiki-breadcrumb-name">{filename.replace('.md', '')}</span>
                </div>
              </div>
              <span className="badge badge-accent">.md</span>
            </div>
            <div className="wiki-content-body">
              {fileLoading
                ? <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)', fontSize: 13 }}>
                    <div className="spinner" /> Loading…
                  </div>
                : <MarkdownRenderer content={content} />
              }
            </div>
          </>
        ) : (
          <div className="wiki-empty">
            <BookOpen size={36} />
            <h3>Wiki Browser</h3>
            <p>
              Select a file from the left panel to view your AI-generated knowledge articles.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
