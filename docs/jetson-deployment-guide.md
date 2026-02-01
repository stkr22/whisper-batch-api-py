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

#### Option 1: Using Docker Compose (Recommended)

Create a [docker-compose.yml](docker-compose.jetson.yml) file.

Start the service:

```bash
docker compose up -d
```

**Note**: Explicit device mappings are required for reliable GPU access on Jetson devices, especially after system updates.

#### Option 2: Using Docker Run

Start the API server:

```bash
docker run -d \
  --name whisper-api \
  --runtime nvidia \
  --device /dev/nvhost-ctrl-gpu \
  --device /dev/nvhost-gpu \
  --device /dev/nvhost-as-gpu \
  --device /dev/nvhost-prof-gpu \
  --device /dev/nvhost-sched-gpu \
  --device /dev/nvhost-ctxsw-gpu \
  --device /dev/nvhost-dbg-gpu \
  --device /dev/nvhost-tsg-gpu \
  --device /dev/nvmap \
  -p 8080:8080 \
  -e ALLOWED_USER_TOKEN=your_secure_token_here \
  whisper-batch-api:jetson
```

### Verifying Deployment

Check CUDA detection:

```bash
docker run --rm --runtime nvidia \
  --device /dev/nvhost-ctrl-gpu \
  --device /dev/nvhost-gpu \
  --device /dev/nvhost-as-gpu \
  --device /dev/nvmap \
  whisper-batch-api:jetson \
  python3 -c 'import ctranslate2; print("CUDA devices:", ctranslate2.get_cuda_device_count())'
```

Expected output: `CUDA devices: 1`

Or simply check the health endpoint:
```bash
curl http://localhost:8080/health
# Expected: {"status":"healthy"}
```

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

To use a different model, set the `WHISPER_MODEL` environment variable in your docker-compose.yml or via docker run:

**Docker Compose:**
```yaml
environment:
  - WHISPER_MODEL=base.en
  - ALLOWED_USER_TOKEN=your_token
```

**Docker Run:**
```bash
docker run -d \
  --name whisper-api \
  --runtime nvidia \
  --device /dev/nvhost-ctrl-gpu \
  --device /dev/nvhost-gpu \
  --device /dev/nvhost-as-gpu \
  --device /dev/nvmap \
  -p 8080:8080 \
  -e ALLOWED_USER_TOKEN=your_token \
  -e WHISPER_MODEL=base.en \
  whisper-batch-api:jetson
```

## Troubleshooting

### NvRmMemInitNvmap Permission Denied

**Error:**
```
NvRmMemInitNvmap failed with Permission denied
Memory Manager Not supported
NvRmMemMgrInit failed
RuntimeError: CUDA failed with error unknown error
```

**Cause:** Container lacks access to `/dev/nvmap` and other Jetson GPU devices.

**Solution:** Use explicit device mappings (see docker-compose.yml above or docker run with `--device` flags). This issue can occur after system updates when the NVIDIA Container Toolkit configuration changes.

**Quick fix:**
```bash
# Stop broken container
docker stop whisper-api && docker rm whisper-api

# Use docker-compose with explicit device mappings
docker compose up -d
```

### CUDA Devices: 0

If `ctranslate2.get_cuda_device_count()` returns 0:

1. Verify you're using the L4T-based Containerfile (`Containerfile.l4t-r36.4`)
2. Ensure device mappings are present (see docker-compose.yml)
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
- Missing device permissions: See "NvRmMemInitNvmap Permission Denied" above

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
