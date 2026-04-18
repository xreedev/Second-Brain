# Section ID Management Fix - Automated Syncing

## Problem
- **Issue**: LLM was manually creating/guessing section IDs in `index.md`
- **Conflict**: Actual section IDs are generated programmatically by `IndexMapService` in `index.json`
- **Result**: Mismatch between LLM-created IDs in `index.md` and programmatic IDs in `index.json`

## Solution
Implemented **automatic section ID syncing** so:
1. ✅ Section IDs are ONLY generated programmatically (no LLM guessing)
2. ✅ Both `index.json` and `index.md` are updated with the same IDs automatically
3. ✅ LLM focuses on content creation, not ID management

---

## Changes Made

### 1. **Updated Wiki Maintainer Prompt**
**File**: `backend/prompts/wiki_maintainer_prompt.py`

**Changes:**
- ✅ Added explicit instruction: **"Do NOT manage section IDs or update index.md manually"**
- ✅ Removed instruction for LLM to manually update index.md with entries
- ✅ Clarified that system handles section ID generation and index.md updates automatically
- ✅ Focused LLM on content creation only

**Old behavior**: LLM tries to figure out section IDs and update index.md
**New behavior**: LLM creates/updates wiki content, system handles all ID/index management

---

### 2. **Enhanced WikiUpdate Tool**
**File**: `backend/tools/wiki_update.py`

**New Methods Added:**

#### `_sync_index(file_name, content, touched_section_ids)`
- Now calls both index.json AND index.md update
- Coordinates section ID tracking across both files

#### `_update_index_md(wiki_file_name, content, section_ids)`
- Automatically updates `index.md` with section entries
- Extracts page category from YAML frontmatter
- Calls helper methods to extract and add entries

#### `_extract_metadata(content)`
- Parses YAML frontmatter from wiki pages
- Returns `category`, `title`, `created`, `sources`

#### `_extract_sections_data(content, section_ids)`
- Extracts section ID, heading, and summary from content
- Uses heading as displayed name
- Uses first text line as summary
- Truncates summary to 80 chars for table display

#### `_add_entries_to_index(index_content, category, page_name, sections)`
- Adds/updates entries in `index.md` for given category
- Creates category tables if they don't exist
- Removes old entries for page before adding new ones
- Maintains proper markdown table format

#### `_create_default_index()`
- Creates default `index.md` with category tables
- Includes: Concepts, Methods, Findings, Entities, Definitions

---

## Data Flow - Section Creation

```
┌─────────────────────────────────────────────────────────────┐
│ 1. LLM Creates Wiki Page (WITHOUT section IDs)             │
│    Calls: wiki_update(file="concepts.md", mode="create",  │
│            sections=["## Overview\n...", "## Details\n..."]) │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 2. WikiUpdate._run() -> _create_mode                        │
│    - Calls _assign_ids() to generate IDs programmatically  │
│    - Returns IDs: [1, 2, 3, ...]                           │
│    - Renders sections with HTML anchors                    │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 3. _sync_index() called with generated IDs                 │
│    ├─ Updates index.json via IndexService                  │
│    │  Maps: section_id → [source_id]                       │
│    │                                                         │
│    └─ Calls _update_index_md() with same IDs               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 4. _update_index_md() Automatically Updates index.md        │
│    - Extracts category from YAML frontmatter               │
│    - Calls _extract_sections_data() to get headings        │
│    - Calls _add_entries_to_index()                         │
│    - Writes updated index.md with correct section IDs      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ Result: Both index.json and index.md have same section IDs │
│ index.json: { "1": ["source-42"], "2": ["source-42"], ...} │
│ index.md:   | concepts.md | Overview | 1 | Summary...     │
│             | concepts.md | Details | 2 | Summary...      │
└─────────────────────────────────────────────────────────────┘
```

---

## Updated Data Structures

### index.json (Unchanged Format)
```json
{
  "1": ["source-42"],
  "2": ["source-42"],
  "3": ["source-43"]
}
```

### index.md (Auto-updated with IDs)
```markdown
# Wiki Index

## Concepts
| Page | Section | Section ID | Summary |
|------|---------|------------|---------|
| concepts.md | Overview | 1 | Introduction to ML concepts... |
| concepts.md | Neural Networks | 2 | Deep learning architectures... |

## Methods
| Page | Section | Section ID | Summary |
|------|---------|------------|---------|
```

---

## Workflow Comparison

### Before (Broken)
1. LLM reads index.md (doesn't have section IDs yet)
2. LLM guesses/creates section IDs manually
3. WikiUpdate generates IDs programmatically (different from LLM's guess)
4. index.json gets correct IDs, index.md gets wrong IDs
5. **Result: Mismatch!**

### After (Fixed)
1. LLM creates content (NO section ID management)
2. WikiUpdate generates IDs programmatically
3. Both index.json and index.md updated with same IDs automatically
4. **Result: Perfect sync!**

---

## Section Update & Insert Flows

### Mode: Update
```
LLM provides: {"id": "1", "content": "## Updated content..."}
     ↓
WikiUpdate updates section 1 in wiki file
     ↓
_sync_index() called with section_id="1"
     ↓
index.md entry for section 1 updated with new heading/summary
```

### Mode: Insert
```
LLM provides: after_section_id="5", sections=["## New section..."]
     ↓
WikiUpdate generates new ID (e.g., "6")
     ↓
Inserts section 6 after section 5
     ↓
_sync_index() called with section_id="6"
     ↓
index.md entry for section 6 added automatically
```

---

## Logging Output - Section Creation

When a PDF triggers wiki creation, you'll see:
```
[INGESTION] Parsed PDF into 12 sections.
[TOOL] Wiki update - file: concepts.md, mode: create
[INDEX] Updated index.md with 3 section(s) from concepts.md
[TOOL] Wiki update - file: methods.md, mode: create
[INDEX] Updated index.md with 2 section(s) from methods.md
[INGESTION] Wiki maintainer agent completed successfully.
```

---

## Error Handling

If index.md update fails:
- ✅ Does NOT stop wiki file creation
- ✅ Prints warning: `[INDEX] Warning: Could not update index.md: {error}`
- ✅ Wiki file still created successfully
- ✅ index.json still updated correctly

---

## Benefits

1. **No ID Mismatches**: Programmatic IDs are the single source of truth
2. **No LLM Guessing**: Reduces hallucination about section IDs
3. **Automatic Sync**: Both index files stay in sync without manual coordination
4. **Simpler Prompt**: LLM has simpler instructions, focuses on content
5. **Audit Trail**: section_id → source tracking always accurate in index.json

---

## Testing

To verify the fix works:

1. Upload a PDF via `/ingest` endpoint
2. Check console output for `[INDEX] Updated index.md with X section(s)`
3. Verify `wiki/index.md` contains entries with section IDs
4. Verify `wiki/index.json` contains the same section IDs
5. Verify they match exactly

---

## Configuration Files

**No configuration changes needed.** The system works automatically once deployed.

---

## Backward Compatibility

⚠️ **Important**: 
- Existing `index.md` files will be preserved
- New entries will be added to existing categories
- Old entries for same page will be removed and replaced with new ones
- If a page has no category metadata, it won't be indexed (printed warning)
