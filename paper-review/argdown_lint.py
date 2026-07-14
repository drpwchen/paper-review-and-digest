#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""argdown_lint.py — deterministic inference-gap linter for a paper's argument.

/paper-review builds an explicit argument map: the paper's CONCLUSION (claim)
plus each finding that is supposed to support it, TAGGED by premise type. This
script deterministically flags the known illegal-inference patterns — the gaps
that "spin" hides behind — so the verdict isn't a holistic impression.

The LLM does the semantic work (reading the paper, tagging each premise's type
and the claim's type). This script does the deterministic work (given the tags,
which premise→claim jumps are logically illicit). That division is what makes
the gate real rather than vibes.

Zero dependencies (stdlib only). Portable: no private paths, no secrets.
Inspired by the /argdown reasoning gate in htlin222/robust-lit-review,
reimplemented as a standalone tag-based linter.

Input JSON (file arg or stdin):
{
  "claim": "Intervention X improves outcomes in condition Y",
  "claim_type": "causal" | "hard_endpoint" | "consistency" | "general",
  "premises": [
    {"id": "P1", "text": "...", "type": "direct_rct|association|surrogate_outcome|single_study|subgroup|secondary_outcome|mechanistic|expert_opinion", "supports": true}
  ]
}

claim_type meanings:
  causal        — asserts X *causes* / *improves* Y (needs interventional support)
  hard_endpoint — asserts benefit on a patient-important outcome (mortality, function…)
  consistency   — asserts the effect is *consistent / robust / repeatedly shown*
  general       — descriptive / hedged; most permissive

Usage:
    python argdown_lint.py argmap.json           # human-readable report
    cat argmap.json | python argdown_lint.py -    # stdin
    python argdown_lint.py argmap.json --json     # machine-readable

