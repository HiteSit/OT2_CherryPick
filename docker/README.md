# Docker Deployment for OT-2 CherryPick GUI

Containerized deployment using Docker Compose with an Nginx reverse proxy.

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

The compose project name (`COMPOSE_PROJECT_NAME=ot2cherrypick` in `.env`) prefixes volume names, so the real volumes are `ot2cherrypick_gui_state` and `ot2cherrypick_logs`.

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

In addition to these named volumes, the host's Opentrons App data directory is bind-mounted read-write into the backend container at the path set by `OPENTRONS_DIR_HOST` / `OPENTRONS_DIR_MOUNT` in `.env`, giving the container access to custom labware definitions and protocol directories.
