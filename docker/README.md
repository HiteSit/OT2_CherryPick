# Docker Deployment for OT-2 CherryPick GUI

Production-ready containerized deployment using Docker Compose with Nginx reverse proxy.

## Architecture

```
┌─────────────────────────────────────────┐
│  User Browser (http://localhost)       │
└──────────────┬──────────────────────────┘
               │
        ┌──────▼──────┐
        │   Nginx     │  Port 80
        │ (frontend)  │
        └──────┬──────┘
               │
       ┌───────┴────────┐
       │                │
   /   │            /api│
  (SPA)│           (proxy)
       │                │
       ▼                ▼
  React Static    FastAPI Backend
   (built-in)      Port 8000
                   (internal)
```

**Benefits:**
- ✅ Single port (80) - no CORS issues
- ✅ Production-ready nginx serving
- ✅ Persistent volumes for configs
- ✅ Health checks and auto-restart
- ✅ Non-root containers (security)

## Quick Start

### Prerequisites

- Docker Desktop installed and running
- At least 4GB RAM available
- Ports 80 and 8000 free (or configure `HOST_PORT`)

### 1. Build and Start

```bash
# From repository root
cd docker

# Build images (takes 3-5 minutes first time)
docker compose build

# Start services
docker compose up -d

# View logs
docker compose logs -f
```

### 2. Access the Application

Open your browser to:
- **http://localhost** - Main GUI
- **http://localhost/health** - Health check endpoint

The API is automatically proxied at `/api/*` endpoints.

### 3. Stop Services

```bash
# Stop containers
docker compose down

# Stop and remove volumes (CAUTION: deletes all data)
docker compose down -v
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Available variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST_PORT` | `80` | Port to expose on host machine |
| `OT2_GUI_WORKSPACE` | `gui_state` | Workspace directory name |

### Custom Port

To run on a different port (e.g., 8080):

```bash
# In .env file
HOST_PORT=8080

# Restart services
docker compose down
docker compose up -d

# Access at http://localhost:8080
```

## Data Persistence

Docker volumes maintain state across container restarts:

### `gui_state` Volume
Stores configuration files and CSVs:
- `settings.toml`
- `labware_dict.toml`
- `shell_settings.json`
- `CSVs/*.csv`

### `logs` Volume
Stores application logs:
- `last_simulation.json`
- Other debug logs

### Inspecting Volumes

```bash
# List volumes
docker volume ls | grep ot2

# Inspect gui_state location
docker volume inspect docker_gui_state

# Backup gui_state volume
docker run --rm -v docker_gui_state:/data -v $(pwd):/backup \
  alpine tar czf /backup/gui_state_backup.tar.gz /data

# Restore gui_state volume
docker run --rm -v docker_gui_state:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/gui_state_backup.tar.gz --strip 1"
```

## Development Workflow

### Rebuild After Code Changes

```bash
# Rebuild specific service
docker compose build backend   # or frontend
docker compose up -d backend

# Rebuild everything
docker compose build --no-cache
docker compose up -d
```

### View Real-Time Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend

# Last 50 lines
docker compose logs --tail=50 backend
```

### Shell Access

```bash
# Backend container shell
docker compose exec backend /bin/bash

# Check opentrons_simulate installation
docker compose exec backend opentrons_simulate --version

# View gui_state contents
docker compose exec backend ls -la /app/gui_state
```

## Troubleshooting

### Port Already in Use

**Error:** `bind: address already in use`

**Solution:**
```bash
# Check what's using port 80
sudo lsof -i :80  # Linux/Mac
netstat -ano | findstr :80  # Windows

# Option 1: Stop conflicting service
# Option 2: Change HOST_PORT in .env
```

### Backend Health Check Failing

**Error:** Container marked as unhealthy

**Solution:**
```bash
# Check backend logs
docker compose logs backend

# Common issues:
# - Missing dependencies (check uv.lock sync)
# - Module import errors (check PYTHONPATH)
# - Port conflict (verify 8000 internal port free)

# Manual health check
docker compose exec backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/settings')"
```

### Frontend Build Failures

**Error:** npm build fails during Docker build

**Solution:**
```bash
# Check Node version compatibility
docker compose build frontend --progress=plain 2>&1 | grep -A 10 "npm"

# Common issues:
# - package-lock.json out of sync (delete and regenerate)
# - Node memory limit (increase Docker Desktop RAM)

# Test frontend build locally
cd src/gui/frontend
npm ci
npm run build
```

### Volume Permission Issues

**Error:** Permission denied in gui_state

**Solution:**
```bash
# Recreate volumes with correct permissions
docker compose down -v
docker compose up -d

# Or manually fix permissions
docker compose exec backend chown -R root:root /app/gui_state
```

## Production Deployment

### Security Hardening

1. **Change CORS settings** in `src/gui/backend/main.py`:
   ```python
   allow_origins=["https://your-domain.com"]
   ```

2. **Enable HTTPS** with Let's Encrypt:
   ```yaml
   # Add certbot service to docker-compose.yml
   # Update nginx.conf for SSL
   ```

3. **Set resource limits** in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```

### Monitoring

Add health check monitoring:

```bash
# Check service health
docker compose ps

# Monitor resource usage
docker stats ot2-cherrypick-backend ot2-cherrypick-frontend
```

## Architecture Details

### Network Flow

1. **User requests http://localhost/**
   → Nginx serves React SPA (`/usr/share/nginx/html`)

2. **React makes API call to `/api/settings`**
   → Nginx proxies to `http://backend:8000/settings`
   → FastAPI processes request (with `--root-path /api`)
   → Response sent back through Nginx

3. **SPA routing** (`/workflow`, `/settings`)
   → Nginx `try_files` falls back to `index.html`
   → React Router handles client-side routing

### Build Process

**Backend:**
1. Install UV package manager
2. Install system deps (pipx for opentrons)
3. Copy `pyproject.toml` and `uv.lock`
4. Install Python dependencies
5. Install `opentrons_simulate` via pipx
6. Copy source code
7. Run uvicorn with `--root-path /api`

**Frontend:**
1. **Stage 1 (Build):**
   - Install npm dependencies
   - Set `VITE_API_BASE_URL=/api`
   - Build React app to `/frontend/dist`
2. **Stage 2 (Serve):**
   - Copy nginx config
   - Copy built assets from Stage 1
   - Run nginx as non-root user

## FAQ

**Q: Why use Nginx instead of serving React with Node?**
A: Nginx is 5-10x faster for static files, production-ready, and industry standard.

**Q: Can I use this for development?**
A: Yes, but `./scripts/run_gui_dev.sh` is faster (hot reload). Use Docker for testing production config.

**Q: How do I update configurations?**
A: Edit files via the GUI. They're persisted in the `gui_state` volume. Or `docker compose exec backend vi /app/gui_state/settings.toml`.

**Q: Can I run this on Windows/Mac?**
A: Yes! Docker Desktop works on all platforms. Just ensure Docker is running.

**Q: Why `/api` prefix for backend?**
A: Standard convention for reverse proxies. Frontend calls `/api/*`, nginx strips `/api` and proxies to backend.

## Additional Resources

- [FastAPI Docker Deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Multi-stage Docker Builds](https://docs.docker.com/build/building/multi-stage/)

## Support

For issues specific to Docker deployment, check:
1. Docker logs: `docker compose logs -f`
2. Health checks: `docker compose ps`
3. Container shell: `docker compose exec backend /bin/bash`

For application issues, see main project `README.md` and `CLAUDE.md`.
