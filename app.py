from fastapi import FastAPI, File, UploadFile
from service import IngestionService

app = FastAPI()
ingestion_service = IngestionService()

@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    await ingestion_service.ingest_pdf(file)
    return {"file_source": file.filename, "status": "ingested"}

@app.get("/chat")
async def chat(query: str):
    return ''