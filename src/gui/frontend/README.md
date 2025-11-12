# CherryPick GUI Frontend

React/Mantine client for the OT-2 CherryPick FastAPI backend.

## Dev Workflow

```bash
cd src/gui/frontend
npm install          # already done once
npm run dev:full     # starts FastAPI (+reload) and Vite together
```

- `npm run dev` — UI only (expects API already running on `VITE_API_BASE_URL`)
- `npm run dev:api` — backend only (`uvicorn gui.backend.main:app --reload`)
- `npm run dev:full` — concurrent backend + frontend (requires `uv` on PATH)

Set `VITE_API_BASE_URL` (e.g., in `.env.development`) if the FastAPI server is not on `http://127.0.0.1:8000`.

## Building for Production

```bash
npm run build   # emits dist/ assets
npm run preview # optional: serve the built bundle locally
```

The bundle uses the FastAPI endpoints directly; deploy both the API and the static `dist/` assets (e.g., via Nginx, uvicorn + ASGI static files, etc.).

## Features

- Full `settings.toml` editor (form controls + raw TOML mode)
- Deck layout table with labware catalog lookup
- CSV manager (upload, edit, delete, preview)
- Workflow runner (generate protocol, simulate, deploy/copy)
- React Query caching + Mantine UI + Toast notifications
