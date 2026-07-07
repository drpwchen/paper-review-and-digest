#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""透過 Elsevier TDM「Article Retrieval API」抓 ScienceDirect/Elsevier 全文。

KEY 安全處理：API key 從 PC 的 DPAPI secret store 讀（名稱 ELSEVIER_TDM_KEY），
讀進來只放在記憶體變數、塞進 HTTP header，全程「不列印、不寫檔」。
Claude 執行本腳本時只會看到全文結果與 HTTP 狀態，看不到 key 本身。

用法:
    python elsevier_fulltext.py <DOI> [輸出檔.txt]
    # 不給輸出檔 → 印全文前 3000 字到 stdout

先存 key（你自己跑，輸入時隱藏，Claude 看不到）:
    powershell -File ~/.secrets/secret.ps1 set ELSEVIER_TDM_KEY
（若在校外、需機構 token 才能解全文，可另存 ELSEVIER_INSTTOKEN；gold OA 通常只要 API key）
"""
import subprocess, sys, pathlib
import requests

SECRET_PS1 = pathlib.Path.home() / ".secrets" / "secret.ps1"


def get_secret(name):
    """從 DPAPI 取一個 secret；失敗回 None。stdout 只被本函式吃掉，不外流。"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-File", str(SECRET_PS1), "get", name],
            capture_output=True, text=True, timeout=20)
    except Exception:
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return r.stdout.strip()


def main():
    if len(sys.argv) < 2:
        sys.exit("用法: python elsevier_fulltext.py <DOI> [輸出檔.txt]")
    doi = sys.argv[1].strip()
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None

    key = get_secret("ELSEVIER_TDM_KEY")
    if not key:
        sys.exit("✗ 找不到 ELSEVIER_TDM_KEY。先存：\n"
                 "  powershell -File ~/.secrets/secret.ps1 set ELSEVIER_TDM_KEY")

    # 輸出檔副檔名為 .pdf → 抓 PDF（二進位）；否則抓純文字全文
    want_pdf = bool(out) and out.suffix.lower() == ".pdf"
    accept = "application/pdf" if want_pdf else "text/plain"
    headers = {"X-ELS-APIKey": key, "Accept": accept}
    insttoken = get_secret("ELSEVIER_INSTTOKEN")   # 可選；沒有就略過
    if insttoken:
        headers["X-ELS-Insttoken"] = insttoken

    url = f"https://api.elsevier.com/content/article/doi/{doi}"
    try:
        r = requests.get(url, headers=headers, params={"view": "FULL"}, timeout=90)
    except Exception as e:
        sys.exit(f"✗ 連線失敗: {e}")

    # 只印狀態；絕不印 headers（含 key）
    print(f"HTTP {r.status_code} · {len(r.content)} bytes")
    if r.status_code != 200:
        sys.exit("✗ 失敗，body 前 600 字（診斷用，不含 key）:\n" + r.text[:600])

    if want_pdf:
        out.write_bytes(r.content)
        print(f"✓ PDF 已存 → {out} ({len(r.content)} bytes)")
        return

    text = r.text
    # 粗略判斷是否只拿到 metadata（entitlement 不足時常見）
    if len(text) < 1500:
        print("⚠ 內容偏短，可能只拿到 metadata 而非全文（entitlement 不足？）")

    if out:
        out.write_text(text, encoding="utf-8")
        print(f"✓ 全文已存 → {out} ({len(text)} chars)")
    else:
        print("---- 全文前 3000 字 ----")
        print(text[:3000])


if __name__ == "__main__":
    main()
