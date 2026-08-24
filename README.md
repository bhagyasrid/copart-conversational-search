# Copart Conversational Search

A working, responsive prototype for finding and refining a 200-vehicle inventory with natural-language queries. It demonstrates NVIDIA NIM-assisted multi-turn interpretation, deterministic filtering, visible search criteria, undo, zero-result recovery, favorites, comparisons, sorting, and vehicle details with simulated seller-disclosure reasons and damage severity. The 56 make/model combinations use distinct, openly licensed representative photos with visible source attribution; photos and condition data do not represent real auction lots.

**Live demo:** https://copart-conversational-search-bhagyasrid.banny51202.chatgpt.site

## Run locally

Prerequisites: Node.js 22.13 or later.

```bash
npm install
npm run dev
```

Open the local URL printed in the terminal. For a production check, run `npm run build`. Tests run with `npm test`.

To enable the same AI interpretation used by the public demo, set `NVIDIA_API_KEY` in the server environment. The default model is `meta/llama-3.1-8b-instruct`; override it with `NVIDIA_MODEL` if needed. Never expose the key through a `NEXT_PUBLIC_*` variable or commit it to source control. Without a key, the application remains usable through its deterministic parser.

## Try these conversations

- `Include Honda`
- `Only clean titles`
- `Under 20k`
- `Lower mileage`
- `Remove the location`
- `Show me trucks from 2021 or newer`
- `Reset search`
- `Between $15k and $30k`
- `Electric or hybrid AWD SUVs`
- `No Ford and exclude flood damage`
- `Undo`

## Architecture

The prototype is a React 19/TypeScript application running on vinext/Vite. A curated 200-vehicle inventory is held in memory so the reviewer can run the complete experience immediately. A same-origin server route sends the current filter state and each refinement to NVIDIA NIM, using `meta/llama-3.1-8b-instruct` by default. The model returns a constrained filter object across make, model, body, year, bid, mileage, state, fuel, transmission, drive, title, damage, and color. The server normalizes that object before deterministic search; conversational text never executes as code or a database query. If NVIDIA or the route is unavailable, the client uses the local deterministic interpreter.

The browser stores liked vehicles, recent searches, and comparison history in `localStorage`, so they survive refreshes on the same browser and device. This is intentionally guest-device persistence, not authenticated cross-device storage.

The repository also includes a production-oriented Python/FastAPI service under `backend/`. The unchanged React UI can call it by setting `NEXT_PUBLIC_SEARCH_API_URL`; when the service is unavailable, the client safely falls back to its local parser. The API validates a typed search schema, supports NVIDIA NIM parsing and JWT identity, and includes configuration boundaries for PostgreSQL, OpenSearch, Redis, OpenTelemetry, Docker, and AWS ECS/Fargate. These services are production-path adapters and are not claimed as active infrastructure behind the public Sites demo.

The production version would preserve this separation: an LLM or intent service would propose a schema-validated filter update, while the search service would own authorization, normalization, query construction, and ranking. PostgreSQL or OpenSearch would replace the in-memory collection, Redis would hold short-lived session state, and inventory updates would arrive through an event pipeline.

### Why combine an LLM with deterministic search?

NVIDIA NIM handles flexible conversational phrasing and multi-turn intent, while a typed filter contract and deterministic matching keep retrieval inspectable and testable. The local parser is a resilience mechanism: it keeps setup simple and the demo usable without secrets or network access. This separation lets the model, validation layer, and inventory repository evolve independently without changing the search UI.

## Key decisions

- **Runnable without secrets:** deterministic natural-language parsing makes the assignment easy to review.
- **LLM-assisted interpretation:** NVIDIA NIM converts conversational refinements into the same constrained filter contract.
- **Stateful refinement:** each message updates rather than recreates the active criteria.
- **Transparent interpretation:** active filter chips show what the system understood.
- **Safe search boundary:** only allowlisted fields and operations reach the search layer.
- **Testable behavior:** parser and search scenarios run without model or network variability.
- **Honest simulated data:** representative photos, sale reasons, prices, and damage severity are visibly disclosed as demonstration data.
- **Lightweight persistence:** guest history and liked/compared vehicles persist locally without requiring authentication.
- **Production path:** the UI and typed filter contract can remain while the parser and repository are swapped independently.

## Current scope and next steps

The inventory, lot identifiers, bids, seller reasons, and damage percentages are simulated. Photos are openly licensed, representative make/model images rather than actual auction-lot evidence. A production-facing capability would connect to an authorized inventory feed containing actual lot photos, VIN/lot identity, inspections, damage records, and seller disclosures; add authenticated sessions and database-backed inventory; and introduce geospatial search, relevance ranking, streaming responses, rate limiting, prompt-injection defenses, audit logs, tracing, accessibility testing, and offline evaluation sets for interpretation and result quality.

## Run the production-style backend

Copy `backend/.env.example` to `backend/.env`, then run `docker compose up --build`. The API is available at `http://localhost:8000`, with health at `/health` and interactive documentation at `/docs`. Set `NEXT_PUBLIC_SEARCH_API_URL=http://localhost:8000` before starting the frontend to connect it. `NVIDIA_API_KEY` is optional; without it the API uses the deterministic parser, keeping local development reproducible and secret-free. On EC2/ECS, inject the key from AWS Secrets Manager as `NVIDIA_API_KEY`; never commit it to `.env` or source control.

The included `infra/ecs-task-definition.json` is a deployment template for AWS ECS/Fargate with CloudWatch logs and Secrets Manager. Production PostgreSQL, OpenSearch, Redis, OAuth issuer, networking, domains, and IAM resources must be supplied by the target AWS account rather than hard-coded in the repository.

The default hosted model is `meta/llama-3.1-8b-instruct`, selected for responsive structured filter extraction through NVIDIA NIM. The model is configurable through `NVIDIA_MODEL` without changing application code.

The public Sites build exposes a same-origin `/api/refine` server route, so the NVIDIA key remains server-side and the browser never receives it. When that route or NVIDIA is unavailable, the client automatically falls back to the deterministic parser.
