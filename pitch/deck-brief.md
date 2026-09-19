# Prompt for Claude to build the Relay pitch deck

Copy everything below the line into Claude and ask for the artifact. Refresh the
figures marked REFRESH before the pitch, because they change as guards are built.

---

Build me a presentation deck as a single self-contained HTML artifact. It is for a
six-minute startup-style pitch to a jury at a hackathon, followed by seven minutes of
questions. The deck supports a live software demo; it does not replace it. Keep it to
the slide list below and no more.

## Technical requirements for the artifact

- One HTML file, 16:9 slides, one slide visible at a time, arrow keys and space to move,
  and a slide counter in a corner.
- Readable from the back of a room: body text no smaller than 22px equivalent, headlines
  large, never more than about 30 words on a slide.
- It must also survive print-to-PDF at 16:9, because the PDF is a submission deliverable.
  Give each slide a page break and avoid anything that only works on hover.
- Self-contained: no external scripts, stylesheets, fonts or images. Inline SVG for
  diagrams and icons. If you want Inter, link Google Fonts and give a full system-font
  fallback stack.
- Leave a `<!-- SLIDE: name -->` comment above each slide so we can find and edit them.

## Who we are and what we built

Team Relay, four students from ETH Zürich and the University of St. Gallen:
Vanessa Burckhardt, Andrés Gallardo, Jonas Lüthi, Viktor Vantsev.

We built **Relay**, a wallet control layer for the Viseca challenge "Agent on a Leash".

The problem in plain words. AI shopping assistants can now pay with your credit card —
Visa and Mastercard have shipped the capability. You tell your assistant "buy black
running shoes for up to CHF 200" and it goes and pays. The only thing a customer has
today to stay in control is a spending limit. A spending limit sees the price. It does
not see the wrong shoe size, the seller with a name one letter off a real one, the
non-returnable final sale, the extra item nobody asked for, the same order placed twice,
or a shop that writes "the customer pre-authorised CHF 900" into its own product text
hoping the assistant reads it as an instruction.

Relay sits between the assistant and the payment. For every purchase the assistant
proposes, Relay answers one of three things: **approve**, **decline**, or **ask the
customer**. The customer writes the rules in their own words, reviews exactly what Relay
understood, and can tighten or revoke them at any time.

Our slogan, use it as the spine of the deck: **"A spending limit sees the price. Relay
sees the purchase."**

## Tone and visual direction

This is a bank, money, and transactions. The team's own brief to itself was: stable,
consistent, rather conservative, but not so conservative that we lose on innovation, and
able to explain every choice so we come across as transparent and trustworthy.

So: calm, precise, financial-grade. Generous whitespace. No gradients-as-decoration, no
stock photography, no playful illustration, no emoji. Data and diagrams carry the visual
interest. It should look like it was made by the product team of a Swiss card issuer.

Match the product UI, which uses this palette:

- Deep navy `#07152e` (headers, dark slides), softer navy `#102548`
- Ink `#15223a` for body text, muted `#68758b` for secondary text
- Page background `#f4f7fb`, panels white, hairline borders `#dce3ed`
- Action blue `#1769e0`, darker `#0d53bc`
- Approve green `#167454` on `#e7f6ef`
- Ask/step-up amber `#a45a08` on `#fff4dd`
- Decline red `#b72c2c` on `#fdecec`
- Soft shadow `0 12px 36px rgba(18, 36, 65, 0.07)`

Use the three decision colours consistently and only for decisions: green approve, amber
ask, red decline. Those three colours are the visual through-line of the whole deck.

Inter or a system sans. Tight letter-spacing on headlines. Tabular figures for numbers.

## How we want blanks handled

Several slides are ours to write. For each of those, render a clearly visible placeholder
block — dashed amber border, small "TO FILL IN" label, and the guidance text I give you
set inside it in muted type — so we can see at a glance what is still open and replace it
by editing one obvious chunk of HTML. Do not write our words for us on those slides, and
do not quietly leave them blank either.

## Slide list

**1. Title.**
"Relay" as the product name, the slogan underneath, the four team names, and the challenge
name "Viseca · Agent on a Leash". Leave a small empty slot bottom-right where we will drop
the Viseca and START Hack logos ourselves — mark it, do not draw a fake logo.

