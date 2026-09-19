# Relay frontend

The customer interface has three screens: policy review, approval inbox and decision log. It is presented as a Viseca feature powered by Relay and is structured as an independently deployable module for later integration into the Viseca one app. It starts in offline mock mode, so it can be demonstrated before the backend web API is ready.

## Run locally

```text
npm install
npm run dev
```

Use `VITE_USE_MOCK_API=false` to connect to the backend. `VITE_API_BASE_URL` may be left empty when Vite proxies a local backend on port 8000, or set to the deployed backend origin.

## Backend contract

The frontend calls these routes through `src/api.ts`:

- `POST /api/policy/compile`
- `POST /api/policy/draft`, then `POST /api/policy/confirm`
- `PATCH` and `DELETE /api/policy`
- `POST /api/run/start`
- `GET /api/status`, `/api/decisions` and `/api/pending`
- `POST /api/resolve/{authorization_id}`
- `GET /api/stream` as a server-sent event stream

The TypeScript wire types are in `src/types.ts`. The decisions and pending routes return backend decision records; the adapter exposes their nested `DecisionTrace` values to the screens and uses `human_deadline_at` for the approval countdown. The event stream uses named `status`, `decision`, `resolution`, `run`, `mandate` and `reset` events. The frontend handles the first three directly and reloads authoritative inbox/log data whenever the stream reconnects. Repeated records are upserted by live authorization ID.

The browser talks only to this REST/SSE boundary. It contains no Viseca team key, direct Viseca API calls, policy engine or purchase-decision logic.

See `DEMO.md` for the safe offline rehearsal, coordinated live-run checklist and recovery steps.

## Checks

```text
npm test
npm run build
```
