import asyncio
import os

from fastapi.responses import JSONResponse
from constants import AUDIO_CACHE_DIR
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.main import api_router

app = FastAPI()

os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
app.mount("/audio", StaticFiles(directory=AUDIO_CACHE_DIR), name="audio")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.middleware("http")
async def add_process_time_header(request, call_next):
    try:
        response = await asyncio.wait_for(call_next(request), timeout=2400) # 4分钟超时
        return response
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={"detail": "Request processing time exceeded the limit."}
        )
