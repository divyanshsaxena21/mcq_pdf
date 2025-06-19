from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import tempfile
import os

# Import functions from mcq_engine
from mcq_engine.extractor import (
    extract_sections_from_pdf,
    extract_sections_from_docx,
    extract_sections_from_pptx,
    extract_sections_from_youtube,
)
from mcq_engine.generator import generate_mcqs_from_sections

# Initialize the FastAPI app
app = FastAPI()

# CORS Configuration: Allowing frontend to interact with the backend
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")  # Adjust the frontend URL as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],  # Set your frontend URL here
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Pydantic model to handle incoming request payloads
class MCQRequest(BaseModel):
    input_type: str
    youtube_url: Optional[str] = None

# Route for generating MCQs from YouTube video
@app.post("/generate_mcqs/youtube/")
async def generate_mcqs_youtube(request: MCQRequest):
    input_type = request.input_type.lower()
    
    # Validate the input type
    if input_type != "youtube":
        raise HTTPException(status_code=400, detail="Input type must be 'youtube'")
    
    # Validate YouTube URL
    if not request.youtube_url:
        raise HTTPException(status_code=400, detail="YouTube URL required")
    
    # Extract sections from the YouTube video and generate MCQs
    sections = extract_sections_from_youtube(request.youtube_url)
    results = generate_mcqs_from_sections(sections)
    
    return {"results": results}

# Route for generating MCQs from uploaded files (PDF, DOCX, PPTX)
@app.post("/generate_mcqs/file/")
async def generate_mcqs_file(
    input_type: str = Form(...),
    file: UploadFile = File(...),
):
    input_type = input_type.lower()
    
    # Validate the file type
    if input_type not in ["pdf", "docx", "pptx"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Read file contents
    contents = await file.read()

    # Create a temporary file with the content
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{input_type}") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    # Extract sections based on the file type
    if input_type == "pdf":
        sections = extract_sections_from_pdf(tmp_path)
    elif input_type == "docx":
        sections = extract_sections_from_docx(tmp_path)
    elif input_type == "pptx":
        sections = extract_sections_from_pptx(tmp_path)

    # Generate MCQs from extracted sections
    results = generate_mcqs_from_sections(sections)
    
    return {"results": results}