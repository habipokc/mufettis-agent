# ===============================
# AWS Lightsail Deployment Script
# ===============================

$PEM_FILE   = "LightsailDefaultKey-eu-central-1.pem"
$HOST_IP    = "3.79.180.143"
$USER       = "ubuntu"
$REMOTE_DIR = "/home/ubuntu/mufettis-agent"

Write-Host "Starting Deployment to AWS Lightsail ($HOST_IP)..." -ForegroundColor Cyan

# Check if PEM file exists
if (-not (Test-Path $PEM_FILE)) {
    Write-Error "CRITICAL: Key file '$PEM_FILE' not found!"
    exit 1
}

# 1. Create remote directory
Write-Host "Creating remote directory..."
ssh -i $PEM_FILE -o StrictHostKeyChecking=no "$USER@${HOST_IP}" "mkdir -p $REMOTE_DIR"

# 2. Transfer Files
Write-Host "Uploading project files..."

# Copy files
$files = @(
    "docker-compose.yml",
    "Dockerfile",
    "pyproject.toml",
    "poetry.lock",
    ".env"
)

foreach ($item in $files) {
    if (Test-Path $item) {
        Write-Host "   Uploading $item"
        scp -i $PEM_FILE $item "$USER@${HOST_IP}:$REMOTE_DIR/"
    }
}

# Copy folders
Write-Host "Uploading backend..."
scp -r -i $PEM_FILE backend "$USER@${HOST_IP}:$REMOTE_DIR/"

Write-Host "Uploading data..."
scp -r -i $PEM_FILE data "$USER@${HOST_IP}:$REMOTE_DIR/"

Write-Host "Uploading mevzuat..."
scp -r -i $PEM_FILE mevzuat "$USER@${HOST_IP}:$REMOTE_DIR/"

# Frontend (compressed)
Write-Host "Uploading frontend (compressed)..."
tar --exclude node_modules --exclude .next --exclude .git -czf frontend.tar.gz frontend
scp -i $PEM_FILE frontend.tar.gz "$USER@${HOST_IP}:$REMOTE_DIR/"
ssh -i $PEM_FILE -o StrictHostKeyChecking=no "$USER@${HOST_IP}" "cd $REMOTE_DIR && tar -xzf frontend.tar.gz && rm frontend.tar.gz"
Remove-Item frontend.tar.gz

# 3. Setup Remote Environment
Write-Host "Configuring remote server..."

# Create setup script with REMOTE_DIR hardcoded (to avoid PowerShell/Bash variable confusion)
$SETUP_SCRIPT = @"
set -e

REMOTE_DIR=/home/ubuntu/mufettis-agent

# 1. Install Docker Compose if missing
if ! docker compose version >/dev/null 2>&1; then
    if ! command -v docker-compose >/dev/null 2>&1; then
        echo "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
fi

# 2. Create Swap (2GB) if not exists
if [ ! -f /swapfile ]; then
    echo "Creating 2GB swap file..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
fi

# 3. Run Docker Compose
cd `$REMOTE_DIR
echo "Current directory: `$(pwd)"
echo "Files in directory:"
ls -la

echo "Building and starting containers..."

# Determine docker compose command
if docker compose version >/dev/null 2>&1; then
    DC_CMD="sudo docker compose"
else
    DC_CMD="sudo docker-compose"
fi

echo "Using: `$DC_CMD"
`$DC_CMD down 2>/dev/null || true
`$DC_CMD up -d --build
"@

# Remove CR characters for Linux compatibility
$SETUP_SCRIPT = $SETUP_SCRIPT -replace "`r", ""
$SETUP_SCRIPT | ssh -i $PEM_FILE -o StrictHostKeyChecking=no "$USER@${HOST_IP}" "bash"

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend URL:  http://${HOST_IP}:8000" -ForegroundColor Cyan
Write-Host "Frontend URL: http://${HOST_IP}:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "To check logs:" -ForegroundColor Yellow
Write-Host "  ssh -i $PEM_FILE ubuntu@$HOST_IP 'cd $REMOTE_DIR && sudo docker compose logs -f'"
