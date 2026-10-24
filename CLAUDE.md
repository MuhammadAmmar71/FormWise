# CLAUDE.md

Unofficial AI helper for the German residence registration (Anmeldung). It is a portfolio project for an M.Sc. E-Government application (Universität Koblenz). It answers in EN/DE **only** from official sources, with citations.

> Keep this file current: update **Status** and anything else that changes whenever the project changes.

## Hard constraints
- **$0 budget**: Groq (chat), Gemini (embeddings), Supabase (pgvector), Vercel (frontend), Render/HF Spaces (backend). Don't add paid services.
- **No real personal data**: no chat logging, no accounts. Form practice values stay in browser state. `backend/app/pii.py` redacts before any LLM call.
- **Clearly unofficial**: keep the banner, the disclaimer and the "not endorsed" wording. Never imply affiliation with Uni Koblenz or any authority.
- **Scope**: the Anmeldung only, EN + DE only. Urdu and HEC attestation were deliberately dropped.
- **Grounding**: answers must cite retrieved chunks. If it can't, it refuses (see `check` in `graph.py`). Don't loosen this to "improve" answers.

## Research references (use exactly)
- Klass, Ibrahim, Straub, Kolekar, Bahle, Theiß, Wecker, Veith, Jaeger, **Wimmer** (last author). *Supporting Patients in Administrative Form-Filling through Conversational Agents: A Case from an Orthopedic Technology Provider.* AI4DPS 2025 @ STAF 2025, Koblenz.
- "Chatbot for AI-based form-filling help" is a **WS 2024/25 research-internship topic** of Prof. Wimmer's group, **not a lab**.

## Layout
- `ingest/`: `sources.yaml` (allow-list of official URLs and sections) → `fetch.py` → `raw/` → `chunk.py` → `chunks.jsonl` → `embed_upload.py` (Gemini 768-d, normalized) → Supabase. `raw/` and `chunks.jsonl` are gitignored.
- `supabase/migrations/001_init.sql`: `sources`, `chunks`, HNSW index, `match_chunks` RPC. RLS is on; only the service role can read.
- `backend/app/`
  - `graph.py`: LangGraph `prepare → route → (out_of_scope | retrieve → answer → check)`. Chat and retrieve functions are **injected** so tests run offline.
  - `main.py`: FastAPI `/chat`, `/form/anmeldung`, `/health`, with slowapi rate limiting and CORS from `ALLOWED_ORIGINS`.
  - `llm.py`, `retrieval.py`: raw httpx calls, no SDKs.
  - `config.py`: all settings come from env vars.
  - `forms/anmeldung.json`: field schema, checklist and `sources` map. It is the **single source of truth**, and the frontend imports it at build time.
- `frontend/`: Vite + React 19 + TS. `src/i18n.ts` holds all UI strings (EN/DE). The components are `Chat.tsx` and `FormWalkthrough.tsx`.
- `eval/`: `questions.jsonl` (28 in-scope + 4 out-of-scope) and `run_eval.py` (`--full` uses Groq quota).

## Commands
```bash
# Python (venv at repo root)
.venv/bin/ruff check backend ingest eval            # config: ruff.toml
cd backend && ../.venv/bin/python -m pytest -q
cd backend && ../.venv/bin/uvicorn app.main:app --reload --port 8000
.venv/bin/python ingest/fetch.py && .venv/bin/python ingest/chunk.py && .venv/bin/python ingest/embed_upload.py
.venv/bin/python eval/run_eval.py [--full]
# Frontend
cd frontend && npm run dev | npm run build | npm run lint
```
Secrets go in `backend/.env` (see `backend/.env.example`). Frontend: `VITE_API_URL` in `frontend/.env`.

## Conventions and gotchas
- Adding a source: edit `sources.yaml`, then run `fetch` → `chunk` → `embed_upload`. Also update the `sources` map in `anmeldung.json` (a test enforces that the URLs match).
- Every `sources` id referenced in `anmeldung.json` must exist in `sources.yaml` (enforced by a test).
- Field help text must be supported by the cited source. Don't add facts the sources don't contain.
- User-facing text always needs both `en` and `de`.
- The npm registry is very slow on this machine, so run `npm install` in the background.
- Tests must not hit the network. Use the fakes in `backend/tests/test_graph.py`.

## Status (last updated 2026-10-24)
- Done: ingest pipeline (24 chunks, verified), migration, backend + 16 passing tests, frontend (builds, lints), eval set, README, DISCLAIMER, CI, Dockerfile.
- **Not yet verified**: real Groq/Gemini/Supabase calls (no keys yet), UI in a browser, eval numbers, `MIN_SIMILARITY=0.55` tuning.
- Placeholders: live demo URL in README, GitHub link in `frontend/src/App.tsx` footer, LICENSE holder name (guessed).
- Not committed yet (git initialised only).

## Next steps
1. Add API keys, run the migration and ingest, run the eval, and fill in the README results table.
2. Check the UI in a browser and tune `MIN_SIMILARITY`.
3. Deploy (Vercel + Render/HF Spaces), set `ALLOWED_ORIGINS`, and replace the placeholders.
4. Optional: a small usability test with 3–5 people, written up in the README.
