from arxiv_parser import parse_arxiv
from arxiv_chroma import store_sections_in_chroma, get_sections_from_chroma
from sqllite_service import store_sections_in_sqlite, get_sections_from_sqlite
import xml.etree.ElementTree as ET

xml  = parse_arxiv("paper/test.pdf", output_format="xml")
root = ET.fromstring(xml)

sections = []

for sec in root.findall(".//section"):
    heading = sec.find("heading")
    content = sec.find("content")

    sections.append({
        "heading": heading.text if heading is not None else "",
        "content": content.text if content is not None else "",
        "page": sec.attrib.get("page")
    })
print(f"Extracted {len(sections)} sections from the paper.")

store_sections_in_sqlite([(sec["content"], sec["page"], sec["heading"]) for sec in sections])
retrieved_sections = get_sections_from_sqlite()
print("Sections retrieved from SQLite:")

store_sections_in_chroma([{ "content": sec["content"], "id": sec["id"] }
    for sec in retrieved_sections 
    if sec["content"] and isinstance(sec["content"], str) and sec["content"].strip()])
query = "What is the main contribution of the paper?"
retrieved_sections = get_sections_from_chroma(query)
print(retrieved_sections[0])

