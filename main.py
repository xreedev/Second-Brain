from pathlib import Path
import xml.etree.ElementTree as ET

from components.arxiv_chroma import ChromDBService
from components.arxiv_parser import ArxivParser
from components.sqllite_service import SQLiteService
from components.summarize_agent import GeminiAgent


def main() -> None:
    pdf_path = Path("paper/test.pdf")
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    parser = ArxivParser()
    sqlite_service = SQLiteService(db_name="papers.db")
    chroma_service = ChromDBService(collection_name="research")
    gemini_agent = GeminiAgent(system_prompt="Please summarize the paper in markdown.\n\n")

    xml_output = parser.parse(pdf_path, output_format="xml")
    print("Parsed PDF to XML successfully.")

    source_id = str(pdf_path.resolve())
    sections = parser.extract_sections_from_xml(xml_output)
    print(f"Extracted {len(sections)} sections from the paper.")

    sqlite_service.create_table("documents")
    sqlite_service.store_sections_in_sqlite(
        [
            (sec["content"], sec["page"], sec["heading"], source_id)
            for sec in sections
        ]
    )
    print("Stored sections in SQLite.")

    retrieved_sections = sqlite_service.get_sections_from_sqlite()
    print(f"Retrieved {len(retrieved_sections)} sections from SQLite.")

    chroma_service.store_sections_in_chroma(retrieved_sections)
    print("Stored sections in ChromaDB.")

    query = "What is the main contribution of the paper?"
    chroma_results = chroma_service.get_sections_from_chroma(query)
    print("Chroma query results:", chroma_results)

    paper_text = parser.build_paper_text(retrieved_sections)
    summary = gemini_agent.summarize_scientific_paper_to_markdown(paper_text)
    print("Generated paper summary.")

    output_file = Path("output.md")
    output_file.write_text(summary, encoding="utf-8")
    print(f"Summary written to {output_file.resolve()}")


if __name__ == "__main__":
    main()
