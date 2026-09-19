# START Hack Tour St. Gallen 2026

24 hour hackathon on finance and AI, 18 and 19 September 2026.

Case. Viseca "Agent on a Leash". We build the wallet control layer: a shopping agent proposes purchases, Relay answers each one with approve, decline or a question to the customer, inside the platform's deadline, with every check written down. Team working documents, including the implementation plan and the web API contract, are in [internal/](internal/).

## Team

- Vanessa Burckhardt (ETH Zürich)
- Andrés Gallardo (University of St. Gallen)
- Jonas Lüthi (ETH Zürich)
- Viktor Vantsev (University of St. Gallen)

## Quick start

You need Python 3.12 or newer and Node 20 or newer. Every command runs from the repository root. On Windows the interpreter is `backend\.venv\Scripts\python` instead of `backend/.venv/bin/python`.

One-time setup:

```text
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.lock.txt
(cd frontend && npm install)
cp backend/.env.example backend/.env        # fill in the keys only for live mode or the model
```

Start the app:

```text
scripts/dev.sh                     # offline mode, keeps the decisions from earlier runs
scripts/dev.sh offline --fresh     # offline mode with an empty log and inbox
scripts/dev.sh stop                # stops the backend and the interface
```

The script stops whatever still runs on the two ports, starts the backend on `http://127.0.0.1:8000` and the interface on `http://localhost:5173`, prints which platform the backend talks to, and writes its logs to `outputs/logs/`. `--fresh` moves the old store to `outputs/state/backup-<time>/` rather than deleting it.

Starting by hand, in two terminals, does the same thing:

```text
LEASH_MODE=offline backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --port 8000 --reload
(cd frontend && VITE_USE_MOCK_API=false npm run dev)
```

`http://localhost:8000/docs` lists every endpoint of the backend. Without `VITE_USE_MOCK_API=false` the interface runs on static prototype data and never calls the backend.

## Offline or live

The backend talks to one of two platforms, chosen when it starts. The banner at the top of the interface shows which one.

| Mode | Where the purchases come from | Needs | Costs |
|---|---|---|---|
| `offline` (blue banner) | A copy of Viseca's platform inside the backend, serving the 45 public purchases | Nothing | Nothing. Rehearse here as often as you like |
| `live` (red banner) | Viseca's server at `https://leash-api-production.up.railway.app` | `TEAM_API_KEY` in `backend/.env` | One of the team's 300 runs per scenario start, at most 3 runs open at once |

Switching means restarting the backend in the other mode: `scripts/dev.sh live` or `scripts/dev.sh offline`. The script asks for a typed `live` before it starts live mode, and refuses without the key. By hand, set `LEASH_MODE` in `backend/.env` or in the environment, where the environment wins over the file. Note that `backend/.env.example`, and so a fresh copy of it, says `LEASH_MODE=live`, which is why the script always passes the mode explicitly. Both modes use the same endpoints, the same engine and the same screens, so what works offline works live. A restart in offline mode forgets the confirmed policy, because the platform copy lives inside the backend, so confirm it again before the next run.

For the demo, rehearse offline and use live only for runs the team agreed on. Viseca judges the latest completed run of each scenario, so a stray live run can replace a clean one. One designated operator starts live runs after a line in the team chat, and in live mode the start button stays disabled until the coordination box is ticked. `frontend/DEMO.md` has the operator checklist, and `internal/live-runs-runbook.md` the procedure for the judged runs with the expected result of each scenario and the answer to give to every question. When the inbox cannot send an answer, `scripts/live_pending.py` lists the open questions with the runbook's answer and sends one with `--resolve <id> approve|decline`.

To run whole scenarios the way the runbook says, `backend/.venv/bin/python scripts/judged_runs.py --scenario SCEN0001` confirms the scenario's instruction, starts the run, answers every question with the runbook's answer as it arrives, waits for the run to complete and writes a report to `outputs/live/`. Without `--scenario` it runs all five in order. It refuses a backend in live mode unless `--live` is given, because every scenario start is one of the team's runs.

## Using the app

The interface has three screens. The usual order is policy, run, inbox, log.

