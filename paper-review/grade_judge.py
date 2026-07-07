#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""grade_judge.py — deterministic GRADE certainty recompute.

The LLM (in /paper-review) rates the five GRADE downgrade domains and, for
observational bodies of evidence, the upgrade criteria. This script recomputes
the FINAL certainty deterministically from the starting level and the signed sum
of downgrades/upgrades. The model's own gut-call label is advisory only — the
value this script prints is the authoritative one written into the note.

Zero dependencies (stdlib only). Portable: no private paths, no secrets.

Ported from the deterministic core of htlin222/robust-lit-review's grade_judge.py
(compute_final_certainty) and generalized to a single-paper CLI.

Input JSON (file arg or stdin):
{
  "outcome": "pain reduction at 12 wk",          # optional label
  "starting_level": "high" | "low",              # RCT-dominant=high, observational=low
  "domains": [                                    # the 5 downgrade domains
    {"name": "risk_of_bias",     "rating": "not_serious|serious|very_serious", "justification": "..."},
    {"name": "inconsistency",    "rating": "not_serious", "justification": "..."},
    {"name": "indirectness",     "rating": "serious",     "justification": "..."},
    {"name": "imprecision",      "rating": "serious",     "justification": "..."},
    {"name": "publication_bias", "rating": "not_serious", "justification": "..."}
  ],
  "upgrades": [                                   # OBSERVATIONAL only, only if no downgrade applied
    {"name": "large_effect",  "points": 1, "justification": "RR 3.1"},
    {"name": "dose_response", "points": 1, "justification": "..."},
    {"name": "opposing_confounding", "points": 1, "justification": "residual confounding biases toward null"}
  ]
}

Usage:
    python grade_judge.py grade_input.json          # human-readable report
    cat grade_input.json | python grade_judge.py -   # read stdin
    python grade_judge.py grade_input.json --json    # machine-readable result

Exit code: 0 always (this is a calculator, not a gate). Warnings go to stderr.
"""
from __future__ import annotations

import argparse
import json
import sys

# GRADE certainty ladder, low index = lower certainty.
_LEVELS = ("very_low", "low", "moderate", "high")
_LEVEL_INDEX = {name: i for i, name in enumerate(_LEVELS)}
_LEVEL_LABEL = {
    "very_low": "Very low ⊕◯◯◯",
    "low": "Low ⊕⊕◯◯",
    "moderate": "Moderate ⊕⊕⊕◯",
    "high": "High ⊕⊕⊕⊕",
}

_RATING_DOWNGRADE = {
    "not_serious": 0,
    "serious": -1,
    "very_serious": -2,
}

_REQUIRED_DOMAINS = (
    "risk_of_bias",
    "inconsistency",
    "indirectness",
    "imprecision",
    "publication_bias",
)

_VALID_UPGRADES = ("large_effect", "dose_response", "opposing_confounding")


def compute_final_certainty(starting_level: str, total_change: int) -> str:
    """Map (starting level index + signed net change) to a clamped GRADE label."""
    start = _LEVEL_INDEX.get(starting_level.lower(), _LEVEL_INDEX["high"])
    idx = max(0, min(len(_LEVELS) - 1, start + total_change))
    return _LEVELS[idx]


def grade(data: dict) -> dict:
    warnings: list[str] = []

    start = str(data.get("starting_level", "")).lower()
    if start not in ("high", "low"):
        warnings.append(
            f"starting_level '{data.get('starting_level')}' invalid; "
            "defaulting to 'high' (RCT-dominant)."
        )
        start = "high"

    domains = data.get("domains", []) or []
    seen = {d.get("name") for d in domains}
    for req in _REQUIRED_DOMAINS:
        if req not in seen:
            warnings.append(f"domain '{req}' missing — treated as not_serious (0).")

    downgrade_sum = 0
    domain_rows = []
    for d in domains:
        name = d.get("name", "?")
        rating = str(d.get("rating", "not_serious")).lower()
        if rating not in _RATING_DOWNGRADE:
            warnings.append(f"domain '{name}' rating '{rating}' invalid — treated as not_serious.")
            rating = "not_serious"
        pts = _RATING_DOWNGRADE[rating]
        downgrade_sum += pts
        domain_rows.append((name, rating, pts, d.get("justification", "")))

    any_downgrade = downgrade_sum < 0

    # Upgrades: GRADE only permits them for observational evidence with NO downgrade.
    upgrades = data.get("upgrades", []) or []
    upgrade_sum = 0
    upgrade_rows = []
    for u in upgrades:
        name = u.get("name", "?")
        pts = int(u.get("points", 0) or 0)
        if name not in _VALID_UPGRADES:
            warnings.append(f"upgrade '{name}' not a recognized GRADE upgrade criterion — ignored.")
            continue
        if start != "low":
            warnings.append(
                f"upgrade '{name}' ignored — upgrades apply to observational (starting_level=low) evidence only."
            )
            continue
        if any_downgrade:
            warnings.append(
                f"upgrade '{name}' ignored — GRADE forbids upgrading when any domain is downgraded."
            )
            continue
        pts = max(0, min(2, pts))
        upgrade_sum += pts
        upgrade_rows.append((name, pts, u.get("justification", "")))

    total_change = downgrade_sum + upgrade_sum
    final = compute_final_certainty(start, total_change)

    llm_label = str(data.get("final_certainty", "")).lower().replace(" ", "_")
    if llm_label in _LEVEL_INDEX and llm_label != final:
        warnings.append(
            f"model's self-reported final_certainty '{llm_label}' disagrees with the "
            f"computed value '{final}' — the computed value is authoritative; "
            "re-examine a domain rating if you believe the model."
        )

    return {
        "outcome": data.get("outcome", ""),
        "starting_level": start,
        "domain_rows": domain_rows,
        "downgrade_sum": downgrade_sum,
        "upgrade_rows": upgrade_rows,
        "upgrade_sum": upgrade_sum,
        "total_change": total_change,
        "final_certainty": final,
        "final_label": _LEVEL_LABEL[final],
        "warnings": warnings,
    }


def render(res: dict) -> str:
    lines = []
    if res["outcome"]:
        lines.append(f"Outcome: {res['outcome']}")
    lines.append(f"Starting level: {res['starting_level'].upper()}")
    lines.append("")
    lines.append("Domain            | Rating        | Δ")
    lines.append("------------------|---------------|---")
    for name, rating, pts, _just in res["domain_rows"]:
        lines.append(f"{name:<17} | {rating:<13} | {pts:+d}")
    lines.append(f"{'downgrade sum':<17} | {'':<13} | {res['downgrade_sum']:+d}")
    if res["upgrade_rows"]:
        lines.append("")
        lines.append("Upgrade (observational, no downgrade applied):")
        for name, pts, _just in res["upgrade_rows"]:
            lines.append(f"  {name:<20} +{pts}")
        lines.append(f"  upgrade sum          +{res['upgrade_sum']}")
    lines.append("")
    lines.append(f"Net change: {res['total_change']:+d}")
    lines.append(f"==> FINAL CERTAINTY (authoritative): {res['final_label']}")
    if res["warnings"]:
        lines.append("")
        lines.append("Warnings:")
        for w in res["warnings"]:
            lines.append(f"  ⚠️ {w}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic GRADE certainty recompute.")
    ap.add_argument("input", help="path to input JSON, or '-' for stdin")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON result")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"invalid JSON: {e}", file=sys.stderr)
        return 2

    res = grade(data)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(render(res))
    for w in res["warnings"]:
        print(f"⚠️ {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
