import uuid
from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import json
from typing import Dict, Optional
from constants import SPEEKERS
from utils import combine_audio, generate_dialogue, generate_podcast_info, generate_podcast_summary, get_link_text, get_pdf_text

router = APIRouter()

@router.post("/generate_transcript")
async def generate_transcript(
    pdfFile: Optional[UploadFile] = File(None),
    textInput: str = Form(...),
    mode: str = Form(...),
    url: Optional[str] = Form(None),
    tone: str = Form(...),
    duration: str = Form(...),
    language: str = Form(...),
    
): 
    pdfContent ="" 
    if mode=='pdf':
        pdfContent = await get_pdf_text(pdfFile)
    else:
        linkData = get_link_text(url)
        pdfContent = linkData['text']
    new_text = pdfContent
    return StreamingResponse(generate_dialogue(new_text,textInput, tone, duration, language), media_type="application/json")


@router.get("/test")
def test():
    return {"message": "Hello World"}


@router.get("/speekers")
def speeker():
    return JSONResponse(content=SPEEKERS)

@router.get("/jina")
def jina():
    result = get_link_text("https://ui.shadcn.com/docs/components/select")
    return JSONResponse(content=result)


@router.post("/summarize")
async def get_summary(
    textInput: str = Form(...),
    tone: str = Form(...),
    duration: str = Form(...),
    language: str = Form(...),
    mode: str = Form(...),
    url: Optional[str] = Form(None),
    pdfFile: Optional[UploadFile] = File(None)
):
    pdfContent ="" 
    if mode=='pdf':
        pdfContent = await get_pdf_text(pdfFile)
    else:
        linkData = get_link_text(url)
        pdfContent = linkData['text']
    new_text = pdfContent
    return StreamingResponse(
        generate_podcast_summary(
            new_text,
            textInput,
            tone,
            duration,
            language,
        ),
        media_type="application/json"
    )

@router.post("/pod_info")
async def get_pod_info(
    textInput: str = Form(...),
    tone: str = Form(...),
    duration: str = Form(...),
    language: str = Form(...),
    mode: str = Form(...),
    url: Optional[str] = Form(None),
    pdfFile: Optional[UploadFile] = File(None)
):
    pdfContent ="" 
    if mode=='pdf':
        pdfContent = await get_pdf_text(pdfFile)
    else:
        linkData = get_link_text(url)
        pdfContent = linkData['text']

    new_text = pdfContent[:100]
    
    return StreamingResponse(generate_podcast_info(new_text, textInput, tone, duration, language), media_type="application/json")


task_status: Dict[str, Dict] = {}


@router.post("/generate_audio")
async def audio(
    background_tasks: BackgroundTasks,
    text: str = Form(...),
    host_voice: str = Form(...),
    guest_voice: str = Form(...),
    language: str = Form(...) ,
    provider: str = Form(...)
):  
    task_id = str(uuid.uuid4())
    task_status[task_id] = {"status": "processing"}
    
    background_tasks.add_task(combine_audio, task_status, task_id, text, language,provider , host_voice,guest_voice)

    return JSONResponse(content={"task_id": task_id, "status": "processing"})


@router.get("/audio_status/{task_id}")
async def get_audio_status(task_id: str):
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    status = task_status[task_id]
    
    if status["status"] == "completed":
        return JSONResponse(content={
            "status": "completed",
            "audio_url": status["audio_url"]
        })
    elif status["status"] == "failed":
        return JSONResponse(content={
            "status": "failed",
            "error": status["error"]
        })
    else:
        return JSONResponse(content={
            "status": "processing"
        })
    
    


