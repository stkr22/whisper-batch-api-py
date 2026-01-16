# Jetson Deployment Guide

## Overview

This guide explains how to deploy the Whisper Batch API on NVIDIA Jetson devices with GPU acceleration.

## Prerequisites

- NVIDIA Jetson Orin device (Nano, NX, or AGX)
- JetPack 6.x (L4T R36.4+)
- Docker with NVIDIA Container Runtime
- Sufficient storage for model downloads (~1-2GB)

## Quick Start

### Building the Container

Build the container directly on your Jetson device:

```bash
docker build -f Containerfile.l4t-r36.4 -t whisper-batch-api:jetson .
```

**Note**: Building takes approximately 15-20 minutes due to CTranslate2 compilation from source.

### Running the Container

Start the API server:

```bash
docker run -d \
  --name whisper-api \
  --runtime nvidia \
  --gpus all \
  -p 8080:8080 \
  -e ALLOWED_USER_TOKEN=your_secure_token_here \
  whisper-batch-api:jetson
```

### Verifying Deployment

Check CUDA detection:

```bash
docker run --rm --runtime nvidia --gpus all \
  whisper-batch-api:jetson \
  python3 -c 'import ctranslate2; print("CUDA devices:", ctranslate2.get_cuda_device_count())'
```

Expected output: `CUDA devices: 1`

## API Usage

### Health Check

```bash
curl http://localhost:8080/health
```

### Transcription

The API expects raw float32 audio at 16kHz mono. Convert your audio file first:

```bash
# Convert audio to required format
ffmpeg -i input.wav -f f32le -acodec pcm_f32le -ar 16000 -ac 1 output.raw -y

# Submit for transcription
curl -X POST http://localhost:8080/transcribe \
  -H "user-token: your_secure_token_here" \
  -F "file=@output.raw"
```

Response:
```json
{
  "message": "Transcription successful",
  "text": "your transcribed text here"
}
```

## Technical Details

### Base Image

Uses `nvcr.io/nvidia/l4t-jetpack:r36.4.0` which includes:
- CUDA 12.6
- cuDNN 9.3
- L4T-specific GPU drivers

**Important**: Standard `nvidia/cuda` Docker images do NOT work on Jetson devices. L4T (Linux for Tegra) images are required.

### Custom CTranslate2 Build

CTranslate2 is compiled from source with Jetson-specific optimizations:
- CUDA Architecture: 8.7 (Jetson Orin)
- Optimized for integrated GPU
- FP16 inference support

### Model

Default model: `Systran/faster-distil-whisper-medium.en`

To use a different model, set the `WHISPER_MODEL` environment variable:

```bash
docker run -d \
  --name whisper-api \
  --runtime nvidia \
  --gpus all \
  -p 8080:8080 \
  -e ALLOWED_USER_TOKEN=your_token \
  -e WHISPER_MODEL=base.en \
  whisper-batch-api:jetson
```

## Troubleshooting

### CUDA Devices: 0

If `ctranslate2.get_cuda_device_count()` returns 0:

1. Verify you're using the L4T-based Containerfile (`Containerfile.l4t-r36.4`)
2. Ensure `--runtime nvidia --gpus all` flags are present
3. Check JetPack version matches base image (R36.4.x)

### Container Won't Start

Check logs:
```bash
docker logs whisper-api
```

Common issues:
- Insufficient memory: Jetson Orin Nano 8GB should work, but close other applications
- Model download failure: Check internet connectivity
- Port already in use: Change `-p 8080:8080` to another port

### Build Failures

Network timeouts during pip install:
- Simply retry the build - Docker caches successful layers
- Ensure stable internet connection

## Performance

On Jetson Orin Nano 8GB:
- Model loading: ~10-15 seconds
- Transcription: Real-time or faster (depends on audio length)
- Memory usage: ~2-3GB with medium model

## References

- [NVIDIA L4T JetPack on NGC](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/l4t-jetpack)
- [CTranslate2 Documentation](https://opennmt.net/CTranslate2/)
- [faster-whisper Repository](https://github.com/SYSTRAN/faster-whisper)
- [Debug Log](jetson-debug-log.md) - Detailed troubleshooting journey
