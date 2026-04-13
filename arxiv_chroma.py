from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Literal, Optional

import chromadb
from chromadb.config import Settings

# Import our parser internals
from arxiv_parser import (
    _load_pdf,
    _extract_lines,
    _build_sections,
    _clean_section_text,
    _extract_meta_from_preamble,
)

# ─── Types ────────────────────────────────────────────────────────────────────

Backend = Literal["openai", "sentence_transformers", "chroma_default", "tfidf", "auto"]

DEFAULT_PERSIST_DIR = "./chroma_db"
DEFAULT_COLLECTION  = "arxiv_papers"


# ─── Embedding backends ───────────────────────────────────────────────────────

class _OpenAIBackend:
    name = "openai"

    def __init__(self, model: str = "text-embedding-3-small", api_key: str | None = None):
        from openai import OpenAI  # noqa: PLC0415
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model  = model
        self.dim    = 1536

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self.client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in resp.data]

    def chroma_ef(self):
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction  # noqa
        return OpenAIEmbeddingFunction(
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            model_name=self.model,
        )


class _SentenceTransformerBackend:
    name = "sentence_transformers"

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        self.model = SentenceTransformer(model)
        self.dim   = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def chroma_ef(self):
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction  # noqa
        return SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")


class _ChromaDefaultBackend:
    """Uses ChromaDB's built-in ONNX MiniLM (downloads ~25 MB on first use)."""
    name = "chroma_default"
    dim  = 384

    def chroma_ef(self):
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction  # noqa
        return DefaultEmbeddingFunction()

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.chroma_ef()(texts)


class _TFIDFBackend:
    """
    TF-IDF + SVD (LSA) embeddings — 512-dim, zero extra dependencies.
    Quality is lower than neural embeddings but always works offline.
    The vectoriser is fit on the paper's own sections for best recall.
    """
    name = "tfidf"
    dim  = 512

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        from sklearn.pipeline import Pipeline
        self._pipeline: Pipeline | None = None
        self._TfidfVectorizer = TfidfVectorizer
        self._TruncatedSVD    = TruncatedSVD
        self._Pipeline        = Pipeline

    def fit(self, texts: list[str]):
        n_components = min(self.dim, len(texts) - 1, 20000)
        self._pipeline = self._Pipeline([
            ("tfidf", self._TfidfVectorizer(
                sublinear_tf=True,
                ngram_range=(1, 2),
                max_features=20_000,
                stop_words="english",
            )),
            ("svd", self._TruncatedSVD(n_components=n_components, random_state=42)),
        ])
        self._pipeline.fit(texts)
        self.dim = n_components

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._pipeline is None:
            self.fit(texts)
        return self._pipeline.transform(texts).tolist()

    def chroma_ef(self):
        """Return a ChromaDB-compatible callable wrapping this backend."""
        backend = self

        class _TFIDFChromaEF:
            def __call__(self, input: list[str]) -> list[list[float]]:  # noqa: A002
                return backend.embed(input)

            def embed_query(self, input: list[str]) -> list[list[float]]:  # noqa: A002
                return backend.embed(input)

        return _TFIDFChromaEF()


def _resolve_backend(backend: Backend) -> object:
    """Instantiate the best available backend."""
    if backend == "openai":
        return _OpenAIBackend()
    if backend == "sentence_transformers":
        return _SentenceTransformerBackend()
    if backend == "chroma_default":
        return _ChromaDefaultBackend()
    if backend == "tfidf":
        return _TFIDFBackend()

    # "auto" — try in priority order
    if backend == "auto":
        # 1. sentence_transformers
        try:
            import sentence_transformers  # noqa: F401
            print("[arxiv_chroma] Backend: sentence_transformers", file=sys.stderr)
            return _SentenceTransformerBackend()
        except ImportError:
            pass
        # 2. openai (only if key is set)
        if os.environ.get("OPENAI_API_KEY"):
            try:
                import openai  # noqa: F401
                print("[arxiv_chroma] Backend: openai", file=sys.stderr)
                return _OpenAIBackend()
            except ImportError:
                pass
        # 3. tfidf fallback
        print(
            "[arxiv_chroma] Backend: tfidf (install sentence-transformers for better quality)",
            file=sys.stderr,
        )
        return _TFIDFBackend()

    raise ValueError(f"Unknown backend: {backend!r}")


# ─── ChromaDB client helper ───────────────────────────────────────────────────

_CLIENTS: dict[str, chromadb.Client] = {}


def _get_client(persist_dir: str) -> chromadb.ClientAPI:
    if persist_dir not in _CLIENTS:
        _CLIENTS[persist_dir] = chromadb.PersistentClient(path=persist_dir)
    return _CLIENTS[persist_dir]


# ─── Document ID helper ───────────────────────────────────────────────────────

