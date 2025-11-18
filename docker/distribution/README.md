# Docker Distribution Package Creator

This directory contains the script to build, export, and package Docker images for offline distribution.

## Quick Start

```bash
cd docker/distribution
./export-images.sh 1.0.0
```

This will create `ot2-cherrypick-v1.0.0.zip` in this directory containing everything needed for customer installation.

## Usage

```bash
./export-images.sh [version]
```

**Arguments:**
- `version` (optional) - Version number for the package (default: 1.0.0)

**Examples:**
```bash
./export-images.sh           # Creates v1.0.0
./export-images.sh 1.2.3     # Creates v1.2.3
./export-images.sh 2.0.0-rc1 # Creates v2.0.0-rc1
```

## What the Script Does

1. ✅ Checks Docker is installed and running
2. ✅ Cleans up any previous export files
3. ✅ Builds Docker images using `docker compose build`
4. ✅ Exports images to compressed TAR files
5. ✅ Creates distribution package structure
6. ✅ Generates README and installation scripts
7. ✅ Creates SHA256 checksums for verification
8. ✅ Packages everything into a ZIP file

## Output Structure

After running the script, you'll get:

```
docker/distribution/
├── ot2-cherrypick-v1.0.0.zip          # Final distribution package
└── ot2-cherrypick-v1.0.0/             # Extracted contents
    ├── images/
    │   ├── ot2cherrypick-backend.tar.gz
    │   ├── ot2cherrypick-frontend.tar.gz
    │   └── checksums.sha256
    ├── docker-compose.yml
    ├── .env.example
    ├── install.sh                      # Linux/Mac installer
    ├── install.bat                     # Windows installer
    └── README.md                       # Customer installation guide
```

## Distribution Package Contents

### Images (~600 MB compressed)
- **backend.tar.gz** - FastAPI backend + opentrons_simulate
- **frontend.tar.gz** - React frontend + Nginx

### Configuration Files
- **docker-compose.yml** - Service orchestration
- **.env.example** - Environment variable template

### Installation Scripts
- **install.sh** - Automated Linux/Mac installation
- **install.bat** - Automated Windows installation

### Documentation
- **README.md** - Complete installation and troubleshooting guide
- **checksums.sha256** - File integrity verification

## Customer Installation Flow

### Linux/Mac
```bash
unzip ot2-cherrypick-v1.0.0.zip
cd ot2-cherrypick-v1.0.0
./install.sh
```

### Windows
```cmd
Extract ZIP file
cd ot2-cherrypick-v1.0.0
install.bat
```

The installer will:
1. Load Docker images from TAR files
2. Create `.env` from `.env.example`
3. Prompt user to configure paths
4. Start services with `docker compose up -d`

## Testing the Distribution Package

Before sending to customers, test the package:

```bash
# 1. Create test directory
mkdir /tmp/test-install
cd /tmp/test-install

# 2. Extract package
unzip ~/path/to/ot2-cherrypick-v1.0.0.zip
cd ot2-cherrypick-v1.0.0

# 3. Run installation
./install.sh

# 4. Configure .env
nano .env
# Set your LABWARE_PATH_HOST and PROTOCOLS_DIR_HOST

# 5. Start services
docker compose up -d

# 6. Test application
curl http://localhost/health

# 7. Cleanup
docker compose down -v
cd /tmp && rm -rf test-install
```

## Prerequisites

### On Build Machine (Your System)
- Docker Desktop installed and running
- 4GB+ free disk space
- `zip` or `tar` command available

### On Customer Machine
- Docker Desktop installed
- 2GB+ free disk space
- Port 80 available (or configured custom port)
- Access to Opentrons labware and protocols directories

## Troubleshooting

### "Docker is not running"
**Solution:** Start Docker Desktop before running the script

### "No space left on device"
**Solution:** Free up disk space or clean up old Docker images:
```bash
docker system prune -a
```

### "Permission denied"
**Solution:** Make script executable:
```bash
chmod +x export-images.sh
```

### Build fails
**Solution:** Check Docker logs:
```bash
cd ../
docker compose build --progress=plain
```

## Versioning Best Practices

Use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR** - Incompatible changes (e.g., 2.0.0)
- **MINOR** - New features, backwards compatible (e.g., 1.1.0)
- **PATCH** - Bug fixes (e.g., 1.0.1)

**Examples:**
```bash
./export-images.sh 1.0.0    # Initial release
./export-images.sh 1.0.1    # Bug fix
./export-images.sh 1.1.0    # New feature
./export-images.sh 2.0.0    # Breaking changes
```

## File Sizes

Typical package sizes:
- Backend image (compressed): ~500 MB
- Frontend image (compressed): ~80 MB
- **Total package**: ~600 MB

Uncompressed images require ~1.4 GB disk space on customer machine.

## Security Notes

The exported images contain:
- **Source code** - Python and JavaScript source files are included
- **No secrets** - Ensure no credentials in environment variables
- **Compiled bytecode** - Python .pyc files generated at runtime

For source code protection, see production Dockerfiles in the main documentation.

## Automation

To automate distribution package creation:

```bash
# In CI/CD pipeline
cd docker/distribution
./export-images.sh ${CI_COMMIT_TAG}

# Upload to artifact storage
aws s3 cp ot2-cherrypick-v${CI_COMMIT_TAG}.zip s3://releases/
```

## Support

For issues with the export script, check:
1. Docker is running: `docker info`
2. Disk space available: `df -h`
3. Permissions correct: `ls -la export-images.sh`
4. View detailed output during build for errors
