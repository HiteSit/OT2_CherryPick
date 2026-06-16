# Installation

The recommended installation path is Docker Compose. It runs the web GUI and backend without installing the Python or frontend toolchain directly on the host.

## Docker Compose quick start

Run the service from the `docker/` directory:

```bash
cd docker
cp .env.example .env
docker compose up -d --build
```

Open the GUI at:

```text
http://localhost
```

If `HOST_PORT` is changed to a non-standard port such as `8080`, open:

```text
http://localhost:8080
```

## Example environment file

Create `docker/.env` from this template and update the paths for the host machine.

```dotenv
COMPOSE_PROJECT_NAME=ot2cherrypick
HOST_PORT=80

OT2_GUI_WORKSPACE=gui_state
OT2_PROJECT_DIR=/app/gui_state

# Opentrons App data root. Do not point this at labware/ or protocols/.
# Windows via WSL/Docker Desktop:
OPENTRONS_DIR_HOST=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons
OPENTRONS_DIR_MOUNT=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons

# Linux example:
# OPENTRONS_DIR_HOST=/home/YOUR_USERNAME/.config/Opentrons
# OPENTRONS_DIR_MOUNT=/home/YOUR_USERNAME/.config/Opentrons
```

`OPENTRONS_DIR_HOST` is the path Docker mounts from the host. `OPENTRONS_DIR_MOUNT` is the path recorded inside generated configuration. In WSL and Docker Desktop setups these are usually the same `/mnt/c/...` path.

## Runtime commands

Inspect logs:

```bash
docker compose logs -f
```

Stop the service:

```bash
docker compose down
```

Rebuild after an update:

```bash
docker compose up -d --build
```

## Data locations

The Docker service keeps GUI state in the configured workspace directory, normally `gui_state`. Generated protocols and custom labware are synchronized through the Opentrons App data root configured in `.env`.

Back up both locations when preserving a working setup:

- `gui_state/`
- the host Opentrons App data directory

## Documentation build

Build the HTML documentation from the repository root:

```bash
uv run mkdocs build
```

Build the PDF manual:

```bash
ENABLE_PDF_EXPORT=1 uv run mkdocs build
```

The PDF output is written to:

```text
site/pdf/OT2-CherryPick-Manual.pdf
```
