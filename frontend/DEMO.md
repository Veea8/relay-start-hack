# Frontend demo operator guide

## Safe rehearsal

1. Start the backend with `LEASH_MODE=offline` and confirm `GET /api/status` says `"leash_mode": "offline"`.
2. Start the frontend with `VITE_USE_MOCK_API=false npm run dev`.
3. Confirm the blue banner says **OFFLINE SIMULATOR** before starting a scenario. Offline rehearsals consume no team runs.
4. Confirm a policy, start `SCEN0001`, and let the interface return to the approval inbox.
5. Answer each question within the visible 120-second window using `assumed_customer_answer` in `data/processed/purchase_verdicts.csv`.
6. Open the decision log and expand a row to show its five guard families, evidence and deadline margin.

## Live judging run

Live runs share the team's 300-run quota, and only the latest completed run of each scenario counts. One designated operator coordinates every live run with the team.

Before pressing **Start live run**, verify all of these:

- The red banner says **LIVE TEAM ENVIRONMENT**.
- The guard owner has approved the engine version for the run.
- Another teammate is ready to answer the inbox for the entire scenario.
- No other teammate is starting a run.
- For the final judged run, nobody will run that scenario again afterward.

The live start button remains disabled until the operator checks the coordination acknowledgement.

## Recovery

- If the stream disconnects, keep the page open. It reconnects automatically and reloads the inbox and log.
- If the interface cannot resolve a purchase, use the backend's documented `POST /api/resolve/{live_authorization_id}` fallback immediately.
- If the backend becomes unavailable, use **Try again** after it restarts. Existing records remain in the backend store.
- Never switch to live mode merely to diagnose the interface; reproduce the issue in offline mode.
