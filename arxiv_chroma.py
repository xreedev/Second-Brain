import chromadb

class ChromDBService:

    def __init__(self, collection_name="research"):
        chroma_client = chromadb.Client()
        self.collection = chroma_client.get_or_create_collection(name=collection_name)
        
    def store_sections_in_chroma(self,sections):
        self.collection.add(
            ids= [str(sec["id"]) for sec in sections],
            documents=[sec["content"] for sec in sections],
        )
        print("Sections stored in ChromaDB")
    
    def get_sections_from_chroma(self, query):
        results = self.collection.query(
        query_texts=[query],
        n_results=2 
        )
        return results["documents"]