# Jetson Self-Hosted Runner Setup Guide

## Quick Setup

### 1. Install GitHub Actions Runner on Jetson

```bash
# Download and extract runner
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -O -L https://github.com/actions/runner/releases/download/v2.330.0/actions-runner-linux-arm64-2.330.0.tar.gz
# Extract the installer
tar xzf ./actions-runner-linux-arm64-2.330.0.tar.gz

# Configure (get token from GitHub repo settings)
./config.sh --url https://github.com/stkr22/whisper-batch-api-py --token YOUR_TOKEN

# Last step, run it!
./run.sh

# When prompted, add labels: self-hosted,Linux,ARM64,jetson

# Install and start as service
sudo ./svc.sh install
sudo ./svc.sh start
```

### 2. Configure Docker Access

```bash
# Add runner to docker group
sudo usermod -aG docker $(whoami)

# Restart runner service
sudo ./svc.sh stop
sudo ./svc.sh start
```

### 3. Get Configuration Token

Visit: `https://github.com/stkr22/whisper-batch-api-py/settings/actions/runners/new`

Select **Linux** and **ARM64**, copy the token shown.

## Verify Setup

Check runner status on GitHub:
`https://github.com/stkr22/whisper-batch-api-py/settings/actions/runners`

Should show:
- ✅ **jetson-orin-nano** (or your runner name)
- Status: **Idle** (green)
- Labels: `self-hosted`, `Linux`, `ARM64`, `jetson`

## Maintenance

```bash
# Check runner status
sudo ~/actions-runner/svc.sh status

# View logs
journalctl -u actions.runner.* -f

# Stop/start runner
sudo ~/actions-runner/svc.sh stop
sudo ~/actions-runner/svc.sh start

# Update runner (when new version available)
cd ~/actions-runner
sudo ./svc.sh stop
sudo ./svc.sh uninstall
curl -o actions-runner-linux-arm64-NEW_VERSION.tar.gz -L DOWNLOAD_URL
tar xzf ./actions-runner-linux-arm64-NEW_VERSION.tar.gz
sudo ./svc.sh install
sudo ./svc.sh start
```

## Troubleshooting

### Runner offline
```bash
sudo systemctl status actions.runner.*
sudo ~/actions-runner/svc.sh start
```

### Docker permission denied
```bash
sudo usermod -aG docker $(whoami)
# Log out and back in, or:
sudo ~/actions-runner/svc.sh restart
```

### Build fails with out of disk space
```bash
docker system prune -af --volumes
```