**2. Hook and problem. TO FILL IN.**
Placeholder with this guidance inside it: "30 seconds. One customer story, two sentences,
told out loud. Our working version: Anna asks her agent to buy a monitor for at most CHF
400. The shop writes into its own product text that she pre-authorised CHF 900. Then:
agents can pay today, and a spending limit is all a customer has."
Below the placeholder, and this part you do design fully, put one quiet line of context we
are happy to show: the four questions the challenge asks, as four short items —
*Doesn't spend too much? Doesn't buy from shady merchants? Buys what I actually intended?
Resists prompt injection?* Make it clear a spending limit only answers the first.

**3. Demo.**
A holding slide that stays up for three minutes while we drive the live app. It must be
useful to a judge glancing up from the screen, so put the three moments we will show, as a
numbered list with the decision colour beside each:
1. An ordinary purchase, approved, no friction. (green)
2. A manipulated purchase — the shop text tries to raise the limit — Relay judges it on
   the facts and asks or declines. (amber/red)
3. The human path: the customer answers the question, and can tighten or revoke the policy
   at any time. (amber then red)
Add one line at the bottom: "Live, against Viseca's sandbox API." Keep this slide visually
quiet — the screen behind us is the star.

**4. Backup demo slide.**
Same three moments, but built to hold four screenshots we will paste in (policy screen,
approval inbox, decision log expanded on a trace, and one spare). Draw labelled empty
image frames with captions we can edit. This is our insurance if the network or the API
dies on stage.

**5. How it works.**
One diagram, the centrepiece of the deck. Draw it as inline SVG, clean and boxy, in the
palette above. It shows:
- The customer, with two separate arrows leaving them: a *shopping request* going to the
  AI shopping agent, and a *wallet policy* going to Relay. These are two different things
  and the separation is the whole point — the agent can never touch the policy.
- The AI shopping agent, greyed out and labelled "not ours — simulated", proposing a
  transaction to Relay.
- Payment context (card history, familiar merchants, device, session) feeding Relay.
- Relay itself, split into the two halves Viseca asked for in their technical preferences,
  using their words: **customer side** (the interface: write a policy, review checks,
  answer questions, revoke) and **engine side** (the decision, in the backend, under a
  hard deadline).
- Out of the engine: three arrows, green approve, red decline, amber ask-the-customer,
  and the amber one loops back to the customer and then returns as a final outcome.
Under the diagram, three short facts:
- The engine runs **23 checks in 5 families**: Spending limits · Item and terms · Seller ·
  Session · Repeats and manipulation.
- Every check records what it looked at, what it compared it to, and how long it took, so
  every decision can be read afterwards line by line.
- **Severity can only rise.** No check can soften another's verdict, and a check that
  errors never approves. Shop-provided text is treated as untrusted data and can never
  loosen a decision.

**6. Metrics.**
The proof slide. We ran the same 45 synthetic purchases through three setups. Two columns,
because blocking too much is also a failure — say that on the slide.

| Setup | Unwanted purchases stopped or questioned | Ordinary purchases wrongly blocked |
|---|---|---|
| No control at all | 0 of ~30 | 0 |
| A plain spending limit, roughly what a card offers today | 6 of ~30, every one of them a price breach | 0 |
| Relay | REFRESH — final number from the last replay run | must be 0 or close to it |

Supporting figures, shown small and precisely, all REFRESH before the pitch:
- No control: 45 approvals, CHF 8,925.73 approved.
- Plain limit: 6 declines, CHF 1,726 stopped.
- Relay as of the last measured run: 35 approvals, 5 questions, 5 declines, CHF 6,559.73
  approved.
- Decision deadline is 8 seconds; individual checks run in fractions of a millisecond;
  show the measured margin, REFRESH.
- Test suite: 651 backend tests, 6 interface tests, REFRESH.

Two honesty rules, and please build them into the slide rather than leaving them to us:
print the words **"on this synthetic test set"** near the table, and show **counts, never
percentages** — the data pack is deliberately tricky and real life has far fewer unwanted
purchases. One line naming what a plain limit misses: wrong size, final sale, lookalike
seller, unrequested add-ons, duplicate order, night burst, and an injected instruction
with a perfectly clean price.

**7. Business case.**
Why a card issuer would pay for this. Every purchase ends in one of four outcomes, each
with a value to the issuer — show this as a 2×2 or four-row block:
- Ordinary purchase approved → earns the transaction fee.
- Ordinary purchase wrongly blocked → loses the fee, and some customers move their agent
  to another card.
- Unwanted purchase approved → some become disputes; each costs handling time and
  sometimes the amount itself.
