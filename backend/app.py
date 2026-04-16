from fastapi import FastAPI, File, UploadFile
from service.chat_service import ChatService
from service.ingestion_service import IngestionService

app = FastAPI()
ingestion_service = IngestionService()
chat_service = ChatService()

@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    await ingestion_service.ingest_pdf(file)
    return {"file_source": file.filename, "status": "ingested"}

@app.post("/chat")
async def chat(query: str):
    result = chat_service.chat(query)
    return result
