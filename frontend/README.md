# Frontend

## Run locally

1. Start the Django API from the repository root:

   ```bash
   .venv/bin/python backend/manage.py runserver
   ```

2. In another terminal, install and run the frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

The default `VITE_API_BASE_URL=/api/v1` uses the Vite development proxy to reach
the local Django server. Copy `.env.example` to `.env` only when overriding that
base URL.

The app depends on the Django API being available. The current backend uses a
deterministic mock routing provider, so no external mapping key is required.
