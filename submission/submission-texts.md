# Relay - Submission Texts and Video Script

## 1 - Title

The form allows 60 characters.

| | Title | Characters |
|---|---|---|
| Recommended | Relay - the wallet control layer for AI shopping agents | 55 |
| Alternative | Relay - who watches the AI that spends your money | 49 |
| Alternative | Relay - your AI agent shops, you stay in charge | 48 |
| Alternative | Relay | 5 |

## 2 - Slogan

The form allows 100 characters.

| | Slogan | Characters |
|---|---|---|
| Recommended | A spending limit sees the price. Relay sees the purchase. | 57 |
| Alternative | Your AI agent shops. Relay decides whether it may pay. | 54 |
| Alternative | 28 of 28 risky purchases stopped or questioned. 17 of 17 ordinary ones approved untouched. | 90 |
| Alternative | Approve, decline or ask the customer, with the evidence behind every decision. | 78 |

## 3 - Description

The form states no length, so this runs to 199 words.

AI shopping agents can pay with a customer's card. The cardholder's only control today is a spending limit, and a limit sees only the price. It misses the wrong item, the imitated seller and text aimed at the agent.

Relay is the wallet control layer between the agent and the card. The customer states the policy in plain words, and fixed readers turn it into rules the customer confirms. Apertus helps on the policy screen only, with wording the readers do not cover, and it can only make a policy stricter. For every purchase Relay answers approve, decline or ask the customer, from 18 checks in five families, inside 8 seconds, with no model on the decision path. Every decision carries a trust score and the evidence behind it. The customer stays responsible, so Relay asks when the call is theirs.

On Viseca's five public scenarios Relay matches all 45 reference decisions. It stops or questions 28 of 28 risky purchases where a plain spending limit catches 6, keeps CHF 5,899 of risky spend from going through unchecked against CHF 1,726, and approves 17 of 17 ordinary purchases without friction. A decision needs under 2 ms of engine time. All five scenarios have completed runs on Viseca's live server.

Next, the 30-day reconfirmation of the customer's preferences, built and tested as a state machine, gets wired in.

## 4 - Video script

120 seconds and 224 spoken words, which leaves room to breathe between scenes. Record the screen first and lay the voice over it. Anna is the name the voice gives the customer. If the screen shows another name, say "the customer" instead.

| Seconds | On screen | Spoken line | Words |
|---|---|---|---|
| 0 to 9 | Title card with the name Relay and the slogan, then a cut to the app | An AI agent can now pay with your card, and a spending limit is the only thing watching it. | 19 |
| 9 to 21 | Policy screen. The policy is typed in plain words, the compiled rules appear, the customer confirms | Relay sits between the agent and the card. Anna writes her rules in plain words, Relay turns them into a policy, and she confirms it. | 24 |
| 21 to 36 | Decision log. An ordinary purchase arrives and turns green. The row is expanded to show the checks and the trust gauge | An ordinary purchase comes in. All checks pass, Relay approves in milliseconds, and Anna is never interrupted. The decision still carries its trust score and its evidence. | 27 |
| 36 to 50 | The monitor purchase arrives. Zoom on the shop text with the claimed pre-authorization | Now the agent wants a monitor. Anna's limit is CHF 400, and the shop's text claims she pre-authorized CHF 900. | 20 |
| 50 to 66 | The decline card. The quoted sentence is highlighted, the gauge sits in the red band, the row is expanded to the list of deductions | Relay never takes instructions from shop text. It declines on the limit, quotes the planted sentence as text that had no effect, and lists every point the trust score lost. | 30 |
| 66 to 78 | The shoe purchase arrives. The inbox shows a question with the 120 second countdown | Next the agent finds the right shoes for CHF 215, against a limit of 200. A plain limit would throw the sale away. | 23 |
| 78 to 92 | The inbox card with the question. The cursor taps approve and the card resolves | Relay asks instead. CHF 15 above your limit, approve anyway? It is Anna's call, so she answers in the inbox with one tap. | 23 |
| 92 to 104 | Policy screen. A rule is tightened, then the policy is revoked and the screen shows the revoked state | She stays in control. She can tighten the policy at any time, or revoke the agent's permission to spend altogether. | 20 |
| 104 to 120 | Chart 02 full screen, the three bars with 0, 6 and 28 of 28. Hold the chart for the last three seconds | On Viseca's five public scenarios Relay matches all 45 reference decisions and approves 17 of 17 ordinary purchases without friction. A plain spending limit catches 6 of the 28 risky purchases. Relay stops or questions 28 of 28. | 38 |

## 5 - Likely judge questions

**What happens when a language model is unavailable?**
Nothing changes for a decision, because no model sits on the decision path. The policy is compiled by fixed readers, Apertus only helps with wording on the policy screen, and a decision that runs out of time becomes a question to the customer and never an approval.

**How do we know the decisions are not hard-coded to the scenarios?**
Our tests replace every purchase identifier and every scenario name with random values and shift every date by weeks, and the 45 decisions stay the same. Every decision follows from the customer's policy and the facts of the purchase.

**Does Relay block too much?**
It approves 17 of 17 ordinary purchases in the public scenarios without any friction. When a purchase is a judgment call, such as CHF 15 above the limit for the right shoes, Relay asks the customer and the sale survives.

**How does Relay handle text written to manipulate the agent?**
Shop text is treated as untrusted and can never loosen a decision. The planted sentence is quoted on the decision card as text that had no effect, so the customer sees the attempt.

**What is the trust score, and is it a model?**
It is a number from 0 to 100 that starts at 100 and loses points for every finding of the checks, with each deduction listed. It has no learned weights, it never replaces the decision, and it travels with the decision as evidence.

**Will it hold the 8 second deadline at scale?**
A decision needs under 2 ms of engine time, which leaves almost the whole deadline as margin. The engine is a separate service from the interface, as Viseca recommends, so each side can be deployed and scaled independently.

**Why does this belong with the card issuer, and how would it be adopted?**
Only the issuer can stop a payment whatever the agent does, and only the issuer sees signals across customers. The customer side fits into the existing one app, and the engine runs in the backend next to authorization.

**What is not finished?**
The 30-day reconfirmation of the customer's preferences is built and tested as a state machine and not yet wired in. The figures come from 45 purchases in five public scenarios, so they describe this test set and are no forecast of a real-world rate.
