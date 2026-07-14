#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fetch ScienceDirect/Elsevier full text via the Elsevier TDM Article Retrieval API.

KEY HANDLING: the API key is resolved through the configured secrets backend and
kept in memory only — it goes straight into an HTTP header and is never printed
or written to disk. Claude sees the full text and the HTTP status, never the key.

Usage:
    python elsevier_fulltext.py <DOI> [out.txt|out.pdf] [--backend env|dpapi|none|auto]
    # no output file  -> print the first 3000 chars of the full text to stdout
    # .pdf extension  -> fetch the PDF instead of plain text

Secrets backend (resolution order: --backend > $SECRETS_BACKEND > config.yaml
`secrets.backend` > "env"; an unrecognised value falls back to "env"):
    env    read ELSEVIER_TDM_KEY / ELSEVIER_INSTTOKEN from the environment
    dpapi  read them from the Windows DPAPI store (~/.secrets/secret.ps1)
    none   disable the route entirely
    auto   try env first, then dpapi

Store the key (env backend):
    export ELSEVIER_TDM_KEY=...          # or `setx` on Windows
Store the key (dpapi backend):
    powershell -File ~/.secrets/secret.ps1 set ELSEVIER_TDM_KEY

ELSEVIER_INSTTOKEN is optional — needed only when off-campus entitlement requires
an institutional token; gold-OA articles usually resolve with the API key alone.
"""
import os, re, subprocess, sys, pathlib
import requests

SECRET_PS1 = pathlib.Path.home() / ".secrets" / "secret.ps1"
CONFIG_YAML = pathlib.Path(__file__).resolve().parent / "config.yaml"
BACKENDS = ("env", "dpapi", "none", "auto")
DEFAULT_BACKEND = "env"


def config_backend():
    """Read `secrets.backend` from config.yaml. No YAML dependency: the key is a
    plain scalar, so a targeted regex is enough (and PyYAML is used when present)."""
    if not CONFIG_YAML.exists():
        return None
    try:
        raw = CONFIG_YAML.read_text(encoding="utf-8")
    except Exception:
        return None
    try:
        import yaml
        val = (yaml.safe_load(raw) or {}).get("secrets", {}).get("backend")
        return str(val).strip().lower() if val else None
    except Exception:
        pass
    m = re.search(r"^secrets:\s*$.*?^\s+backend:\s*[\"']?([A-Za-z]+)",
                  raw, re.MULTILINE | re.DOTALL)
    return m.group(1).strip().lower() if m else None


def resolve_backend(cli_backend=None):
    """--backend flag > $SECRETS_BACKEND > config.yaml > default. An unrecognised
    value falls back to the default rather than silently reaching for DPAPI."""
    for candidate in (cli_backend, os.environ.get("SECRETS_BACKEND"), config_backend()):
        if not candidate:
            continue
        candidate = candidate.strip().lower()
        if candidate in BACKENDS:
            return candidate
        print(f"⚠ unknown secrets backend {candidate!r}; falling back to "
              f"{DEFAULT_BACKEND!r}", file=sys.stderr)
        return DEFAULT_BACKEND
    return DEFAULT_BACKEND


def _from_env(name):
    val = os.environ.get(name)
    return val.strip() if val and val.strip() else None


def _from_dpapi(name):
    """stdout of the helper is consumed here and never propagates."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-File", str(SECRET_PS1), "get", name],
            capture_output=True, text=True, timeout=20)
    except Exception:
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return r.stdout.strip()


def get_secret(name, backend):
    if backend == "none":
        return None
    if backend == "env":
        return _from_env(name)
    if backend == "dpapi":
        return _from_dpapi(name)
    return _from_env(name) or _from_dpapi(name)   # auto


def key_help(backend):
    if backend == "dpapi":
        return ("  powershell -File ~/.secrets/secret.ps1 set ELSEVIER_TDM_KEY")
    if backend == "auto":
        return ("  export ELSEVIER_TDM_KEY=...   (or the DPAPI store on Windows)")
    return ("  export ELSEVIER_TDM_KEY=...        # Windows: setx ELSEVIER_TDM_KEY ...")


def main():
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    argv = [a for a in sys.argv[1:]]
    cli_backend = None
    for i, a in enumerate(argv):
        if a == "--backend" and i + 1 < len(argv):
            cli_backend = argv[i + 1]
            argv = argv[:i] + argv[i + 2:]
            break
        if a.startswith("--backend="):
            cli_backend = a.split("=", 1)[1]
            argv = argv[:i] + argv[i + 1:]
            break

    if not argv:
        sys.exit("usage: python elsevier_fulltext.py <DOI> [out.txt|out.pdf] "
                 "[--backend env|dpapi|none|auto]")
    doi = argv[0].strip()
    out = pathlib.Path(argv[1]) if len(argv) > 1 else None

    backend = resolve_backend(cli_backend)
    if backend == "none":
        sys.exit("✗ secrets backend is 'none' — the Elsevier TDM route is disabled.")

    key = get_secret("ELSEVIER_TDM_KEY", backend)
    if not key:
        sys.exit(f"✗ ELSEVIER_TDM_KEY not found via the {backend!r} backend. Store it with:\n"
                 + key_help(backend))

    # A .pdf output path means fetch the PDF (binary); otherwise fetch plain text.
    want_pdf = bool(out) and out.suffix.lower() == ".pdf"
    accept = "application/pdf" if want_pdf else "text/plain"
    headers = {"X-ELS-APIKey": key, "Accept": accept}
    insttoken = get_secret("ELSEVIER_INSTTOKEN", backend)   # optional
    if insttoken:
        headers["X-ELS-Insttoken"] = insttoken

    url = f"https://api.elsevier.com/content/article/doi/{doi}"
    try:
        r = requests.get(url, headers=headers, params={"view": "FULL"}, timeout=90)
    except Exception as e:
        sys.exit(f"✗ request failed: {e}")

    # Status only — headers (which carry the key) are never printed.
    print(f"HTTP {r.status_code} · {len(r.content)} bytes")
    if r.status_code != 200:
        sys.exit("✗ failed. First 600 chars of the body (diagnostic, no key):\n" + r.text[:600])

    if want_pdf:
        out.write_bytes(r.content)
        print(f"✓ PDF saved → {out} ({len(r.content)} bytes)")
        return

    text = r.text
    # Short body usually means metadata only — the common symptom of missing entitlement.
    if len(text) < 1500:
        print("⚠ body is short — this may be metadata rather than full text (entitlement?)")

    if out:
        out.write_text(text, encoding="utf-8")
        print(f"✓ full text saved → {out} ({len(text)} chars)")
    else:
        print("---- first 3000 chars ----")
        print(text[:3000])


if __name__ == "__main__":
    main()
