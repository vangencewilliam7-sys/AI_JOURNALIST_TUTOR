"""
Audio transcription route using Deepgram.
"""

import httpx
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from auth import get_current_user
from config import DEEPGRAM_API_KEY

logger = logging.getLogger("course_architect.routes.transcription")
router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...), user_id: str = Depends(get_current_user)):
    if not DEEPGRAM_API_KEY:
        raise HTTPException(status_code=500, detail="Deepgram API key not configured")
        
    try:
        audio_data = await audio.read()
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true",
                headers={
                    "Authorization": f"Token {DEEPGRAM_API_KEY}",
                    "Content-Type": audio.content_type or "audio/webm"
                },
                content=audio_data
            )
            
        if response.status_code == 401 or response.status_code == 403:
            logger.error(f"Deepgram auth error: {response.text}")
            raise HTTPException(status_code=500, detail="Deepgram API key is invalid or expired. Please check your DEEPGRAM_API_KEY in .env")
            
        if response.status_code != 200:
            logger.error(f"Deepgram error ({response.status_code}): {response.text}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: Deepgram returned {response.status_code}")
            
        data = response.json()
        transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
        return {"transcript": transcript}
    except httpx.TimeoutException:
        logger.error("Deepgram request timed out after 120s")
        raise HTTPException(status_code=504, detail="Transcription timed out. The audio file may be too large or Deepgram is slow. Try a shorter recording.")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Transcription error")
        raise HTTPException(status_code=500, detail=str(e))

