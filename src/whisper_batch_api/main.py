import base64
import os
from typing import Annotated

import numpy as np
from fastapi import FastAPI, Header, HTTPException
from faster_whisper import WhisperModel
from pydantic import BaseModel

app = FastAPI()


class AudioData(BaseModel):
    audio_base64: str
    dtype: str = "float32"


class TranscriptionResult(BaseModel):
    message: str
    text: str


WHISPER_MODEL = os.getenv("WHISPER_MODEL", "distil-medium.en")
ALLOWED_USER_TOKEN = os.environ["ALLOWED_USER_TOKEN"]
TRANSCRIBER_OBJ = WhisperModel(
    WHISPER_MODEL,
    device="cpu",
    compute_type="int8",
)


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}


@app.post("/transcribe")
async def transcribe(
    audio_data: AudioData, user_token: Annotated[str | None, Header()] = None
) -> TranscriptionResult:
    if user_token != ALLOWED_USER_TOKEN:
        raise HTTPException(status_code=403)
    try:
        # Convert base64 string back to numpy array
        audio_bytes = base64.b64decode(audio_data.audio_base64)
        audio_np = np.frombuffer(audio_bytes, dtype=audio_data.dtype)

        segments, info = TRANSCRIBER_OBJ.transcribe(
            audio_np,
            language="en",
            max_new_tokens=128,
            condition_on_previous_text=False,
        )
        final_text = ""
        for segment in segments:
            final_text += segment.text

        return TranscriptionResult(message="Transcription successful", text=final_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