def _doc_id(arxiv_id_or_path: str, section_heading: str, idx: int) -> str:
    base = re.sub(r"[^a-z0-9]", "_", arxiv_id_or_path.lower())[:40]
    heading_slug = re.sub(r"[^a-z0-9]", "_", section_heading.lower())[:30]
    return f"{base}__{heading_slug}__{idx:03d}"


# ─── Main ingest function ─────────────────────────────────────────────────────

def embed_paper(
    source: str | Path | bytes,
    *,
    backend: Backend = "auto",
    collection_name: str | None = None,
    persist_dir: str = DEFAULT_PERSIST_DIR,
    skip_preamble: bool = True,
    skip_references: bool = False,
    min_section_chars: int = 80,
    title: str | None = None,
    authors: str | None = None,
) -> chromadb.Collection:
    """
    Parse a paper into sections, embed each one, and upsert into ChromaDB.

    Parameters
    ----------
    source : str | Path | bytes
        arXiv ID (e.g. "2401.12345"), local PDF path, or raw PDF bytes.
    backend : {"auto", "openai", "sentence_transformers", "chroma_default", "tfidf"}
        Embedding backend. "auto" picks the best available one.
    collection_name : str, optional
        ChromaDB collection name. Defaults to "arxiv_<id>" or "arxiv_<hash>".
    persist_dir : str
        Directory where ChromaDB stores its data. Defaults to "./chroma_db".
    skip_preamble : bool
        Skip the title/author preamble section (default True).
    skip_references : bool
        Skip the References section (default False — references are useful for citation search).
    min_section_chars : int
        Sections with fewer characters than this are skipped (e.g. empty stubs).
    title : str, optional
        Override auto-detected title.
    authors : str, optional
        Override auto-detected authors.

    Returns
    -------
    chromadb.Collection
        The populated ChromaDB collection.
    """
    # ── 1. Load PDF ──────────────────────────────────────────────────────────
    pdf_bytes, base_meta = _load_pdf(source)
    lines    = _extract_lines(pdf_bytes)
    if not lines:
        raise ValueError("No text could be extracted from the PDF.")

    # ── 2. Section extraction ────────────────────────────────────────────────
    sections = _build_sections(lines)
    meta     = _extract_meta_from_preamble(sections, base_meta)
    if title:   meta["title"]   = title
    if authors: meta["authors"] = authors
    meta.setdefault("title", "Unknown Title")

    paper_id = meta.get("arxiv_id") or hashlib.md5(pdf_bytes[:4096]).hexdigest()[:12]
    if collection_name is None:
        collection_name = f"arxiv_{re.sub(r'[^a-z0-9_-]', '_', paper_id.lower())}"

    # ── 3. Filter sections ───────────────────────────────────────────────────
    def _keep(sec: dict) -> bool:
        if skip_preamble and sec["heading"] == "Preamble":
            return False
        if skip_references and re.match(r"^references?$", sec["heading"], re.I):
            return False
        content = _clean_section_text(sec["lines"])
        return len(content) >= min_section_chars

    filtered = [s for s in sections if _keep(s)]
    if not filtered:
        raise ValueError("No sections with enough content found after filtering.")

    # ── 4. Prepare documents ─────────────────────────────────────────────────
    contents = [_clean_section_text(s["lines"]) for s in filtered]
    ids      = [_doc_id(paper_id, s["heading"], i) for i, s in enumerate(filtered)]
    metadatas = [
        {
            "heading":      s["heading"],
            "page":         s["page"],
            "paper_title":  meta.get("title", ""),
            "paper_authors":meta.get("authors", ""),
            "arxiv_id":     meta.get("arxiv_id", paper_id),
            "source":       meta.get("source", ""),
            "char_count":   len(contents[i]),
        }
        for i, s in enumerate(filtered)
    ]

    # ── 5. Resolve embedding backend & create collection ────────────────────
    backend_obj = _resolve_backend(backend)

    # TF-IDF needs to be fit before creating the ChromaDB EF
    if isinstance(backend_obj, _TFIDFBackend):
        backend_obj.fit(contents)

    chroma_ef  = backend_obj.chroma_ef()
    client     = _get_client(persist_dir)

    # Delete existing collection if re-ingesting the same paper
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name               = collection_name,
        embedding_function = chroma_ef,
        metadata           = {
            "hnsw:space":   "cosine",
            "paper_title":  meta.get("title", ""),
            "arxiv_id":     meta.get("arxiv_id", paper_id),
            "backend":      backend_obj.name,
            "total_sections": len(filtered),
        },
    )

    # ── 6. Upsert in batches of 64 ───────────────────────────────────────────
    batch = 64
    for start in range(0, len(contents), batch):
        end = start + batch
        collection.upsert(
            ids        = ids[start:end],
            documents  = contents[start:end],
            metadatas  = metadatas[start:end],
        )

    total = collection.count()
    print(
        f"[arxiv_chroma] ✓ '{collection_name}'  {total} sections embedded "
        f"({backend_obj.name})  →  {persist_dir}",
        file=sys.stderr,
    )
    return collection


