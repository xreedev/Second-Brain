import os
from typing import Optional, Literal

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from core.config import Config
from files_service import IndexMapService, WikiTrackingService
from .wiki_update import WikiUpdate


class FileOperation(BaseModel):
    mode: Literal["write", "update"]
    sections: list[dict] = Field(
        description=(
            "write  → each section needs: name, content, description. "
            "update → each section needs: id, name, content, description."
        )
    )


class WikiBatchInput(BaseModel):
    files: dict[str, FileOperation] = Field(
        description=(
            "Keys are relative file paths (e.g. 'concepts/ml.md'). "
            "Values are {mode, sections}. "
            "index.md is always rejected — the system manages it."
        )
    )


class WikiBatch(BaseTool):
    name: str = "wiki_batch"
    description: str = """Write or update multiple wiki files in a single call.

    Pass a 'files' dict where each key is a file path and the value is:
      mode     – 'write'  → create the file or append brand-new sections
               – 'update' → replace specific sections by their existing ID
      sections – list of section objects matching the mode requirements

    write sections need:  name, content, description
    update sections need: id, name, content, description

    Rules
    -----
    - Never include index.md as a key — it is system-managed and will be rejected.
    - One wiki_batch call replaces what previously required one call per file.
    - If a file needs both new sections AND updates to existing ones, include it
      twice: once with mode='write' for new sections, once with mode='update'
      for existing section replacements.
    - Never re-send sections that already exist in a file under mode='write'.
      Read the file first, get the section ID, then use mode='update'.
    """

    args_schema: type[BaseModel] = WikiBatchInput

    _source_id: Optional[str] = PrivateAttr(default=None)

    def __init__(self, source_id: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self._source_id = source_id

    def _run(self, files: dict) -> str:
        results = []

        for file_name, op in files.items():
            # Hard guard — never allow direct index writes
            if os.path.basename(file_name).lower() == "index.md":
                results.append(f"⚠  '{file_name}': REJECTED — index.md is system-managed.")
                continue

            if isinstance(op, BaseModel):
                op = op.model_dump()

            mode = op.get("mode")
            sections = op.get("sections", [])

            if mode not in ("write", "update"):
                results.append(
                    f"✗  '{file_name}': unknown mode '{mode}' — use 'write' or 'update'."
                )
                continue

            worker = WikiUpdate(source_id=self._source_id)
            msg = worker._run(file_name, mode=mode, sections=sections)
            status = "✗" if msg.startswith("Error") or msg.startswith("Aborted") else "✓"
            results.append(f"{status}  '{file_name}' [{mode}]: {msg}")

        return "\n".join(results)