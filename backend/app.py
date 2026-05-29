"""
Main FastAPI Application Entrypoint.
Refactored to industry standards: components, modules, dependencies.
"""

import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from routes import interview, synthesis, knowledge, transcription

logger = logging.getLogger("course_architect")

app = FastAPI(
    title="AI Course Architect",
    version="2.0.0",
    description="Industry-grade backend for extracting course tacit knowledge."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview.router, tags=["Interview"])
app.include_router(synthesis.router, tags=["Synthesis"])
app.include_router(knowledge.router, tags=["Knowledge Hub"])
app.include_router(transcription.router, tags=["Audio"])

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}

if __name__ == "__main__":
    logger.info(f"Starting server... Allowed CORS: {CORS_ORIGINS}")
    uvicorn.run(app, host="0.0.0.0", port=9120)
