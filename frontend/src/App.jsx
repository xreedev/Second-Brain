import { useMemo, useRef, useState } from 'react'
import './App.css'

const initialDocs = [
  {
    id: '1',
    title: 'Research Notes',
    type: 'md',
    path: '/wiki/index.md',
    summary: 'Markdown notes from the knowledge base ready for preview.',
    preview: `# Research Notes\n\n- Review the wiki file collection\n- Extract insights from PDF sources\n- Keep your research organized and actionable\n\n## Actions\n\n1. Upload a PDF directly from chat\n2. Create a new document from the workspace\n3. Cite content when needed`,
    api: 'https://api.example.com/wiki/notes'
  },
  {
    id: '2',
    title: 'AI Paper Overview',
    type: 'pdf',
    path: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
    summary: 'A PDF source loaded from the current research collection for rendering.',
    preview: 'pdf',
    api: 'https://api.example.com/wiki/paper'
  },
  {
    id: '3',
    title: 'System Design Map',
    type: 'md',
    path: '/wiki/index.json',
    summary: 'Technical design metadata and source references.',
    preview: `## System Design Map\n\nThe wiki stores files in the root project folder under /wiki. This canvas panel renders markdown and PDF previews from the selected file source.\n\n- File path: /wiki/index.json\n- Status: preview enabled\n- Upload flow: chat tools available`,
    api: 'https://api.example.com/wiki/design'
  }
]

const initialMessages = [
  {
    id: 'm1',
    role: 'assistant',
    text: 'Welcome to Research Assist. Start a conversation, preview wiki content, and render PDF sources in the canvas panel.'
  },
  {
    id: 'm2',
    role: 'user',
    text: 'Show me the current wiki documents and the default PDF source.'
  },
  {
    id: 'm3',
    role: 'assistant',
    text: 'You can upload a PDF from chat or use the wiki tab to browse source files. Use the side canvas to render markdown and PDF content as you go.'
  }
]

const markdownToHtml = (markdown) => {
  const escaped = markdown
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  return escaped
    .split('\n')
    .map((line) => {
      if (/^###\s+/.test(line)) {
        return `<h3>${line.replace(/^###\s+/, '')}</h3>`
      }
      if (/^##\s+/.test(line)) {
        return `<h2>${line.replace(/^##\s+/, '')}</h2>`
      }
      if (/^#\s+/.test(line)) {
        return `<h1>${line.replace(/^#\s+/, '')}</h1>`
      }
      if (/^-\s+/.test(line)) {
        return `<li>${line.replace(/^-\s+/, '')}</li>`
      }
      if (/^>\s+/.test(line)) {
        return `<blockquote>${line.replace(/^>\s+/, '')}</blockquote>`
      }
      if (line.trim() === '') {
        return '<br/>'
      }
      return `<p>${line}</p>`
    })
    .join('')
}

