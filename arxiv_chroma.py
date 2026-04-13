import chromadb
chroma_client = chromadb.Client()

collection = chroma_client.get_or_create_collection(name="papers")

def store_sections_in_chroma(sections):
    collection = chroma_client.get_or_create_collection(name="papers")
    collection.add(
            ids= [str(sec["id"]) for sec in sections],
            documents=[sec["content"] for sec in sections],
        )
    print("Sections stored in ChromaDB")
    
def get_sections_from_chroma(query):
    collection = chroma_client.get_or_create_collection(name="papers")
    results = collection.query(
        query_texts=[query],
        n_results=2 
    )
    return results["documents"]