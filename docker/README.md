# Docker Deployment for OT-2 CherryPick GUI

Containerized deployment using Docker Compose with an Nginx reverse proxy.

## Quick Start

Create a `.env` file in this `docker/` directory, then start the stack:

```bash
cd docker
cp .env.example .env
docker compose up -d --build
```

The included `docker/.env.example` uses this template:

```dotenv
COMPOSE_PROJECT_NAME=ot2cherrypick
HOST_PORT=80

OT2_GUI_WORKSPACE=gui_state
OT2_PROJECT_DIR=/app/gui_state

# Opentrons App data root. This directory must contain labware/ and protocols/.
# Windows via WSL/Docker Desktop:
OPENTRONS_DIR_HOST=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons
OPENTRONS_DIR_MOUNT=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons

# Linux example:
# OPENTRONS_DIR_HOST=/home/YOUR_USERNAME/.config/Opentrons
# OPENTRONS_DIR_MOUNT=/home/YOUR_USERNAME/.config/Opentrons
```

Open the GUI at `http://localhost` when `HOST_PORT=80`. If port 80 is already
used, set `HOST_PORT=8080` in `.env`, restart with `docker compose up -d`, and
open `http://localhost:8080`.

## Compose Commands

Run these commands from the `docker/` directory:

```bash
# Build/rebuild and start in the background
docker compose up -d --build

# Show service status
docker compose ps

# Follow logs
docker compose logs -f

# Stop containers, keeping gui_state and logs volumes
docker compose down

# Stop and delete persistent volumes too
docker compose down -v
```

## Environment Variables

`docker-compose.yml` expects these values from `.env`:

| Variable | Purpose |
| --- | --- |
| `COMPOSE_PROJECT_NAME` | Prefix for Compose resources and named volumes. Use `ot2cherrypick` unless you need multiple installs. |
| `HOST_PORT` | Host port exposed by Nginx. Defaults to `80` if omitted. |
| `OT2_GUI_WORKSPACE` | Workspace name inside the backend repo. Use `gui_state`. |
| `OT2_PROJECT_DIR` | Persistent project directory inside the backend container. Use `/app/gui_state`. |
| `OPENTRONS_DIR_HOST` | Host path to the Opentrons App data root. |
| `OPENTRONS_DIR_MOUNT` | Container path for that same Opentrons App data root. Usually keep it identical to `OPENTRONS_DIR_HOST`. |

`OPENTRONS_DIR_HOST` must point to the Opentrons root directory that contains
both `labware/` and `protocols/`. Do not set it to either subdirectory. On
Windows through WSL/Docker Desktop, use the `/mnt/c/...` form.

## Architecture

```
┌─────────────────────────────────────────┐
│  User Browser (http://localhost)        │
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

Nginx serves the built React SPA on port 80 and reverse-proxies `/api/*` to the FastAPI backend on internal port 8000. The backend runs `opentrons_simulate` inside the container and reads/writes configuration under `/app/gui_state`.

## Data Persistence

Two named Docker volumes maintain state across container restarts.

### `gui_state` volume
Configuration files and CSV transfer maps:
- `settings.toml`
- `labware_dict.toml`
- `shell_settings.json`
- `CSVs/*.csv`

### `logs` volume
Application logs and simulation output:
- `last_simulation.json`
- Other debug logs

### Inspecting and backing up

The compose project name (`COMPOSE_PROJECT_NAME=ot2cherrypick` in `.env`)
prefixes volume names, so the real volumes are `ot2cherrypick_gui_state` and
`ot2cherrypick_logs`.

```bash
# List volumes
docker volume ls | grep ot2cherrypick

# Inspect
docker volume inspect ot2cherrypick_gui_state

# Backup
docker run --rm -v ot2cherrypick_gui_state:/data -v $(pwd):/backup \
  alpine tar czf /backup/gui_state_backup.tar.gz /data

# Restore
docker run --rm -v ot2cherrypick_gui_state:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/gui_state_backup.tar.gz --strip 1"
```

In addition to these named volumes, the host's Opentrons App data directory is
bind-mounted read-write into the backend container at the path set by
`OPENTRONS_DIR_HOST` / `OPENTRONS_DIR_MOUNT` in `.env`, giving the container
access to custom labware definitions and protocol directories.
