import os
import re
from typing import List, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from core.config import Config


class WikiReadInput(BaseModel):
    files: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of file paths to read in full (e.g. ['concepts/attention.md']). "
            "Use when you need the complete content of a file."
        ),
    )
    section_ids: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of section IDs to read selectively across all wiki files "
            "(e.g. ['42', '17', '88']). "
            "Use when the index shows a relevant section and you only need that "
            "section's content, not the entire file. More token-efficient than "
            "reading whole files."
        ),
    )


class WikiRead(BaseTool):
    name: str = "wiki_read"
    description: str = """Read wiki content in two ways — choose the most token-efficient option.

    Option A — full file read (files=[...]):
        Returns the complete content of one or more files.
        Use when you need to understand the full structure of a page
        before deciding how to update it.

    Option B — targeted section read (section_ids=[...]):
        Returns only the specific sections matching those IDs, with
        their file path and section heading included for context.
        Use when the index shows a section that may overlap with or
        conflict with incoming content — read just that section rather
        than the whole file.

    Both can be used in the same call if needed.
    """

    args_schema: type[BaseModel] = WikiReadInput

    def _run(
        self,
        files: Optional[List[str]] = None,
        section_ids: Optional[List[str]] = None,
    ) -> dict:
        results = {}

        if files:
            results["files"] = self._read_files(files)

        if section_ids:
            results["sections"] = self._read_sections(section_ids)

        if not files and not section_ids:
            return {"error": "Provide at least one of: files, section_ids"}

        return results

    # ── full file read ────────────────────────────────────────────────────────

    def _read_files(self, files: List[str]) -> dict:
        out = {}
        for file_name in files:
            file_path = os.path.join(Config.WIKI_BASE_DIR, file_name)
            if not os.path.exists(file_path):
                out[file_name] = f"File does not exist: {file_path}"
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    out[file_name] = f.read()
            except Exception as e:
                out[file_name] = f"Error reading file: {e}"
        return out

    # ── targeted section read ─────────────────────────────────────────────────

    def _read_sections(self, section_ids: List[str]) -> dict:
        """
        Scan all wiki files for the requested section IDs.
        Returns a dict keyed by section_id:
          {
            "42": {
              "file":    "concepts/attention.md",
              "heading": "Core Principles",
              "content": "## Core Principles\n..."
            },
            ...
          }
        """
        target_ids = set(str(sid) for sid in section_ids)
        found: dict = {}

        anchor_pattern = re.compile(r"<!-- section-id: ([^ ]+?) -->")
        heading_pattern = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)

        if not os.path.exists(Config.WIKI_BASE_DIR):
            return {sid: "Wiki directory does not exist." for sid in target_ids}

        for root, _, filenames in os.walk(Config.WIKI_BASE_DIR):
            for filename in filenames:
                if not filename.endswith(".md") or filename == "index.md":
                    continue

                abs_path = os.path.join(root, filename)
                rel_path = os.path.relpath(abs_path, Config.WIKI_BASE_DIR)

                try:
                    with open(abs_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception:
                    continue

                # Split on anchors, keeping delimiters
                parts = re.split(r"(<!-- section-id: [^ ]+? -->)", content)

                for i, part in enumerate(parts):
                    m = anchor_pattern.fullmatch(part.strip())
                    if not m:
                        continue

                    sid = m.group(1)
                    if sid not in target_ids:
                        continue

                    # Body is the next element after the anchor
                    body = parts[i + 1].strip() if i + 1 < len(parts) else ""

                    heading_match = heading_pattern.search(body)
                    heading = heading_match.group(1) if heading_match else f"Section {sid}"

                    found[sid] = {
                        "file": rel_path,
                        "heading": heading,
                        "content": body,
                    }

                    if len(found) == len(target_ids):
                        return found  # early exit once all found

        # Report any IDs that were not found
        for sid in target_ids:
            if sid not in found:
                found[sid] = {"error": f"Section ID '{sid}' not found in any wiki file."}

        return found