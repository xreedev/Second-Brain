<div align="center">
<br/>

# episteme

### *An LLM-maintained knowledge wiki for arXiv papers — every answer traced to its exact source passage.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6B35?style=for-the-badge)](https://www.trychroma.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Section_Index-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Pattern](https://img.shields.io/badge/Based_on-Karpathy_LLM_Wiki-f59e0b?style=for-the-badge)](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

[**How It Works**](#how-it-works) · [**Wiki Structure**](#wiki-structure) · [**API**](#api-reference) · [**Setup**](#getting-started)

<br/>
</div>

---

## What is this?

Andrej Karpathy's [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) proposes something fundamentally different from RAG: instead of searching raw documents at query time, have the LLM compile your sources into a **living, structured markdown wiki** that accumulates knowledge over time.

**episteme** implements this for academic research — specifically arXiv PDFs — and adds one critical layer:

> After the LLM answers from the wiki, it embeds the response and performs a vector search against the original source sections, returning the **exact passage from the original paper** that semantically produced each part of the answer.

This lets researchers verify AI claims against primary sources. Students can see exactly which section of which paper an explanation came from.

---

## How It Works

### `POST /ingest` — Ingest Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│  arXiv PDF                                                       │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  Section Splitter                                                │
│  Splits PDF into logical sections (abstract, intro, methods…)   │
│  Each section: { section_id, title, text, source_filename }     │
└────────┬────────────────────────┬────────────────────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────────┐
│  SQLite         │    │  ChromaDB            │
│  ─────────────  │    │  ──────────────────  │
│  section_id     │    │  section embedding   │
│  section_text   │    │  metadata:           │
│  section_title  │    │    section_id        │
│  source_file    │    │    source_filename   │
└─────────────────┘    └──────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  LLM Wiki Writer                                                 │
│  Reads each section. For every section:                         │
│    1. Check wiki/index.md — does a relevant wiki page exist?    │
│    2. If yes: retrieve that page, update the relevant section   │
│    3. If no: create a new wiki page with a new section          │
│    4. Update wiki/index.md  → section_id : section_description  │
│    5. Update wiki/index.json → section_id : source_id           │
└──────────────────────────────────────────────────────────────────┘
```

The wiki only ever reads and writes at the **section level** — never whole pages at once. This keeps source tracking granular and accurate.

---

### `POST /chat` — Chat Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│  User query                                                      │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  Wiki Section Retrieval                                          │
│  Search wiki/index.md for relevant section IDs + descriptions   │
│  Fetch the matching wiki page sections as context               │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  LLM Answer Generation                                           │
│  Generates answer using wiki section context                    │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  Source Tracing (the key extension)                              │
│  1. Look up wiki/index.json → get source_ids for those sections  │
│  2. Embed the LLM's response                                    │
│  3. Vector search in ChromaDB: response vs sections from those   │
│     source papers only                                          │
│  4. Return ranked passages: exact text from original PDFs        │
│     with similarity scores                                      │
└──────────────────────────────────────────────────────────────────┘
                   │
                   ▼
     answer + [{ paper, section, passage, similarity }]
```

---

## Wiki Structure

The wiki is a directory of markdown files. Every read and write happens at the section level.

```
wiki/
├── index.md          ← section_id → section description (human-readable)
├── index.json        ← section_id → source_id (machine-readable, for tracing)
├── transformers.md
├── attention_mechanism.md
├── positional_encoding.md
└── ...
```

**`wiki/index.md`** — The LLM's map of what exists in the wiki:
```markdown
# Wiki Index

## sec_001
Transformer architecture overview. Covers encoder-decoder structure and self-attention.
Source: attention_is_all_you_need.pdf

## sec_002
Multi-head attention mechanism. Parallel projection heads and output concatenation.
Source: attention_is_all_you_need.pdf

## sec_003
BERT masked language modeling pre-training objective.
Source: bert_pretraining.pdf
```

**`wiki/index.json`** — Machine-readable section-to-source mapping used by the chat pipeline tracer:
```json
{
  "sec_001": "attention_is_all_you_need.pdf",
  "sec_002": "attention_is_all_you_need.pdf",
  "sec_003": "bert_pretraining.pdf"
}
```

When the chat pipeline retrieves wiki sections to answer a query, it looks up the source IDs from `index.json` and scopes the ChromaDB vector search to only those source papers — ensuring retrieved passages genuinely relate to what the LLM drew on.

---

## Architecture

```
episteme/
├── backend/
│   ├── app.py                    # API entry point (POST /ingest, POST /chat)
│   │
│   ├── ingest/
│   │   ├── pdf_splitter.py       # Section-aware PDF extraction
│   │   ├── section_store.py      # SQLite: section text + metadata
│   │   ├── vector_store.py       # ChromaDB: section embeddings
│   │   └── wiki_writer.py        # LLM wiki updater (section-level r/w)
│   │
│   ├── chat/
│   │   ├── retriever.py          # wiki/index.md section lookup
│   │   ├── responder.py          # LLM answer from wiki context
│   │   └── tracer.py             # index.json → ChromaDB source trace
│   │
│   ├── wiki/
│   │   ├── index.md              # Section ID → description
│   │   ├── index.json            # Section ID → source file
│   │   └── *.md                  # Wiki pages
│   │
│   └── requirements.txt
│
└── frontend/
    ├── index.html
    ├── src/app.js
    └── styles/main.css
```

---

## API Reference

### `POST /ingest`

**Request**
```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@attention_is_all_you_need.pdf"
```

**Response**
```json
{
  "status": "ok",
  "paper": "attention_is_all_you_need.pdf",
  "sections_indexed": 12,
  "wiki_pages_updated": ["transformers.md", "attention_mechanism.md"],
  "new_sections": ["sec_041", "sec_042", "sec_043"]
}
```

---

### `POST /chat`

**Request**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How does multi-head attention work?"}'
```

**Response**
```json
{
  "answer": "Multi-head attention runs the attention function in parallel across h learned projections...",
  "wiki_sections_used": ["sec_002", "sec_007"],
  "sources": [
    {
      "paper": "attention_is_all_you_need.pdf",
      "section": "3.2 Multi-Head Attention",
      "passage": "Instead of performing a single attention function with d_model-dimensional keys...",
      "similarity": 0.94
    }
  ]
}
```

---

## Getting Started

```bash
git clone https://github.com/xreedev/episteme.git
cd episteme/backend

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure .env
LLM_API_KEY=your_key
LLM_MODEL=gpt-4o          # or claude-3-5-sonnet, etc.
CHROMA_PATH=./chroma_db
SQLITE_PATH=./sections.db
WIKI_PATH=./wiki

python app.py              # → http://localhost:8000
```

```bash
# Ingest a paper
curl -X POST localhost:8000/ingest -F "file=@paper.pdf"

# Chat with your wiki
curl -X POST localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What problem does this paper solve?"}'
```

---

## Why Not Just RAG?

| | Classic RAG | episteme (LLM Wiki) |
|---|---|---|
| Knowledge accumulation | None — every query starts fresh | Wiki grows with every paper ingested |
| Cross-paper synthesis | Chunks retrieved in isolation | LLM links concepts across papers at write time |
| Source attribution | Rough chunk-level | Exact passage via post-answer vector trace |
| Maintenance | Passive | LLM updates wiki when new papers arrive |
| Human readability | Raw chunks | Structured markdown wiki you can browse |

---

## Suggested GitHub Metadata

**Repo name:** `episteme`

**Description:** `LLM wiki for arXiv papers — ingests PDFs into a self-maintaining markdown knowledge base and traces every answer back to the exact source passage.`

**Topics:** `karpathy-llm-wiki` · `llm-wiki` · `second-brain` · `arxiv` · `source-attribution` · `verifiable-ai` · `chromadb` · `sqlite` · `knowledge-base` · `research-assistant` · `pdf-ingestion` · `markdown-wiki` · `python` · `rag`

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

Built by **[xreedev](https://github.com/xreedev)** · Inspired by [Andrej Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

</div>
