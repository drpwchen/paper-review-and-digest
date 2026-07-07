# SETUP — paper-review + paper-digest

These two Claude Code skills share one `config.yaml`. This is a one-time setup. Nothing here
phones home; every private integration is optional and off unless you fill it in.

## 1. Install

Drop both skill folders into your Claude Code skills directory:

```
~/.claude/skills/paper-review/    # this folder — holds the shared config + scripts
~/.claude/skills/paper-digest/    # reads paper-review/config.yaml
```

## 2. Create your config

```bash
cd ~/.claude/skills/paper-review
cp config.example.yaml config.yaml
```

Edit `config.yaml`. Every key is documented inline in `config.example.yaml`. Keep `config.yaml`
out of any public repo (it holds your paths) — add it to `.gitignore`.

## 3. What each integration needs (all optional)

| Feature | Config key | Needs |
|---|---|---|
| Write notes to your vault | `vault.*` | An Obsidian vault (or any folder). Set the four paths + your daily-note heading. |
| Self-test review cards | `review_site.push_script` + `.url` | A script that ingests a cards JSON. **Leave blank to disable** — the digest note is still written, cards are just skipped. The author's pushes to a Cloudflare D1 review site; yours can be anything or nothing. |
| Zotero full-text | `fulltext.zotero_local_api` | Zotero running with the local API (+ Better BibTeX for citekeys). `false` skips it. |
| Elsevier / ScienceDirect full text | `fulltext.elsevier_script` + `secrets.backend` | An Elsevier TDM API key. Store it via your secrets backend (see below). No key → route is skipped. |
| Institutional subscribed full text | `fulltext.sfx_base` | Your library's OpenURL/SFX base URL with `{DOI}` placeholder. Blank → skipped. |
| Reimbursement/coverage lookups | `persona.reimbursement_system` | Optional. Blank → the review skips coverage bullets entirely. |

Always-on, no setup: Semantic Scholar + PubMed + CrossRef + Open-Access auto-fetch, and the two
bundled scripts (`grade_judge.py`, `argdown_lint.py`) which are pure stdlib.

## 4. Secrets backend (`secrets.backend`)

Controls how bundled scripts read API keys (Elsevier TDM, and your card-push script's token):

- `env` — plain environment variables (`ELSEVIER_TDM_KEY`, etc.). Simplest, cross-platform.
- `dpapi` — Windows DPAPI store via `~/.secrets/secret.ps1` (the author's setup).
- `none` — no secret-backed routes; Elsevier TDM and any token-gated card push are disabled.

Claude is instructed never to read or print these keys.

## 5. Write your persona

`persona` in `config.yaml` is the one block you should hand-write. It sets the output language,
your clinical specialty (drives which RoB tool + which MCID scales are relevant), your audience,
and your locale (drives external-validity and coverage checks). The author's is a Taiwan PMR
physician writing 繁體中文; replace it with yours.

## 6. Sanity check

```bash
cd ~/.claude/skills/paper-review
echo '{"starting_level":"high","domains":[{"name":"risk_of_bias","rating":"serious"},{"name":"inconsistency","rating":"not_serious"},{"name":"indirectness","rating":"not_serious"},{"name":"imprecision","rating":"serious"},{"name":"publication_bias","rating":"not_serious"}]}' | python grade_judge.py -
# expect: FINAL CERTAINTY: Low  (High −2)

echo '{"claim":"Drug lowers fractures","claim_type":"hard_endpoint","premises":[{"id":"P1","type":"surrogate_outcome"}]}' | python argdown_lint.py - ; echo "exit=$?"
# expect: 1 gap flagged, exit=1
```

If both print as described, you're set. Then in Claude Code: `/paper-review <DOI>` or `/paper-digest <DOI>`.
