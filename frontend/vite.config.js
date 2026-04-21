import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync, readdirSync, statSync, existsSync } from 'fs'
import { join, relative } from 'path'

const BACKEND_DIR = join(process.cwd(), '..', 'backend')

function getAllFiles(dir, baseDir = dir) {
  if (!existsSync(dir)) return []
  const result = []
  try {
    for (const item of readdirSync(dir)) {
      const full = join(dir, item)
      try {
        if (statSync(full).isDirectory()) result.push(...getAllFiles(full, baseDir))
        else result.push(relative(baseDir, full).replace(/\\/g, '/'))
      } catch {}
    }
  } catch {}
  return result
}

function backendFilesPlugin() {
  return {
    name: 'backend-files',
    configureServer(server) {
      const WIKI_DIR = join(BACKEND_DIR, 'wiki')
      const SOURCE_DIR = join(BACKEND_DIR, 'source')

      server.middlewares.use('/wiki-files', (req, res) => {
        const urlPath = decodeURIComponent(req.url.replace(/^\//, '').split('?')[0])
        if (!urlPath) {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify(getAllFiles(WIKI_DIR)))
          return
        }
        const filePath = join(WIKI_DIR, urlPath)
        if (!filePath.startsWith(WIKI_DIR)) { res.statusCode = 403; res.end(); return }
        if (existsSync(filePath)) {
          res.setHeader('Content-Type', 'text/plain; charset=utf-8')
          res.end(readFileSync(filePath, 'utf-8'))
        } else { res.statusCode = 404; res.end('Not found') }
      })

      server.middlewares.use('/source-files', (req, res) => {
        const urlPath = decodeURIComponent(req.url.replace(/^\//, '').split('?')[0])
        if (!urlPath) {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify(getAllFiles(SOURCE_DIR)))
          return
        }
        const filePath = join(SOURCE_DIR, urlPath)
        if (!filePath.startsWith(SOURCE_DIR)) { res.statusCode = 403; res.end(); return }
        if (existsSync(filePath)) {
          res.setHeader('Content-Type', 'application/pdf')
          res.end(readFileSync(filePath))
        } else { res.statusCode = 404; res.end('Not found') }
      })
    }
  }
}

export default defineConfig({
  plugins: [react(), backendFilesPlugin()],
  server: {
    proxy: {
      '/ingest': { target: 'http://localhost:8000', changeOrigin: true },
      '/chat': { target: 'http://localhost:8000', changeOrigin: true },
    }
  }
})
