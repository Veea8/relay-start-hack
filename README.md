# Relay, a wallet control layer for AI shopping agents

Built in 24 hours at the START Hack Tour St. Gallen 2026 (18 and 19 September 2026), for Viseca's case "Agent on a Leash".

AI shopping agents can pay with a customer's card, and today the cardholder's only control is a spending limit. A limit sees the price. It does not see the wrong item, the imitated seller or the shop text written to manipulate the agent.

Relay sits between the agent and the card. The customer states a policy in plain words, Relay turns it into rules the customer confirms, and from then on Relay answers every purchase the agent proposes with **approve**, **decline** or **a question to the customer**, inside the platform's 8 second deadline, with the evidence for every check written down.

![The approval inbox, with two purchases waiting for the customer](outputs/trust/screen_inbox_20260919.png)

## Results

On Viseca's five public scenarios, 45 purchases in total:

- Relay matches the reference decision on **all 45 purchases**.
- It stops or questions **28 of 28 risky purchases**, where a plain spending limit catches 6.
- It approves **17 of 17 ordinary purchases** without asking the customer anything.
- It keeps CHF 5,899 of risky spend from going through unchecked, against CHF 1,726 for a plain limit.
- A decision takes under 2 ms of engine time, which leaves almost the whole 8 second deadline as margin.
- Tests replace every purchase and scenario identifier with random values and shift every date by weeks, and the 45 decisions stay the same, so nothing is hard-coded to the scenarios.

![Risky purchases stopped or put to the customer: no control 0 of 28, plain spending limit 6 of 28, Relay 28 of 28](outputs/pitch/02_risky_purchases_caught.png)

These figures describe this test set of 45 purchases and are no forecast of a real-world rate. The tables behind them are in [outputs/pitch/](outputs/pitch/) and [outputs/replay/business_impact.md](outputs/replay/business_impact.md).

## How it works

- **Policy compiler.** Fixed readers turn the customer's instruction into structured rules: per-order and period budgets, item and category scope, seller requirements, order terms. Anything read with doubt is listed as "When Relay will ask". A language model (Swisscom's Apertus, or any OpenAI-compatible model) can help with wording the readers do not cover, and it can only make a policy stricter.
- **Decision engine.** Every purchase runs through 18 guards in five families: spending limits, item and terms, seller, session, and repeats and manipulation. Examples are split orders that dodge a budget, lookalike seller names, a changed device or country mid-session, a repeated order, and text in four languages that tries to instruct the agent. No language model sits on the decision path, so decisions are deterministic and fast. A decision that runs out of time becomes a question, never an approval.
- **Trust score.** Every decision carries a score from 0 to 100 that starts at 100 and loses points for every finding, with each deduction listed. It has no learned weights and never replaces the decision. See [docs/trust-score.md](docs/trust-score.md).
- **Customer interface.** A React app with three screens: the wallet policy, an approval inbox with a 120 second answer window, and a decision log where every row expands to the evidence of each guard.

Stack: Python 3.12+, FastAPI, Pydantic and SQLite in the backend; React, TypeScript, Vite and Tailwind in the frontend; pytest and Vitest for tests.

## Team

- Vanessa Burckhardt (ETH Zürich): customer interface and its connection to the web API, the bounded language model integration
- Andrés Gallardo (University of St. Gallen): data analysis, the policy readers and the decision guards, replay and pitch figures
- Jonas Lüthi (ETH Zürich): platform client, worker loop, decision store and web API, trust score
- Viktor Vantsev (University of St. Gallen): business impact figures, security score, monthly preference check

## Running it locally

You need Python 3.12 or newer and Node 20 or newer. Every command runs from the repository root. On Windows the interpreter is `backend\.venv\Scripts\python` instead of `backend/.venv/bin/python`.

```text
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.lock.txt
(cd frontend && npm install)
cp backend/.env.example backend/.env
```

Then start the backend and the interface:

```text
scripts/dev.sh                     # offline mode, keeps the decisions from earlier runs
scripts/dev.sh offline --fresh     # offline mode with an empty log and inbox
scripts/dev.sh stop                # stops the backend and the interface
```

The backend runs on `http://127.0.0.1:8000` (endpoint list at `/docs`) and the interface on `http://localhost:5173`. Starting by hand, in two terminals, does the same thing:

```text
LEASH_MODE=offline backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --port 8000 --reload
(cd frontend && VITE_USE_MOCK_API=false npm run dev)
```

Offline mode serves the 45 public purchases from a copy of Viseca's platform inside the backend, and needs no key. Live mode talked to Viseca's sandbox server during the event and needs the team key, so it no longer works.

### A short demo

1. On **Wallet policy**, type an instruction from the table below, press **Build policy**, then **Confirm policy**.
2. Under "Demo control", pick the matching scenario and press **Start offline run**.
3. In the **Approval inbox**, answer each question with **Approve once** or **Decline**. The reference answer for each one is in `data/processed/purchase_verdicts.csv` under `assumed_customer_answer`.
4. In the **Decision log**, expand a row to see each guard's evidence, the deadline margin and the trust score calculation.

| Scenario | Instruction | Purchases |
|---|---|---|
| SCEN0001 Household budget | Order our household groceries for delivery. Keep each order at or below CHF 120 including delivery, and keep the total across any seven days at or below CHF 300. Ask me when uncertain. | 10 |
| SCEN0002 Requested item and order terms | Replace my worn road-running shoes in size 43. Buy only from a specialist sports retailer, only if the order can be returned within 14 days or more, and pay no more than CHF 200. Ask me when uncertain. | 12 |
| SCEN0003 Session integrity | The agent may buy clothing for me, up to CHF 250 per order, from shops I have used before. Pause anything that looks like someone other than me is driving the session. Ask me when uncertain. | 11 |
| SCEN0004 Manipulated agent | Buy the 27-inch monitor I chose, from a seller I have bought from before, for CHF 400 or less. Do not add anything I did not ask for. Ask me when uncertain. | 11 |

SCEN0000, the connection check, takes "Buy one ordinary grocery item for CHF 20 or less from a shop I use regularly. Ask me when uncertain." A confirmed policy applies to every run started afterwards, so build and confirm the matching instruction before each scenario.

## Checks

```text
backend/.venv/bin/python -m pytest -q                        # the backend tests
backend/.venv/bin/python scripts/replay.py --all --compare    # all 45 purchases offline, compared with the reference decisions
(cd frontend && npm test && npm run build)                    # the interface tests and the TypeScript check
```

None of them needs a key or a `.env` file. The replay writes a table and one record per purchase into `outputs/replay/`.

## Repository layout

```text
backend/             Policy compiler, decision engine, platform client, worker and web API.
frontend/            Customer interface.
tests/               Backend tests.
scripts/             Start script, replay, trust report, pitch figures and business impact.
docs/                The trust score method.
data/raw/            The synthetic case data published by Viseca.
data/processed/      Reference tables derived from it.
exploratory/         Data analysis scripts with their saved output.
outputs/             Replay tables, trust reports and pitch figures.
pitch/, submission/  Pitch brief and submission texts.
```

`data/raw/` is copied unchanged from [github.com/START-Hack/viseca-2026](https://github.com/START-Hack/viseca-2026). All customer, card and purchase data in it is synthetic.

## Note

This is a hackathon prototype. It was built for Viseca's challenge, and the interface uses Viseca's logo from the case material, but it is not a Viseca product and is not affiliated with or endorsed by Viseca.


