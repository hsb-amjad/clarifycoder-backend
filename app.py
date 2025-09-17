# uvicorn app:app --reload --port 8000

import sys
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

from clarifycoder_agent.agents.runner import run_clarifycoder

app = FastAPI(title="ClarifyCoder API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    prompt: str
    mode: str
    answer_mode: str = "auto"
    answers: Optional[List[str]] = None


@app.get("/")
def root():
    return {"message": "ClarifyCoder Backend is running 🚀"}


@app.post("/run_prompt")
def run_prompt_api(req: PromptRequest):
    result = run_clarifycoder(
        req.prompt,
        req.mode,
        answers=req.answers,
        answer_mode=req.answer_mode   # <-- forward this
    )
    return {
        "prompt": req.prompt,
        "mode": req.mode,
        **result
    }
