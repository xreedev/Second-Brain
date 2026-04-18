# XML Parsing Error Fix - PDF Ingestion

## Problem
When uploading PDF files to the `/ingest` endpoint, the server crashes with:
```
xml.etree.ElementTree.ParseError: not well-formed (invalid token): line 52, column 129
```

This occurs during PDF text extraction and XML conversion in `backend/util/pdf2xml.py`.

## Root Cause
The PDF text extraction produced text containing:
1. Invalid XML characters (control characters like null bytes)
2. Special XML characters (`<`, `>`, `&`) that were not properly escaped
3. These characters caused XML parsing to fail when converting back from XML

## Solution Applied

### 1. **Added XML character escaping** (`xml.sax.saxutils.escape`)
- All text content is now properly escaped before being added to XML elements
- Metadata, headings, and content are all escaped
- This prevents special characters from breaking XML structure

### 2. **Removed invalid control characters**
- Updated `_clean_section_text()` to filter out control characters
- Keeps only valid XML characters (ASCII 32+, plus tab/newline/carriage return)
- This sanitizes text before XML encoding

### 3. **Added error handling with diagnostics**
- `extract_sections_from_xml()` now catches `ParseError` exceptions
- Prints error details and first 500 chars of XML for debugging
- Raises informative `ValueError` instead of raw XML error

### 4. **Added step-tracking print statements**
- `[PDF] Loading PDF file`
- `[PDF] Extracting text lines from PDF`
- `[PDF] Building sections from X extracted lines`
- `[PDF] Extracted Y sections, parsing metadata`
- `[PDF] Converting to XML format`

These align with your logging requirements (print statements for steps only).

## Files Modified
- `backend/util/pdf2xml.py`
  - Added import: `from xml.sax.saxutils import escape`
  - Enhanced `parse()` method with step logging
  - Enhanced `extract_sections_from_xml()` with error handling
  - Enhanced `_clean_section_text()` to remove control characters
  - Enhanced `_to_xml()` to escape all text content

## Testing
To test the fix, upload a PDF file:
```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@your-pdf-file.pdf"
```

You should now see:
```
[PDF] Loading PDF file
[PDF] Extracting text lines from PDF
[PDF] Building sections from 145 extracted lines
[PDF] Extracted 12 sections, parsing metadata
[PDF] Converting to XML format
[INGESTION] Assigned source_id=1 for the new PDF.
[INGESTION] Parsed PDF into 12 sections.
...
```

## Expected Behavior After Fix
- ✅ PDFs with special characters are properly handled
- ✅ Control characters are filtered out
- ✅ XML is properly escaped and parseable
- ✅ Step-tracking logs are printed
- ✅ Better error messages if XML parsing still fails
