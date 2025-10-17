Performance tuning notes for AI-Coaching-Andreas

This project contains both frontend (Vite + React + Tailwind) and backend (FastAPI + Python) components. Below are quick actionable steps and configuration knobs to improve performance and tune trade-offs.

Frontend optimizations implemented:
- Code-splitting via Vite `manualChunks` for major vendor libraries to reduce initial bundle size.
- Lazy loading for heavy top-level components (`FilesSection`, `AIAssistantSection`, `ReportEditorModal`, `PerformanceMonitor`).
- React rendering optimizations: `React.memo`, `useMemo`, `useCallback` applied to hot components like `FilesSection`, `AIAssistantSection`, and `ChatMessage`.
- Reduced debug logging and disabled source maps in production builds.

Backend optimizations implemented:
- In-memory caching (`backend/cache.py`) and `/files` endpoint cached for 60s.
- Cache invalidation added to mutating endpoints (upload, upload-multiple, delete, copy, move, create folder).
- OCR tuning: limit number of Tesseract configs via `OCR_MAX_TRIES` env var and early exit on good confidence.
- Excel processing: use `pandas.read_csv` with `low_memory=True`, sample rows for very large files to avoid memory blowup.
- Added `/performance` endpoint returning cache stats.

Tuning knobs (environment variables):
- OCR_MAX_TRIES (default: 6) - Reduce to speed up image OCR at cost of accuracy.

Quick commands

Install frontend deps and run dev server (frontend only):

```bash
cd frontend/client
npm install
npm run dev
```

Run backend (FastAPI) locally:

```bash
cd backend
pip install -r ../requirements.txt
uvicorn backend.api.main:app --reload --port 8000
```

Next steps and suggestions:
- Add Redis-backed cache for persistence and process-shared caching in production.
- Add a job queue (Celery/RQ) for heavy vector store creation and image processing to avoid blocking API requests.
- Add APM (Sentry Performance, NewRelic, or OpenTelemetry) for end-to-end tracing.
- Add rate limits and graceful degradation for heavy endpoints.

If you'd like, I can:
- Wire Redis cache and show a migration path.
- Convert heavy processing endpoints to background tasks with progress reporting.
- Add unit and integration tests for performance-critical paths.