Exit code: 0 = no gap (inference clean), 1 = at least one gap flagged (this IS a
gate), 2 = bad input.
"""
from __future__ import annotations

import argparse
import json
import sys

_PREMISE_TYPES = {
    "direct_rct",         # interventional evidence directly on the claimed contrast
    "association",        # observational / correlational
    "surrogate_outcome",  # effect shown on a surrogate marker, not a hard endpoint
    "single_study",       # rests on one study
    "subgroup",           # subgroup finding
    "secondary_outcome",  # non-primary outcome
    "mechanistic",        # bench / plausibility
    "expert_opinion",     # authority, not data
}


def lint(data: dict) -> dict:
    warnings: list[str] = []
    flags: list[dict] = []

    claim = str(data.get("claim", "")).strip()
    claim_type = str(data.get("claim_type", "general")).lower()
    if claim_type not in ("causal", "hard_endpoint", "consistency", "general"):
        warnings.append(f"claim_type '{claim_type}' unknown — treated as 'general'.")
        claim_type = "general"

    premises = data.get("premises", []) or []
    supporting = [p for p in premises if p.get("supports", True)]
    for p in premises:
        t = str(p.get("type", "")).lower()
        if t not in _PREMISE_TYPES:
            warnings.append(f"premise {p.get('id','?')} type '{t}' unknown — ignored in gap checks.")

    def has(t: str) -> list:
        return [p for p in supporting if str(p.get("type", "")).lower() == t]

    def ids(ps) -> str:
        return ", ".join(str(p.get("id", "?")) for ps_ in [ps] for p in ps_) or "—"

    # ---- Rule 0: no supporting premise at all ----
    if not supporting:
        flags.append({
            "rule": "unsupported_conclusion",
            "premises": [],
            "detail": "The conclusion has no supporting premise in the map — it is asserted, not argued.",
        })

    # ---- Rule 1: surrogate premise → hard-endpoint / causal benefit claim ----
    surro = has("surrogate_outcome")
    if surro and claim_type in ("hard_endpoint", "causal"):
        direct = has("direct_rct")
        # only a gap if there is NO hard-endpoint-level support alongside the surrogate
        if not direct:
            flags.append({
                "rule": "surrogate_to_hard_endpoint",
                "premises": [p.get("id") for p in surro],
                "detail": "A patient-important / causal benefit claim rests on surrogate-outcome "
                          "premises with no direct hard-endpoint evidence. Surrogates frequently "
                          "fail to translate (Users' Guide doctrine #12).",
            })

    # ---- Rule 2: association premise → causal claim ----
    assoc = has("association")
    if assoc and claim_type == "causal":
        if not has("direct_rct"):
            flags.append({
                "rule": "association_to_causation",
                "premises": [p.get("id") for p in assoc],
                "detail": "A causal claim rests on associational/observational premises with no "
                          "interventional support. Correlation → causation gap.",
            })

    # ---- Rule 3: single-study premises → consistency claim ----
    singles = has("single_study")
    if claim_type == "consistency":
        distinct_studies = [p for p in supporting if str(p.get("type", "")).lower()
                            in ("single_study", "direct_rct", "association")]
        if len(distinct_studies) <= 1 or (singles and len(distinct_studies) <= 1):
            flags.append({
                "rule": "single_study_to_consistency",
                "premises": [p.get("id") for p in (distinct_studies or singles)],
                "detail": "A 'consistently / robustly shown' claim is backed by a single study. "
                          "Consistency requires multiple independent bodies of evidence.",
            })

    # ---- Rule 4: benefit claim rests only on subgroup / secondary outcomes ----
    if claim_type in ("causal", "hard_endpoint"):
        primary_support = has("direct_rct") or has("association")
        weak = has("subgroup") + has("secondary_outcome")
        if weak and not primary_support:
            flags.append({
                "rule": "spin_secondary_or_subgroup",
                "premises": [p.get("id") for p in weak],
                "detail": "The benefit claim rests on subgroup / secondary-outcome premises with no "
                          "primary-outcome support — classic spin (primary outcome likely null).",
            })

    # ---- Rule 5: mechanistic / expert_opinion only ----
    if claim_type in ("causal", "hard_endpoint"):
        data_premises = [p for p in supporting if str(p.get("type", "")).lower()
                         not in ("mechanistic", "expert_opinion")]
        weakest = has("mechanistic") + has("expert_opinion")
        if weakest and not data_premises:
            flags.append({
                "rule": "mechanistic_or_opinion_only",
                "premises": [p.get("id") for p in weakest],
                "detail": "A clinical benefit claim rests only on mechanistic plausibility / expert "
                          "opinion with no outcome data.",
            })

    return {
        "claim": claim,
        "claim_type": claim_type,
        "n_premises": len(premises),
        "n_supporting": len(supporting),
        "flags": flags,
        "clean": not flags,
        "warnings": warnings,
    }


def render(res: dict) -> str:
    lines = [f"Claim ({res['claim_type']}): {res['claim']}",
             f"Supporting premises: {res['n_supporting']}/{res['n_premises']}", ""]
    if res["clean"]:
        lines.append("✅ No inference gap detected — the premise set supports the claim type.")
    else:
        lines.append(f"🔴 {len(res['flags'])} inference gap(s) flagged:")
        for f in res["flags"]:
            prem = ", ".join(str(x) for x in f["premises"]) or "—"
            lines.append(f"  • [{f['rule']}] premises: {prem}")
            lines.append(f"      {f['detail']}")
    if res["warnings"]:
        lines.append("")
        lines.append("Warnings:")
        for w in res["warnings"]:
            lines.append(f"  ⚠️ {w}")
    return "\n".join(lines)


def main() -> int:
    # The gap banner carries 🔴/⚠️/✅; without this they raise UnicodeEncodeError on
    # non-UTF-8 consoles (cp950 / gbk / cp932), and the crash exits 1 — indistinguishable
    # from the "gap flagged" exit code this script signals with.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="Deterministic inference-gap linter.")
    ap.add_argument("input", help="path to argument-map JSON, or '-' for stdin")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON result")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"invalid JSON: {e}", file=sys.stderr)
        return 2

    res = lint(data)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(render(res))
    return 1 if res["flags"] else 0


if __name__ == "__main__":
    sys.exit(main())
