# Logging Output Reference

## Ingestion Pipeline Output

When a PDF is uploaded via `/ingest`, you'll see step-by-step console output:

```
[2026-04-18 14:32:15] Assigned source_id=42 for the new PDF.
[2026-04-18 14:32:16] Parsed PDF into 12 sections.
[2026-04-18 14:32:17] Stored and retrieved 12 sections from SQLite for source_id=42.
[2026-04-18 14:32:18] Sections stored in ChromaDB.
[2026-04-18 14:32:18] Current index file content: 1250 characters.
[2026-04-18 14:32:18] Running wiki maintainer agent to create wiki pages...
[TOOL] Reading index file
[TOOL] Wiki update - file: concepts.md, mode: create
[2026-04-18 14:32:45] Wiki maintainer agent completed successfully.
```

**Key Steps Logged:**
1. ✅ Source ID assignment
2. ✅ PDF parsing completion
3. ✅ SQLite storage completion
4. ✅ ChromaDB storage completion
5. ✅ Agent execution start/completion
6. ✅ Tool operations (no full content logged)

**NOT Logged:**
- ❌ Full LLM response text
- ❌ Full PDF content
- ❌ Full wiki markdown generated
- ❌ Individual section contents

---

## Chat Pipeline Output

When a user queries via `/chat`, you'll see:

```
[CHAT] Processing user query
[CHAT] Index ensured to exist
[CHAT] Running wiki process agent
[TOOL] Reading index file
[TOOL] Reading wiki sections - 2 request(s)
[CHAT] Agent completed
```

**Key Steps Logged:**
1. ✅ Query receipt
2. ✅ Index preparation
3. ✅ Agent execution start/completion
4. ✅ Tool operations count (not content)

**NOT Logged:**
- ❌ User query text
- ❌ Full LLM response
- ❌ Wiki section contents
- ❌ Search results

---

## Log Files (File-based Logging)

Detailed logs are still written to files for auditing:

### `logs/ingestion.log`
Contains step-by-step ingestion process in structured format.
**Format:** `[timestamp] message`

### `logs/chat.log` (Deprecated)
Previously contained query/response. Now only contains step messages.

### `logs/chat_tools.log` (Deprecated)
Previously contained tool details. Now replaced by print statements.

---

## Monitoring Best Practices

### For Development
Monitor the console for `[TOOL]` and `[CHAT]` print statements to track execution flow.

### For Production
- Check `logs/ingestion.log` for successful PDF ingestions
- Monitor console output for real-time step tracking
- Use structured logging with timestamps for debugging

### Performance Metrics (To Add)
- Parsing time per PDF
- Section count per PDF
- Agent execution time
- Vector storage time

---

## Debugging Hints

If ingestion stalls, watch for these steps:
1. `Parsed PDF into X sections` - PDF parsing worked
2. `Stored and retrieved X sections from SQLite` - Database worked
3. `Sections stored in ChromaDB` - Vector DB worked
4. `Running wiki maintainer agent...` - Agent processing started
5. `Wiki maintainer agent completed successfully` - Success!

If any step is missing, the failure occurred at that point.

---

## Environment Setup for Logging

No additional setup needed. Print statements are enabled by default.

Logs are stored in:
- `logs/ingestion.log` - Ingestion process logs
- Console output - Real-time step tracking

To disable file logging (dev only), comment out the `self.logger()` call in `ingestion_service.py`.
