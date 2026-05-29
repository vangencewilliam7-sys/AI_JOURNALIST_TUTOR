"""
File parsing and chunking logic for data ingestion.
"""

import io
import fitz  # PyMuPDF
import docx
from youtube_transcript_api import YouTubeTranscriptApi
from config import CHUNK_SIZE, CHUNK_OVERLAP

def _read_file_content(file_bytes: bytes, filename: str) -> str:
    ext = filename.split(".")[-1].lower()
    if ext == "pdf":
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    elif ext in ["txt", "md", "csv"]:
        return file_bytes.decode("utf-8", errors="replace")
    elif ext == "docx":
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

def _chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += (CHUNK_SIZE - CHUNK_OVERLAP)
    return chunks

def fetch_youtube_transcript(url: str) -> str:
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL")
        
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join([t['text'] for t in transcript_list])