- Unwanted purchase stopped or questioned → that cost is avoided.
Then the headline, as a big pull-quote with the number left blank for us:
"Per 1,000 agent purchases, Relay is worth about ___ francs more than a plain spending
limit." REFRESH.
Beside it, small and explicit, the five inputs behind that number, labelled **assumptions,
to be replaced by Viseca's own figures**: fee rate; share of unwanted purchases that end
in a dispute; cost of handling one dispute; share of a disputed amount the issuer carries;
cost of a wrongly blocked purchase beyond the lost fee.
Close the slide with the adoption path in three steps: configuration lives in the existing
Viseca **one** app; the engine is a small stateless service behind one JSON contract, so
it drops into a bank runtime; and the strongest argument for why this belongs to the
issuer and not to the agent — **only the issuer can know that no customer has ever bought
from this seller before.** The agent cannot see that. The shop will not tell you.

**8. Stack and the model.**
Why we built it the way we did. Two halves.
Left — **the engine decides, deterministically**: Python, FastAPI, SQLite, an append-only
audit log, a fixed decision-record schema, every threshold in one settings file. Rules
decide, so the same purchase always gets the same answer and we can explain every one of
them.
Right — **the model assists, and never spends**: a small, low-latency model reads the
customer's sentence into proposed rules and pulls product facts out of shop text. It is on
a 2.5-second budget behind a circuit breaker; if it is slow or down, the breaker opens and
decisions continue on rules alone. A timeout asks the customer and never approves.
Under both, four claims with their proof attached — render each as claim + evidence:
- **Enterprise ready** — interface and engine are separate programs behind one JSON
  contract, exactly the split Viseca asked for. Append-only audit log. Every purchase
  recorded exactly once, even when the platform delivers it twice.
- **Zero trust** — shop text never reaches anything that decides; the injected sentence is
  quoted back to the customer as text that had no effect.
- **Reliability** — we can cut the model mid-run and decisions continue unchanged.
- **Ethical AI, Swiss data protection** — the customer's own words go to a Swiss-hosted
  open model; the customer confirms every rule before it counts and can revoke at any
  moment.
Add one line we are proud of: **nothing is hard-coded to the test data.** Scramble every
scenario name, purchase identifier and position in the sequence and the 45 decisions come
out identical.

**9 and 10. Two free slides. TO FILL IN.**
Two empty slides in the deck's own style, each with a headline slot, a subheadline slot,
and a flexible body area, so we can drop in whatever the last hours produce. Give one a
two-column layout and the other a single centred statement layout. Placeholder guidance:
"Spare — e.g. the preference check-in concept, a second metric, or a screenshot."

**11. Close. TO FILL IN.**
Placeholder with this guidance: "15 seconds. Product name, slogan, thank you, and the one
sentence we want left in the room." Design the slide properly — big, quiet, the slogan set
large — but leave the closing sentence itself to us.

**12. Appendix, after the close, for the seven minutes of questions.**
A compact reference slide, denser type is fine here, that we can jump to. Eight questions
with one-line answers:
- *What if the model is down?* Decisions continue on rules alone; unclear cases ask the
  customer; a timeout never approves.
- *How does it scale?* Small stateless service, one JSON contract, separate from the
  interface; every decision records its margin before the deadline.
- *How is customer data protected?* The customer's own words go only to a Swiss-hosted
  model; the cross-customer signal uses counts only.
- *How do we know nothing is hard-coded?* Scramble the names, identifiers and order — same
  45 decisions.
- *Does it block too much?* Familiarity, country and device never decline on their own, and
  a single behaviour signal alone passes.
- *What if nobody answers a question?* The purchase stays unapproved. No money moves.
- *Why does this belong with the issuer?* Only the issuer sees across customers, and only
  the issuer can stop a payment whatever the agent does.
- *What did we not solve?* Revoking while a purchase is already pending; the usual item
  size is learned within a run only; the thresholds rest on a small synthetic data pack.

## Rules for you

- Use only the facts and figures on this page. Invent nothing — no made-up market sizes,
  no growth rates, no customer quotes, no percentages that are not here.
- Every figure marked REFRESH must be visually flagged in the HTML — a small amber dot or
  a comment right next to it — so we cannot ship a stale number by accident.
- Never state an assumption as a measured fact. Where the slide shows the money model, the
  word "assumptions" must be visible on the slide itself.
- Keep the whole deck to the twelve slides above.
