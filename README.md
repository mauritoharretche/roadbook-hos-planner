# Roadbook — HOS Trip Planner

Roadbook is a full-stack technical-assessment project for planning a
property-carrying driver's route under the requested Hours of Service (HOS)
constraints. It accepts current, pickup, and dropoff locations plus current
cycle usage, then returns a route, trip timeline, planned stops, daily totals,
and a 24-hour SVG duty-status visualization.

> This is a planning/demo application, not a certified ELD or regulatory
> compliance product.

## Architecture

```text
React + TypeScript + Leaflet
        │  HTTPS / JSON
        ▼
Django + Django REST Framework
        │
        ├── RoutingProvider: MockRoutingProvider | OpenRouteServiceRoutingProvider
        └── Pure Python HOS planner (no Django imports)
```

The frontend only presents backend results. The HOS planner is framework
independent and tested directly; the Django service adapts route legs into
planner inputs.

## Stack

- Python, Django, Django REST Framework
- React, TypeScript, Vite, React Leaflet
- OpenStreetMap tiles
- OpenRouteService for optional server-side production geocoding/routing
- SVG for the visual daily log
- pytest and Vitest

## Local setup

### Backend

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
set -a; source .env; set +a # Django does not auto-load .env files.
.venv/bin/python backend/manage.py runserver
```

For local development, export the values from `.env.example` or configure them
in your shell. The default routing provider is deterministic `mock`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The Vite development proxy sends `/api` requests to Django at
`http://localhost:8000`. To use a deployed API, set
`VITE_API_BASE_URL=https://your-api.example.com/api/v1` before building.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `DJANGO_DEBUG` | `true` locally; `false` in production. |
| `DJANGO_SECRET_KEY` | Required production Django secret. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated deployed API hostnames. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins allowed to call the API. |
| `ROUTING_PROVIDER` | `mock` for deterministic local work; `ors` for OpenRouteService. |
| `ORS_API_KEY` | Required only when `ROUTING_PROVIDER=ors`; never commit it. |
| `VITE_API_BASE_URL` | Frontend API base URL, including `/api/v1`. |

## HOS assumptions

The planner implements only the assessment rules:

- 70 hours / 8 days cycle
- 11-hour driving limit after a qualifying daily reset
- 14-hour driving window
- 30-minute non-driving interruption after 8 cumulative driving hours
- 10 consecutive hours off duty reset the 11-hour/14-hour clocks
- pickup and dropoff each consume one hour of on-duty-not-driving time
- fuel is planned every 1,000 route miles
- fuel duration is a documented 30-minute planning assumption

The assessment provides only aggregate current cycle hours, not the previous
eight days of duty history. Roadbook therefore does **not** fabricate rolling
hour recovery or a 34-hour restart. If remaining cycle capacity cannot finish a
trip, the API returns an explicit infeasible result.

Daily SVG logs show all unplanned portions of a calendar day as visual
off-duty gaps. This is renderer-only normalization: it does not change backend
HOS events, totals, or cycle calculations.

All planning timestamps, calendar-day boundaries, and UI date/time labels use
UTC. The optional departure field is explicitly interpreted as UTC.

## Routing

`MockRoutingProvider` is deterministic and supports the documented demo
routes. `OpenRouteServiceRoutingProvider` performs authenticated, server-side
geocoding and per-leg GeoJSON directions when `ROUTING_PROVIDER=ors`. Provider
errors are returned as HTTP 502.

## Tests and checks

```bash
.venv/bin/python -m pytest
.venv/bin/python backend/manage.py check

cd frontend
npm test
npm run build
npm run lint
```

## Deployment

- Deploy `frontend/` to Vercel. Set `VITE_API_BASE_URL` to the deployed API
  URL plus `/api/v1`.
- Deploy the repository to Render using [render.yaml](render.yaml). Configure
  the generated service hostname in `DJANGO_ALLOWED_HOSTS`, the Vercel origin
  in `CORS_ALLOWED_ORIGINS`, and provide `ORS_API_KEY` with
  `ROUTING_PROVIDER=ors`.
- Confirm `/api/health`, then test a real trip from the hosted frontend.

The repository contains no production secrets. Reference assessment and FMCSA
documents belong in [docs/reference](docs/reference/README.md).
