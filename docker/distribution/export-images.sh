#!/bin/bash
set -e

# ============================================================================
# OT-2 CherryPick Docker Image Export Script
# ============================================================================
# Purpose: Build, export, and package Docker images for offline distribution
# Usage: ./export-images.sh [version]
# Example: ./export-images.sh 1.0.0
# ============================================================================

# Configuration
VERSION="${1:-1.0.0}"
PACKAGE_NAME="ot2-cherrypick-v${VERSION}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/${PACKAGE_NAME}"
DOCKER_DIR="$(dirname "${SCRIPT_DIR}")"
REPO_ROOT="$(dirname "${DOCKER_DIR}")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Docker is installed and running
check_docker() {
    log_info "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi

    log_success "Docker is installed and running"
}

# Clean up previous builds
cleanup_previous() {
    log_info "Cleaning up previous distribution files..."
    rm -rf "${OUTPUT_DIR}"
    rm -f "${SCRIPT_DIR}/${PACKAGE_NAME}.zip"
    rm -f "${SCRIPT_DIR}/ot2cherrypick-backend.tar.gz"
    rm -f "${SCRIPT_DIR}/ot2cherrypick-frontend.tar.gz"
    log_success "Cleanup complete"
}

# Build Docker images
build_images() {
    log_info "Building Docker images (this may take 5-10 minutes)..."
    cd "${DOCKER_DIR}"

    if docker compose build --no-cache; then
        log_success "Docker images built successfully"
    else
        log_error "Failed to build Docker images"
        exit 1
    fi

    cd "${SCRIPT_DIR}"
}

# Export images to TAR files
export_images() {
    log_info "Exporting backend image..."
    docker save ot2cherrypick/backend:latest | gzip > "${SCRIPT_DIR}/ot2cherrypick-backend.tar.gz"
    BACKEND_SIZE=$(du -h "${SCRIPT_DIR}/ot2cherrypick-backend.tar.gz" | cut -f1)
    log_success "Backend exported (${BACKEND_SIZE})"

    log_info "Exporting frontend image..."
    docker save ot2cherrypick/frontend:latest | gzip > "${SCRIPT_DIR}/ot2cherrypick-frontend.tar.gz"
    FRONTEND_SIZE=$(du -h "${SCRIPT_DIR}/ot2cherrypick-frontend.tar.gz" | cut -f1)
    log_success "Frontend exported (${FRONTEND_SIZE})"
}

# Create distribution package structure
create_package_structure() {
    log_info "Creating distribution package structure..."
    mkdir -p "${OUTPUT_DIR}/images"

    # Move exported images
    mv "${SCRIPT_DIR}/ot2cherrypick-backend.tar.gz" "${OUTPUT_DIR}/images/"
    mv "${SCRIPT_DIR}/ot2cherrypick-frontend.tar.gz" "${OUTPUT_DIR}/images/"

    # Copy docker-compose.yml
    cp "${DOCKER_DIR}/docker-compose.yml" "${OUTPUT_DIR}/"

    # Create .env.example from .env or template
    if [ -f "${DOCKER_DIR}/.env" ]; then
        cp "${DOCKER_DIR}/.env" "${OUTPUT_DIR}/.env.example"
    else
        cat > "${OUTPUT_DIR}/.env.example" << 'EOF'
# Environment variables for Docker Compose
# Copy this file to .env and customize as needed

# Docker Compose project name
COMPOSE_PROJECT_NAME=ot2cherrypick

# Port to expose on host machine
HOST_PORT=80

# GUI workspace directory name (inside container)
OT2_GUI_WORKSPACE=gui_state
OT2_PROJECT_DIR=/app/gui_state

# REQUIRED: Custom labware directory path (WSL/Linux format)
# Windows path: C:\Users\YOUR_USERNAME\AppData\Roaming\Opentrons\labware
# WSL/Linux path: /mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons/labware
LABWARE_PATH_HOST=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons/labware
LABWARE_PATH_MOUNT=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons/labware

# REQUIRED: Opentrons protocols parent directory (WSL/Linux format)
# Windows path: C:\Users\YOUR_USERNAME\AppData\Roaming\Opentrons\protocols
# WSL/Linux path: /mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons/protocols
PROTOCOLS_DIR_HOST=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons/protocols
PROTOCOLS_DIR_MOUNT=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons/protocols
EOF
    fi

    log_success "Package structure created"
}

