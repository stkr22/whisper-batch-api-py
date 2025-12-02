import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Annotated

import faster_whisper
import numpy as np
from fastapi import FastAPI, Header, HTTPException, UploadFile
from pydantic import BaseModel

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

ml_models: dict[str, faster_whisper.WhisperModel] = {}


class TranscriptionResult(BaseModel):
    message: str
    text: str


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Load the ML model
    ml_models["transcriber_engine"] = faster_whisper.WhisperModel(
        os.getenv("WHISPER_MODEL", "distil-medium.en"),
        device="cuda",
        compute_type="float16",
    )
    yield
    # Clean up the ML models and release the resources
    ml_models.clear()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}


@app.post("/transcribe")
async def transcribe(
    file: UploadFile,
    user_token: Annotated[str | None, Header()] = None,
) -> TranscriptionResult:
    transcriber_engine = ml_models["transcriber_engine"]
    if user_token != os.environ["ALLOWED_USER_TOKEN"]:
        raise HTTPException(status_code=403)
    audio_bytes = await file.read()
    audio_np = np.frombuffer(audio_bytes, dtype=np.float32)
    if "distil" in os.getenv("WHISPER_MODEL", "distil-medium.en"):
        batched_model = faster_whisper.BatchedInferencePipeline(
            model=transcriber_engine
        )
        optimal_chunks = (
            15 * 16000
        )  # filling to recommended size of 15s https://github.com/huggingface/distil-whisper/blob/a07edc4f3840bca33c5dc495303196bf6d0b2c40/README.md?plain=1#L131
        desired_length = np.ceil(audio_np.size / optimal_chunks) * optimal_chunks
        pad_size = int(desired_length) - audio_np.size
        padded_array = np.pad(audio_np, (0, pad_size), "constant", constant_values=(0))
        audio_np = padded_array
        segments, _info = batched_model.transcribe(
            audio_np,
            language="en",
            temperature=0,
            batch_size=2,
            max_new_tokens=128,
            condition_on_previous_text=False,
        )
    else:
        segments, _info = transcriber_engine.transcribe(
            audio_np,
            max_new_tokens=224,
            beam_size=5,
            temperature=0,
            language="en",
            condition_on_previous_text=False,
        )
    final_text = ""

    for segment in segments:
        final_text += segment.text

    return TranscriptionResult(
        message="Transcription successful", text=final_text.strip()
    )
