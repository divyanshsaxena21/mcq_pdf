from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import tempfile
import os

from mcq_engine.extractor import (
    extract_sections_from_pdf,
    extract_sections_from_docx,
    extract_sections_from_pptx,
    extract_sections_from_youtube,
)
from mcq_engine.generator import generate_mcqs_from_sections

app = FastAPI()

# Allow CORS for your frontend (adjust origin as needed)
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")  # default fallback
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MCQRequest(BaseModel):
    input_type: str
    youtube_url: Optional[str] = None

@app.post("/generate_mcqs/youtube/")
async def generate_mcqs_youtube(request: MCQRequest):
    input_type = request.input_type.lower()
    if input_type != "youtube":
        raise HTTPException(status_code=400, detail="Input type must be 'youtube'")
    if not request.youtube_url:
        raise HTTPException(status_code=400, detail="YouTube URL required")
    sections = extract_sections_from_youtube(request.youtube_url)
    results = generate_mcqs_from_sections(sections)
    return {"results": results}

@app.post("/generate_mcqs/file/")
async def generate_mcqs_file(
    input_type: str = Form(...),
    file: UploadFile = File(...)
):
    input_type = input_type.lower()
    if input_type not in ["pdf", "docx", "pptx"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{input_type}") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    if input_type == "pdf":
        sections = extract_sections_from_pdf(tmp_path)
    elif input_type == "docx":
        sections = extract_sections_from_docx(tmp_path)
    elif input_type == "pptx":
        sections = extract_sections_from_pptx(tmp_path)

    results = generate_mcqs_from_sections(sections)
    return {"results": results}