# ─── Query function ───────────────────────────────────────────────────────────

def query_paper(
    query: str,
    *,
    collection: chromadb.Collection | None = None,
    collection_name: str | None = None,
    persist_dir: str = DEFAULT_PERSIST_DIR,
    n_results: int = 3,
    where: dict | None = None,
) -> list[dict]:
    """
    Semantic search over an embedded paper.

    Parameters
    ----------
    query : str
        Natural language question or search string.
    collection : chromadb.Collection, optional
        Directly pass the collection returned by embed_paper().
    collection_name : str, optional
        Name of a persisted collection to load (if `collection` is not given).
    persist_dir : str
        ChromaDB storage directory.
    n_results : int
        Number of top sections to return (default 3).
    where : dict, optional
        ChromaDB metadata filter, e.g. {"heading": "Results"}.

    Returns
    -------
    list[dict]
        Each dict has: heading, page, content, distance, paper_title, arxiv_id.

    Examples
    --------
    >>> results = query_paper("what statistical methods were used?", collection=col)
    >>> for r in results:
    ...     print(r["heading"], "—", r["content"][:200])
    """
    if collection is None:
        if collection_name is None:
            raise ValueError("Provide either `collection` or `collection_name`.")
        client     = _get_client(persist_dir)
        collection = client.get_collection(collection_name)

    kwargs: dict = {"query_texts": [query], "n_results": min(n_results, collection.count())}
    if where:
        kwargs["where"] = where

    raw = collection.query(**kwargs)

    results = []
    for i, doc in enumerate(raw["documents"][0]):
        m = raw["metadatas"][0][i]
        results.append(
            {
                "rank":        i + 1,
                "heading":     m.get("heading", ""),
                "page":        m.get("page", ""),
                "content":     doc,
                "distance":    round(raw["distances"][0][i], 4),
                "paper_title": m.get("paper_title", ""),
                "arxiv_id":    m.get("arxiv_id", ""),
                "char_count":  m.get("char_count", len(doc)),
            }
        )
    return results


# ─── Convenience accessor ─────────────────────────────────────────────────────

def get_collection(
    collection_name: str,
    persist_dir: str = DEFAULT_PERSIST_DIR,
) -> chromadb.Collection:
    """Load an already-embedded collection by name."""
    return _get_client(persist_dir).get_collection(collection_name)


def list_collections(persist_dir: str = DEFAULT_PERSIST_DIR) -> list[str]:
    """Return names of all collections in the store."""
    return [c.name for c in _get_client(persist_dir).list_collections()]


# ─── Pretty-print helper ──────────────────────────────────────────────────────

def print_results(results: list[dict], max_chars: int = 300) -> None:
    """Print query results in a readable format."""
    for r in results:
        snippet = r["content"][:max_chars].replace("\n", " ")
        if len(r["content"]) > max_chars:
            snippet += " …"
        print(f"\n{'─'*60}")
        print(f"  #{r['rank']}  [{r['heading']}]  p.{r['page']}  (dist={r['distance']})")
        print(f"  {snippet}")
    print(f"\n{'─'*60}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, json

    ap = argparse.ArgumentParser(description="Embed arXiv paper sections into ChromaDB.")
    ap.add_argument("source", help="arXiv ID or path to PDF")
    ap.add_argument("--backend", default="auto",
                    choices=["auto", "openai", "sentence_transformers", "chroma_default", "tfidf"],
                    help="Embedding backend (default: auto)")
    ap.add_argument("--persist", default=DEFAULT_PERSIST_DIR, metavar="DIR",
                    help="ChromaDB storage directory")
    ap.add_argument("--collection", default=None, metavar="NAME",
                    help="Override collection name")
    ap.add_argument("--query", "-q", default=None,
                    help="Query to run after embedding")
    ap.add_argument("--n", type=int, default=3,
                    help="Number of results to return for a query")
    ap.add_argument("--json", action="store_true",
                    help="Output query results as JSON")
    ap.add_argument("--list", action="store_true",
                    help="List all collections in the store and exit")
    args = ap.parse_args()

    if args.list:
        cols = list_collections(args.persist)
        print("\n".join(cols) if cols else "(no collections found)")
        sys.exit(0)

    col = embed_paper(
        args.source,
        backend         = args.backend,
        collection_name = args.collection,
        persist_dir     = args.persist,
    )

    if args.query:
        results = query_paper(args.query, collection=col, n_results=args.n)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"\nQuery: {args.query!r}")
            print_results(results)