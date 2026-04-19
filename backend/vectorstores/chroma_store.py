import chromadb
from core.config import Config


class ChromaStore:
    def __init__(self, collection_name=Config.CHROMA_COLLECTION_NAME):
        chroma_client = chromadb.Client()
        self.collection = chroma_client.get_or_create_collection(name=collection_name)

    def store_sections_in_chroma(self, sections):
        valid_sections = []
        for sec in sections:
            content = sec.get("content")
            if content is None:
                continue

            content = str(content).strip()
            if not content:
                continue

            valid_sections.append(
                {
                    "id": str(sec["id"]),
                    "content": content,
                    "sourceid": "" if sec.get("sourceid") is None else str(sec.get("sourceid")),
                }
            )

        if not valid_sections:
            print("No non-empty sections available for ChromaDB storage.")
            return

        self.collection.add(
            ids=[sec["id"] for sec in valid_sections],
            documents=[sec["content"] for sec in valid_sections],
            metadatas=[
                {"sourceid": sec["sourceid"]} for sec in valid_sections
            ],
        )
        print("Sections stored in ChromaDB")

    def get_sections_from_chroma(self, query):
        results = self.collection.query(
            query_texts=[query],
            n_results=2
        )
        return results["documents"]
