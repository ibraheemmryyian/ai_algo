from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import json
from typing import Optional, List

# Import processing logic
from ui.processing.pipeline_adapter import run_generate, run_humanize
from ui.processing.file_extractor import extract_text, auto_detect_mode
from ui.processing.fingerprint import extract_fingerprint, fingerprint_to_prompt_block

app = FastAPI(title="Entropy Engine API", version="1.0")

# Enable CORS for Vite frontend (running on port 5173 typically)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    topic: str
    mode: str = "pulse"
    target_words: int = 150
    context: str = ""
    draft_count: int = 1
    main_model: str = "gpt-4o"
    jitter_model: str = "gpt-4o-mini"
    skip_jitter: bool = False
    seed: Optional[int] = None
    tone_fingerprint_block: str = ""
    api_key_override: str = ""

class HumanizeRequest(BaseModel):
    text: str
    mode: str = "pulse"
    jitter_model: str = "gpt-4o-mini"
    skip_jitter: bool = False
    api_key_override: str = ""

def apply_api_key(api_key: str):
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

@app.post("/api/generate")
def generate_endpoint(req: GenerateRequest):
    apply_api_key(req.api_key_override)
    try:
        result = run_generate(
            topic=req.topic,
            mode=req.mode,
            target_words=req.target_words,
            context=req.context,
            draft_count=req.draft_count,
            main_model=req.main_model,
            jitter_model=req.jitter_model,
            skip_jitter=req.skip_jitter,
            seed=req.seed,
            tone_fingerprint_block=req.tone_fingerprint_block
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/humanize")
def humanize_endpoint(req: HumanizeRequest):
    apply_api_key(req.api_key_override)
    try:
        result = run_humanize(
            text=req.text,
            mode=req.mode,
            jitter_model=req.jitter_model,
            skip_jitter=req.skip_jitter
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_endpoint(
    file: UploadFile = File(...),
    mode: str = Form("auto"),
    jitter_model: str = Form("gpt-4o-mini"),
    skip_jitter: bool = Form(False),
    api_key_override: str = Form("")
):
    apply_api_key(api_key_override)
    try:
        file_bytes = await file.read()
        extracted_text = extract_text(file_bytes, file.filename)
        
        target_mode = mode
        if mode == "auto":
            target_mode = auto_detect_mode(extracted_text)
            
        result = run_humanize(
            text=extracted_text,
            mode=target_mode,
            jitter_model=jitter_model,
            skip_jitter=skip_jitter
        )
        # Attach extracted text info to the result
        result["extracted_source"] = file.filename
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fingerprint")
async def fingerprint_endpoint(files: List[UploadFile] = File(...)):
    try:
        samples_text = []
        for file in files:
            file_bytes = await file.read()
            text = extract_text(file_bytes, file.filename)
            if text.strip():
                samples_text.append(text)
                
        if not samples_text:
            raise HTTPException(status_code=400, detail="No readable text found in uploaded files.")
            
        fp = extract_fingerprint(samples_text)
        fp_block = fingerprint_to_prompt_block(fp)
        
        return {
            "fingerprint": fp,
            "prompt_block": fp_block
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
