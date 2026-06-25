import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx

app = FastAPI(
    title="VirtualMind Ollama MCP Server",
    description="Servidor MCP con Ollama para VirtualMind",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:latest"

class GenerateRequest(BaseModel):
    model: Optional[str] = DEFAULT_MODEL
    prompt: str
    system: Optional[str] = None
    temperature: float = 0.7
    stream: bool = False

@app.get("/")
def root():
    return {"name": "VirtualMind Ollama MCP Server", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "ollama": "connected"}

@app.post("/generate")
async def generate(request: GenerateRequest):
    async with httpx.AsyncClient(timeout=120.0) as client:
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": False,
            "options": {"temperature": request.temperature}
        }
        if request.system:
            payload["system"] = request.system
        
        try:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: GenerateRequest):
    async with httpx.AsyncClient(timeout=120.0) as client:
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": request.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": request.temperature}
        }
        
        try:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models():
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
