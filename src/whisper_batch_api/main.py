import base64

import numpy as np
from fastapi import FastAPI, HTTPException
from faster_whisper import WhisperModel
from pydantic import BaseModel

app = FastAPI()


class AudioData(BaseModel):
    audio_base64: str
    dtype: str = "float32"  # Assuming the client tells you the dtype


class TranscriptionResult(BaseModel):
    message: str
    data: str


transcriber_obj = WhisperModel("tiny.en", device="cpu", compute_type="int8")


@app.post("/transcribe/")
async def transcribe(audio_data: AudioData) -> TranscriptionResult:
    try:
        # Convert base64 string back to numpy array
        audio_bytes = base64.b64decode(audio_data.audio_base64)
        audio_np = np.frombuffer(audio_bytes, dtype=audio_data.dtype)

        segments, info = transcriber_obj.transcribe(audio_np)
        final_text = ""
        for segment in segments:
            final_text += segment.text

        return TranscriptionResult(message="Transcription successful", data=final_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
