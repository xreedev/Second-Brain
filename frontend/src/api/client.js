const BASE = import.meta.env.VITE_API_URL || ''

export async function ingestPdf(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/ingest`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function sendChat(query) {
  const res = await fetch(`${BASE}/chat?query=${encodeURIComponent(query)}`, { method: 'POST' })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function fetchWikiFiles() {
  const res = await fetch('/wiki-files/')
  if (!res.ok) throw new Error('Failed to list wiki files')
  return res.json() // string[]
}

export async function fetchWikiContent(path) {
  const res = await fetch(`/wiki-files/${encodeURIComponent(path)}`)
  if (!res.ok) throw new Error('Failed to fetch wiki file')
  return res.text()
}

export async function fetchSourceFiles() {
  const res = await fetch('/source-files/')
  if (!res.ok) throw new Error('Failed to list source files')
  return res.json() // string[]
}
