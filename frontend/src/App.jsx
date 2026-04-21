import { useState, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import ChatView from './components/ChatView'
import IngestView from './components/IngestView'
import WikiView from './components/WikiView'
import SourcePanel from './components/SourcePanel'

export default function App() {
  const [activeView, setActiveView]       = useState('chat')
  const [messages, setMessages]           = useState([])
  const [isLoading, setIsLoading]         = useState(false)
  const [sourcePanel, setSourcePanel]     = useState(null) // { name, documents }
  const [ingestedFiles, setIngestedFiles] = useState([])

  const handleIngestComplete = useCallback((filename) => {
    setIngestedFiles(prev => [...new Set([...prev, filename])])
  }, [])

  const handleSourceClick = useCallback((name, documents) => {
    setSourcePanel(prev => prev?.name === name ? null : { name, documents })
  }, [])

  const closeSourcePanel = useCallback(() => setSourcePanel(null), [])

  return (
    <div className="app-shell">
      <Sidebar
        activeView={activeView}
        setActiveView={setActiveView}
        messages={messages}
        ingestedFiles={ingestedFiles}
        onSourceClick={handleSourceClick}
      />

      <div className="main-area">
        <div className="view-content">
          {activeView === 'chat' && (
            <ChatView
              messages={messages}
              setMessages={setMessages}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
              onSourceClick={handleSourceClick}
              activeSource={sourcePanel?.name}
            />
          )}
          {activeView === 'wiki' && <WikiView />}
          {activeView === 'ingest' && (
            <IngestView onIngestComplete={handleIngestComplete} />
          )}
        </div>

        {sourcePanel && (
          <SourcePanel source={sourcePanel} onClose={closeSourcePanel} />
        )}
      </div>
    </div>
  )
}
