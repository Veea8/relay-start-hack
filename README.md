# START Hack Tour St. Gallen 2026

24 hour hackathon on finance and AI, 18 and 19 September 2026. Case and stack decided on Friday evening.

Case. Viseca "Agent on a Leash". We build the wallet control layer. Team working documents, including the implementation plan, are in [internal/](internal/).

## Team

- Vanessa Burckhardt (ETH Zürich)
- Andrés Gallardo (University of St. Gallen)
- Jonas Lüthi (ETH Zürich)
- Viktor Vantsev (University of St. Gallen)

## Folder map

```text
backend/             Core logic and the API.
frontend/            User interface.
tests/               Automated tests.
scripts/             Pipeline and one-off scripts.
docs/                Architecture notes and README images.
exploratory/<name>/  Your own scratch work. One folder per person.
outputs/             Generated figures and tables.
pitch/               Slides.
submission/          Thumbnail and deck. The video and the archive go to the Hack App.
internal/            Team working documents. Removed before the repository goes public.
```

`data/` is tracked in full. `data/raw/` holds the synthetic case data published by Viseca, copied unchanged from github.com/START-Hack/viseca-2026. `data/processed/` holds anything we derive from it.

Local only, gitignored. `admin/` for paperwork, `context/` for notes.