# Create README
create_readme() {
    log_info "Creating README..."
    cat > "${OUTPUT_DIR}/README.md" << 'EOF'
# OT-2 CherryPick Docker Installation Guide

## System Requirements

- **Docker Desktop** installed and running
- At least 4GB RAM available
- 2GB free disk space
- Port 80 available (or configure custom port in .env)

## Quick Start

### Linux/Mac Installation

```bash
# 1. Run installation script
./install.sh

# 2. Configure paths (edit .env file)
nano .env

# 3. Restart services if you changed .env
docker compose down
docker compose up -d

# 4. Access application
# Open browser to: http://localhost
```

### Windows Installation

```batch
# 1. Run installation script
install.bat

# 2. Configure paths (edit .env file)
notepad .env

# 3. Restart services if you changed .env
docker compose down
docker compose up -d

# 4. Access application
# Open browser to: http://localhost
```

## Configuration

### Required: Update .env File

Before starting, you **must** configure the following paths in `.env`:

1. **LABWARE_PATH_HOST** - Path to Opentrons custom labware directory
   - Windows example: `/mnt/c/Users/YourName/AppData/Roaming/Opentrons/labware`
   - Linux example: `/home/user/opentrons/labware`

2. **PROTOCOLS_DIR_HOST** - Path to Opentrons protocols directory
   - Windows example: `/mnt/c/Users/YourName/AppData/Roaming/Opentrons/protocols`
   - Linux example: `/home/user/opentrons/protocols`

**Note:** Use WSL format for Windows paths (e.g., `/mnt/c/Users/...`)

### Optional: Custom Port

To run on a different port (e.g., 8080):

```bash
# In .env file
HOST_PORT=8080
```

Then access at: http://localhost:8080

## Managing the Application

### View Logs

```bash
docker compose logs -f
```

### Stop Application

```bash
docker compose down
```

### Restart Application

```bash
docker compose restart
```

### Update to New Version

1. Stop current version: `docker compose down`
2. Extract new version package
3. Load new images: `./install.sh`
4. Copy your .env file to new directory
5. Start: `docker compose up -d`

## Troubleshooting

### Port Already in Use

**Error:** `bind: address already in use`

**Solution:** Change `HOST_PORT` in `.env` to a different port (e.g., 8080)

### Docker Not Running

**Error:** Cannot connect to Docker daemon

**Solution:** Start Docker Desktop application

### Images Not Loading

**Error:** Failed to load images

**Solution:**
1. Verify tar.gz files exist in `images/` directory
2. Check Docker has enough disk space
3. Try loading manually:
   ```bash
   docker load -i images/ot2cherrypick-backend.tar.gz
   docker load -i images/ot2cherrypick-frontend.tar.gz
   ```

### Permission Denied (Linux)

**Solution:** Run Docker commands with `sudo` or add your user to docker group:
```bash
sudo usermod -aG docker $USER
# Then logout and login again
```

## Data Persistence

Your configuration and CSV files are stored in Docker volumes:
- `gui_state` - Configuration files, CSVs, generated protocols
- `logs` - Application logs

These persist even when containers are stopped or recreated.

### Backup Data

```bash
docker run --rm -v ot2cherrypick_gui_state:/data -v $(pwd):/backup \
  alpine tar czf /backup/gui_state_backup.tar.gz /data
```

### Restore Data

```bash
docker run --rm -v ot2cherrypick_gui_state:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/gui_state_backup.tar.gz --strip 1"
```

## Support

For issues or questions, contact your system administrator or refer to the main documentation.
EOF
    log_success "README created"
}

