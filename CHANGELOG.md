# Changelog

All notable changes to these skills are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.2.4] — 2026-11-14 — Docs: README quality pass

### Docs
- README (English and 繁體中文): added a Requirements & cost paragraph, a limitations bullet, a link to the blog post, and the support line; the footer is now a `## Support 支持` section.
- Added `SECURITY.md` and `CITATION.cff`.
- No change to the skills or scripts.

- README（英文與繁體中文）：新增「需求與費用」、限制說明、部落格文章連結與支持連結；頁尾改為 `## Support 支持`。
- 新增 `SECURITY.md`、`CITATION.cff`。
- skill 與腳本沒有變動。


## [0.2.3] — 2026-08-22

### Changed
- **Full-text acquisition: the downloader's exit codes now distinguish "no full text" from
  "your session died"** (`paper-review/fulltext-acquisition.md`, shared by `/paper-review` and
  `/paper-digest`). paper-fetch v1.5.0 splits the old catch-all `2` into `2` (a route ran and
  came back empty — the only code that is evidence about the paper), `3` (auth failed / session
  expired) and `6` (no route for that publisher). An expired session fails each paper
  separately, and each failure reads like "this paper has no route": one batch recorded nine
  papers as paywalled when a single automatic login fetched all nine. The reference now says to
  check the session before a batch and abort the batch if it is dead, and the manual
  link-resolver step is gated on exit `2` alone.
- **Pass `--title` to the downloader.** A `%PDF` check cannot tell an article from the whole
  supplement it sits in — conference abstracts carry the supplement's DOI, so every route
  honestly returns the entire proceedings volume (20% of the successful downloads in one
  49-paper batch, including a 563-page file recorded as fine). With a title the downloader
  verifies the article is in the file and cuts it out. Reading the wrong document produces a
  confident digest of somebody else's study — worse than reporting no full text.
- `config.example.yaml`: the `library_script` example path follows the reference
  implementation's rename (`skills/paper-download` → `skills/paper-fetch`) and documents the
  `--title` argument.

## [0.2.2] — 2026-07-14

### Fixed
- **`secrets.backend` is now actually honoured** (`paper-review/elsevier_fulltext.py`).
  `SETUP.md` and `config.example.yaml` documented `env` as the cross-platform default, but the
  script resolved keys through the Windows DPAPI store only — it never read `os.environ` and never
  looked at `secrets.backend` at all. A user on macOS/Linux (or on Windows without
  `~/.secrets/secret.ps1`) who exported `ELSEVIER_TDM_KEY` per the docs got a silent
  "Elsevier full text unavailable", with nothing pointing at the backend as the cause.
  `get_secret()` now dispatches on the backend — `env`, `dpapi`, `none`, `auto` (env, then dpapi) —
  resolved in the order `--backend` flag > `$SECRETS_BACKEND` > `config.yaml`'s `secrets.backend` >
  `env`. An unrecognised value falls back to `env` with a warning, so a typo can never silently
  reach DPAPI. Only gold-OA routes were unaffected. Reported by @liangRXdev ([#2]).
- **Scripts no longer crash on non-UTF-8 Windows consoles** (`paper-review/grade_judge.py`,
  `paper-review/argdown_lint.py`). The GRADE certainty labels (`⊕⊕◯◯`) and the linter's gap banner
  (`🔴 ⚠️ ✅`) raised `UnicodeEncodeError` under `cp950` (zh-TW), `gbk` (zh-CN), and `cp932` (ja-JP)
  — which meant the sanity check in `SETUP.md` §6 failed on first run for those users. Worse,
  `argdown_lint.py` signals through its exit code, so the crash (exit 1) was indistinguishable from
  "gap flagged" (exit 1). Both scripts now pin `stdout`/`stderr` to UTF-8 in `main()`, guarded for
  interpreters without `reconfigure`. `elsevier_fulltext.py` got the same guard.
  Reported by @liangRXdev ([#3]).

### Why
Both bugs are artefacts of extracting a public release from a private, Windows-only, zh-TW setup:
the config surface was written for everyone, but the code paths under it had only ever been
exercised on the author's machine. Verified under a simulated `cp950` console — `SETUP.md` §6 now
prints exactly what it promises — and the backend dispatch is covered for each of the four values,
the typo fallback, and precedence between flag, env var, and config.

[#2]: https://github.com/drpwchen/paper-review-and-digest/issues/2
[#3]: https://github.com/drpwchen/paper-review-and-digest/issues/3

## [0.2.1] — 2026-07-14

### Changed
- **Repository renamed** `claude-paper-tools` → **`paper-review-and-digest`**, so the name says what
  the two skills actually do instead of who built them. The old GitHub URL redirects permanently, so
  existing clones, links, and stars keep working; no code, config key, or skill name changed.
- Cross-link lines in this repo, `paper-radar`, and `paper-fetch` updated to the new name.

## [0.2.0] — 2026-07-10

### Changed
- **Full-text acquisition ladder reordered** (`paper-review/fulltext-acquisition.md`, the shared
  source of truth for both skills). An **automated institutional downloader** is now the primary
  route for paywalled-but-subscribed papers (new config key `fulltext.library_script`; reference
  implementation: [paper-fetch](https://github.com/drpwchen/paper-fetch)). The manual SFX /
  link-resolver route is demoted to **last resort**, and explicitly flagged as an interactive
  wall an agent cannot pass.
- Documented the downloader's exit codes and, importantly, that **`4` (busy) and `5` (watchdog)
  mean "retry serially" — not "no full text"**. Conflating contention with absence is the easiest
  way for a batch run to wrongly mark papers unobtainable.
- Agents are now told **not to drive a browser themselves** when a batch driver has already
  pre-fetched full text, and to **close any browser session they open**.

### Added
- Warning that Unpaywall's `is_oa: true` does not guarantee a PDF exists — hybrid and
  ahead-of-print articles routinely report OA while offering no usable `url_for_pdf`.
- Cross-links to the full three-repo pipeline (paper-radar → paper-fetch → claude-paper-tools).

### Why
A 12-paper batch run on 2026-07-10 exposed the old ladder's failure mode: agents skipped straight
past the automated downloader (it wasn't in the ladder at all), hit the resolver's login wall, and
each independently concluded "no full text" — for papers whose PDFs were one serial fetch away.
Agents that *did* reach for the downloader ran it concurrently and deadlocked on its exclusive
browser profile. Both failure modes are now designed out.

## [0.1.0] — 2026-07-09

Initial public release: `/paper-review` (journal-club appraisal with a deterministic GRADE
judge and a CrossRef reference-existence gate) and `/paper-digest` (fast content absorption
with self-test review cards), sharing one config and one full-text acquisition reference.