1. **Wallet policy.** Write the customer's instruction in plain words, then press **Build policy**. The compiler turns it into checks, split into the rules stored with the platform and the checks the engine enforces on top, and lists under "When Relay will ask" anything it read with doubt. Press **Confirm policy** to store it on the platform as the active mandate.
2. **Start a run.** Once a policy is active, pick a scenario under "Demo control" and press **Start offline run** (or **Start live run**). The backend polls the platform, decides every purchase of the scenario within its 8 second deadline, and the interface jumps to the inbox.
3. **Approval inbox.** Every purchase the engine answered with a question appears as a card with the one sentence the customer reads, the trust score and the reason. Press **Approve once** or **Decline** within the 120 second window. An unanswered question expires and counts as not approved. When an approval you gave meanwhile means this one would break the budget, the card says so, and you can still approve it, because the customer always decides.
4. **Decision log.** Every purchase with its decision, its trust score and the five guard families. Expand a row for the evidence of each guard, the deadline margin and the calculation of the score.
5. **Tighten** moves uncertain purchases to decline and **Revoke** withdraws the mandate. Both go to the platform, and neither can loosen anything.

The public scenarios come with a reference instruction each. Use it as the policy for that scenario, because an instruction that does not fit the scenario turns every purchase into a decline and leaves the inbox empty.

| Scenario | Instruction to type | Purchases |
|---|---|---|
| SCEN0000 Connection check | Buy one ordinary grocery item for CHF 20 or less from a shop I use regularly. Ask me when uncertain. | 1 |
| SCEN0001 Household budget | Order our household groceries for delivery. Keep each order at or below CHF 120 including delivery, and keep the total across any seven days at or below CHF 300. Ask me when uncertain. | 10 |
| SCEN0002 Requested item and order terms | Replace my worn road-running shoes in size 43. Buy only from a specialist sports retailer, only if the order can be returned within 14 days or more, and pay no more than CHF 200. Ask me when uncertain. | 12 |
| SCEN0003 Session integrity | The agent may buy clothing for me, up to CHF 250 per order, from shops I have used before. Pause anything that looks like someone other than me is driving the session. Ask me when uncertain. | 11 |
| SCEN0004 Manipulated agent | Buy the 27-inch monitor I chose, from a seller I have bought from before, for CHF 400 or less. Do not add anything I did not ask for. Ask me when uncertain. | 11 |

With these instructions the engine currently approves 17 of the 45 purchases, declines 15 and asks about 13, matching the reference decision on all 45. The answer the reference expects from the customer for each question is in `data/processed/purchase_verdicts.csv` under `assumed_customer_answer`.

A confirmed mandate applies to every run started afterwards. To demo another scenario, go back to the policy screen, build and confirm its instruction, then start that scenario.

## Checks

```text
backend/.venv/bin/python -m pytest -q                        # the backend, 1382 tests
backend/.venv/bin/python scripts/replay.py --all --compare    # all 45 purchases offline, compared with the reference decisions
(cd frontend && npm test && npm run build)                    # the interface tests and the TypeScript check
```

The tests and the replay need no key and no `.env` file. The replay writes a table and one record per purchase into `outputs/replay/`.

## Where things are written

- `outputs/state/relay.sqlite3` is the decision store of the backend, gitignored. `scripts/dev.sh offline --fresh` sets it aside for an empty start.
- `outputs/audit/run_<id>.jsonl` is the append-only audit file of a live run. Offline runs write under `outputs/audit/offline/`, gitignored.
- `outputs/replay/` holds the replay tables, `outputs/trust/` the trust score reports, `outputs/logs/` the logs of `scripts/dev.sh`.

## Folder map

```text
backend/             Core logic and the API.
frontend/            User interface.
tests/               Automated tests.
scripts/             Pipeline and one-off scripts.
docs/                Architecture notes and README images.
exploratory/<name>/  Your own scratch work. One folder per person.
outputs/             Generated output. Replay tables in replay/, decision traces in audit/.
pitch/               Slides.
submission/          Thumbnail and deck. The video and the archive go to the Hack App.
internal/            Team working documents. Removed before the repository goes public.
```

`data/` is tracked in full. `data/raw/` holds the synthetic case data published by Viseca, copied unchanged from github.com/START-Hack/viseca-2026. `data/processed/` holds anything we derive from it.

Local only, gitignored. `admin/` for paperwork, `context/` for notes.