function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [documents, setDocuments] = useState(initialDocs)
  const [selectedDoc, setSelectedDoc] = useState(initialDocs[1])
  const [messages, setMessages] = useState(initialMessages)
  const [draft, setDraft] = useState('')
  const [selectedFileName, setSelectedFileName] = useState('No file selected')
  const [feedback, setFeedback] = useState({})
  const [toolMenuOpen, setToolMenuOpen] = useState(false)
  const uploadRef = useRef(null)
  const chatUploadRef = useRef(null)

  const activeDocs = useMemo(() => documents, [documents])

  const handleSelectDoc = (doc) => {
    setSelectedDoc(doc)
    setActiveTab('chat')
  }

  const handleSend = () => {
    const trimmed = draft.trim()
    if (!trimmed) return

    const nextUser = {
      id: `u-${Date.now()}`,
      role: 'user',
      text: trimmed
    }
    const nextAssistant = {
      id: `a-${Date.now()}`,
      role: 'assistant',
      text: `I reviewed the selected source and here is the summary from ${selectedDoc.title}. The current path is ${selectedDoc.path}.`
    }

    setMessages((prev) => [...prev, nextUser, nextAssistant])
    setDraft('')
  }

  const handleDocumentUpload = (event) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFileName(file.name)
      const uploadedDoc = {
        id: `uploaded-${Date.now()}`,
        title: file.name,
        type: file.name.toLowerCase().endsWith('.pdf') ? 'pdf' : 'md',
        path: URL.createObjectURL(file),
        summary: 'Uploaded from chat for preview and testing.',
        preview: file.name.toLowerCase().endsWith('.pdf') ? 'pdf' : `# Uploaded document\n\nThis document was added from the chat upload flow.`,
        api: 'https://api.example.com/wiki/upload'
      }
      setDocuments((prev) => [uploadedDoc, ...prev])
      setSelectedDoc(uploadedDoc)
      setActiveTab('chat')
    }
  }

  const handleWikiUpload = (event) => {
    const file = event.target.files?.[0]
    if (file) {
      const uploadedDoc = {
        id: `wiki-upload-${Date.now()}`,
        title: file.name,
        type: file.name.toLowerCase().endsWith('.pdf') ? 'pdf' : 'md',
        path: URL.createObjectURL(file),
        summary: 'Uploaded from the wiki section for quick access.',
        preview: file.name.toLowerCase().endsWith('.pdf') ? 'pdf' : `# Wiki upload\n\nThis markdown was uploaded from the wiki section.`,
        api: 'https://api.example.com/wiki/upload'
      }
      setDocuments((prev) => [uploadedDoc, ...prev])
      setSelectedDoc(uploadedDoc)
      setActiveTab('chat')
    }
  }

  const handleCreateDoc = () => {
    const newDoc = {
      id: `new-${Date.now()}`,
      title: 'New Research Doc',
      type: 'md',
      path: '/wiki/new-doc.md',
      summary: 'A newly created document placeholder from the chat actions.',
      preview: `# New Research Document\n\nThis document was created through the chat toolbar action. Use it to capture new findings and add more details later.`,
      api: 'https://api.example.com/wiki/create'
    }
    setDocuments((prev) => [newDoc, ...prev])
    setSelectedDoc(newDoc)
    setActiveTab('chat')
  }

  const handleFeedback = (messageId, value) => {
    setFeedback((prev) => ({
      ...prev,
      [messageId]: prev[messageId] === value ? null : value
    }))
  }

  const renderPreview = () => {
    if (selectedDoc.type === 'pdf') {
      return (
        <div className="previewFrame">
          <iframe
            title="PDF preview"
            src={selectedDoc.path}
            sandbox="allow-same-origin allow-scripts"
          />
        </div>
      )
    }

    return (
      <div
        className="markdownPreview"
        dangerouslySetInnerHTML={{ __html: markdownToHtml(selectedDoc.preview) }}
      />
    )
  }

  return (
    <div className="appShell">
      <header className="appHeader">
        <div>
          <p className="eyebrow">Rseearch Assist</p>
          <h1>Research Assist</h1>
          <p className="heroSubtitle">
            A professional SaaS-style AI research workspace with wiki browsing,
            PDF rendering, chat actions, and citation tools.
          </p>
        </div>
        <div className="headerActions">
          <button className="button button-secondary">Live demo</button>
          <button className="button">Launch app</button>
        </div>
      </header>

      <main className="workspaceGrid">
        <aside className="sidebar">
          <div className="sectionHeader">
            <div>
              <span className="sectionLabel">Mode</span>
              <h2>Workspace</h2>
            </div>
          </div>

          <div className="tabList">
            <button
              className={activeTab === 'chat' ? 'tab active' : 'tab'}
              onClick={() => setActiveTab('chat')}
            >
              Chatbot
            </button>
            <button
              className={activeTab === 'wiki' ? 'tab active' : 'tab'}
              onClick={() => setActiveTab('wiki')}
            >
              Wiki
            </button>
          </div>

          {activeTab === 'wiki' ? (
            <div className="wikiPanel">
              <p className="panelIntro">
                Browse wiki files from the root research collection. Upload new
                PDF source files for preview.
              </p>

              <div className="docList">
                {activeDocs.map((doc) => (
                  <button
                    key={doc.id}
                    className={
                      doc.id === selectedDoc.id ? 'docCard selected' : 'docCard'
                    }
                    onClick={() => handleSelectDoc(doc)}
                  >
                    <div>
                      <strong>{doc.title}</strong>
                      <p>{doc.summary}</p>
                    </div>
                    <span className="docType">{doc.type.toUpperCase()}</span>
                  </button>
                ))}
              </div>

              <div className="uploadPanel">
                <label className="uploadButton">
                  Upload PDF to Wiki
                  <input
                    type="file"
                    accept="application/pdf"
                    hidden
                    ref={uploadRef}
                    onChange={handleWikiUpload}
                  />
                </label>
                <p className="uploadHint">Current upload target: wiki folder</p>
              </div>
            </div>
          ) : (
            <div className="chatInfoPanel">
              <p className="panelIntro">
                Use the chat workspace to ask questions, preview knowledge, and
                manage research documents.
              </p>
              <div className="metaCard">
                <span>Default PDF source:</span>
                <strong>{selectedDoc.path}</strong>
              </div>
              <div className="metaCard">
                <span>Preview mode:</span>
                <strong>{selectedDoc.type === 'pdf' ? 'PDF canvas' : 'Markdown canvas'}</strong>
              </div>
            </div>
          )}
        </aside>

        <section className="chatroom">
          <div className="chatHeader">
            <div>
              <span className="sectionLabel">Chat</span>
              <h2>Research conversation</h2>
            </div>
            <div className="badge">AI assistant</div>
          </div>

          <div className="messageBoard">
            {messages.map((message) => (
              <div
                key={message.id}
                className={
                  message.role === 'assistant'
                    ? 'message message-assistant'
                    : 'message message-user'
                }
              >
                <div className="messageHeader">
                  <span>{message.role === 'assistant' ? 'Assistant' : 'You'}</span>
                </div>
                <p>{message.text}</p>

                {message.role === 'assistant' && (
                  <div className="messageActions">
                    <button
                      className={feedback[message.id] === 'up' ? 'iconButton active' : 'iconButton'}
                      onClick={() => handleFeedback(message.id, 'up')}
                      aria-label="Give thumbs up"
                    >
                      👍
                    </button>
                    <button
                      className={feedback[message.id] === 'down' ? 'iconButton active' : 'iconButton'}
                      onClick={() => handleFeedback(message.id, 'down')}
                      aria-label="Give thumbs down"
                    >
                      👎
                    </button>
                    <button className="actionButton" onClick={() => {}}>
                      Cite this
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="chatFooter">
            <div className="toolbarRow">
              <button
                className="toolbarButton"
                onClick={() => setToolMenuOpen((open) => !open)}
                aria-label="More actions"
              >
                +
              </button>
              <button
                className="toolbarButton"
                onClick={() => chatUploadRef.current?.click()}
              >
                Upload PDF
              </button>
              <button className="toolbarButton" onClick={handleCreateDoc}>
                Create doc
              </button>
              <span className="fileLabel">{selectedFileName}</span>
            </div>

            {toolMenuOpen && (
              <div className="toolMenu">
                <button className="toolItem" onClick={() => chatUploadRef.current?.click()}>
                  Upload PDF from chat
                </button>
                <button className="toolItem" onClick={handleCreateDoc}>
                  Create research doc
                </button>
              </div>
            )}

            <div className="inputRow">
              <textarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Ask a research question or tell the assistant what to summarize..."
              />
              <button className="button button-primary" onClick={handleSend}>
                Send
              </button>
            </div>
            <input
              type="file"
              accept="application/pdf"
              hidden
              ref={chatUploadRef}
              onChange={handleDocumentUpload}
            />
          </div>
        </section>

        <aside className="canvasPanel">
          <div className="canvasHeader">
            <div>
              <span className="sectionLabel">Canvas</span>
              <h2>{selectedDoc.title}</h2>
            </div>
            <span className="badge">Preview</span>
          </div>

          <div className="canvasMeta">
            <p>{selectedDoc.summary}</p>
            <div>
              <span>Path</span>
              <strong>{selectedDoc.path}</strong>
            </div>
            <div>
              <span>API source</span>
              <strong>{selectedDoc.api}</strong>
            </div>
          </div>

          <div className="canvasContent">{renderPreview()}</div>
        </aside>
      </main>
    </div>
  )
}

export default App