# Create installation scripts
create_install_scripts() {
    log_info "Creating installation scripts..."

    # Linux/Mac install script
    cat > "${OUTPUT_DIR}/install.sh" << 'EOF'
#!/bin/bash
set -e

echo "=== OT-2 CherryPick Docker Installer ==="
echo ""

# Check Docker installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker Desktop first."
    exit 1
fi

# Check Docker running
if ! docker info &> /dev/null; then
    echo "ERROR: Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✓ Docker is installed and running"
echo ""

# Load images
echo "Loading Docker images (this may take 2-3 minutes)..."
docker load -i images/ot2cherrypick-backend.tar.gz
docker load -i images/ot2cherrypick-frontend.tar.gz

echo "✓ Images loaded successfully"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env configuration file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and configure your paths:"
    echo "   - LABWARE_PATH_HOST (path to Opentrons labware directory)"
    echo "   - PROTOCOLS_DIR_HOST (path to Opentrons protocols directory)"
    echo ""
    echo "After editing .env, run: docker compose up -d"
    exit 0
fi

# Start services
echo "Starting services..."
docker compose up -d

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Access the application at: http://localhost"
echo ""
echo "Useful commands:"
echo "  View logs:    docker compose logs -f"
echo "  Stop:         docker compose down"
echo "  Restart:      docker compose restart"
EOF
    chmod +x "${OUTPUT_DIR}/install.sh"

    # Windows install script
    cat > "${OUTPUT_DIR}/install.bat" << 'EOF'
@echo off
echo === OT-2 CherryPick Docker Installer ===
echo.

REM Check Docker installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check Docker running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

echo ✓ Docker is installed and running
echo.

REM Load images
echo Loading Docker images (this may take 2-3 minutes)...
docker load -i images\ot2cherrypick-backend.tar.gz
docker load -i images\ot2cherrypick-frontend.tar.gz

echo ✓ Images loaded successfully
echo.

REM Check if .env exists
if not exist .env (
    echo Creating .env configuration file...
    copy .env.example .env
    echo.
    echo ⚠️  IMPORTANT: Please edit .env file and configure your paths:
    echo    - LABWARE_PATH_HOST (path to Opentrons labware directory)
    echo    - PROTOCOLS_DIR_HOST (path to Opentrons protocols directory)
    echo.
    echo After editing .env, run: docker compose up -d
    pause
    exit /b 0
)

REM Start services
echo Starting services...
docker compose up -d

echo.
echo === Installation Complete ===
echo.
echo Access the application at: http://localhost
echo.
echo Useful commands:
echo   View logs:    docker compose logs -f
echo   Stop:         docker compose down
echo   Restart:      docker compose restart
echo.
pause
EOF

    log_success "Installation scripts created"
}

# Generate checksums for verification
generate_checksums() {
    log_info "Generating SHA256 checksums..."
    cd "${OUTPUT_DIR}/images"
    sha256sum *.tar.gz > checksums.sha256
    cd "${SCRIPT_DIR}"
    log_success "Checksums generated"
}

# Create final ZIP package
create_zip_package() {
    log_info "Creating ZIP package..."
    cd "${SCRIPT_DIR}"

    if command -v zip &> /dev/null; then
        zip -r "${PACKAGE_NAME}.zip" "${PACKAGE_NAME}/" > /dev/null
    else
        log_warning "zip command not found, using tar.gz instead"
        tar czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}/"
        PACKAGE_NAME="${PACKAGE_NAME}.tar.gz"
    fi

    PACKAGE_SIZE=$(du -h "${SCRIPT_DIR}/${PACKAGE_NAME}"* | grep -v "/${PACKAGE_NAME}/" | cut -f1)
    log_success "Package created: ${PACKAGE_NAME} (${PACKAGE_SIZE})"
}

# Clean up extracted directory after zipping
cleanup_extracted_directory() {
    log_info "Cleaning up extracted directory..."
    rm -rf "${OUTPUT_DIR}"
    log_success "Cleanup complete - only ZIP file remains"
}

# Print summary
print_summary() {
    echo ""
    echo "========================================================================"
    echo -e "${GREEN}Distribution Package Created Successfully!${NC}"
    echo "========================================================================"
    echo ""
    echo "Package Details:"
    echo "  Location: ${SCRIPT_DIR}/${PACKAGE_NAME}.zip"
    echo "  Version:  ${VERSION}"
    echo ""
    echo "Package Contents:"
    echo "  - Docker images (backend + frontend)"
    echo "  - docker-compose.yml"
    echo "  - .env.example"
    echo "  - Installation scripts (Linux/Mac + Windows)"
    echo "  - README.md"
    echo "  - SHA256 checksums"
    echo ""
    echo "Next Steps:"
    echo "  1. Test the package by extracting and running install.sh"
    echo "  2. Distribute ${PACKAGE_NAME}.zip to customers"
    echo "  3. Provide README.md for installation instructions"
    echo ""
    echo "========================================================================"
}

# Main execution
main() {
    echo ""
    echo "========================================================================"
    echo "OT-2 CherryPick Docker Image Export"
    echo "Version: ${VERSION}"
    echo "========================================================================"
    echo ""

    check_docker
    cleanup_previous
    build_images
    export_images
    create_package_structure
    create_readme
    create_install_scripts
    generate_checksums
    create_zip_package
    cleanup_extracted_directory
    print_summary
}

# Run main function
main
