import chromadb
from core.config import Config


class ChromaStore:
    def __init__(self, collection_name=Config.CHROMA_COLLECTION_NAME):
        chroma_client = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)
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
            metadatas=[{"sourceid": sec["sourceid"]} for sec in valid_sections],
        )
        print("Sections stored in ChromaDB")

    def get_sections_from_chroma(self, query):
        results = self.collection.query(
            query_texts=[query],
            n_results=2,
        )
        return results["documents"]

    def query_by_text_and_source_ids(self, query: str, source_ids: list, n_results: int = 5):
        if not query or not source_ids:
            return []

        source_ids = [str(sid) for sid in source_ids]

        # Cap n_results to the number of matching docs to avoid ChromaDB errors
        count = self.collection.count()
        if count == 0:
            return []
        n_results = min(n_results, count)

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"sourceid": {"$in": source_ids}},
            )
            return results.get("documents", [])
        except Exception as e:
            print(f"[CHROMA] Query error: {e}")
            return []
