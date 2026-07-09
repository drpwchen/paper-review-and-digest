# paper-review + paper-digest

Two [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for reading a single
academic paper *properly* — one appraises whether it can be trusted, the other absorbs what it says.
Built by a practising physician for real journal-club and clinical use, then generalized for sharing.

📖 **Reading end** claude-paper-tools ｜ 🔭 **Discovery end** [paper-radar](https://github.com/drpwchen/paper-radar) — a personal literature radar that finds and ranks the papers these skills then appraise and digest; together the two repos form the full paper-reading pipeline.

> **English** · [繁體中文](#繁體中文)

---

## What this is

Reading a paper well is really two different jobs, and good readers keep them separate:

| Skill | Answers | What it does |
|---|---|---|
| **`/paper-review`** | *Can I trust this? Is it done well?* | Journal-club-grade appraisal: journal credibility, author track record, **reference verification with a live CrossRef existence gate**, design-routed risk-of-bias, spin / argument-structure audit, **deterministic GRADE**, citation-impact analysis. |
| **`/paper-digest`** | *What does it say? How do I absorb it fastest?* | A teaching-style content digest in three progressive-disclosure layers, structure routed by paper type, ending in active-recall self-test cards. Hard-stops without full text (no abstract-only fake digests). |

They are independent and can both run on one paper.

> **Part of a pipeline.** These skills are the *reading* end. The *discovery* end — a personal
> literature radar that pulls dozens of journal feeds + PubMed searches, ranks them by your interest
> model, and hands the picks off for appraisal/digest — is
> [**paper-radar**](https://github.com/drpwchen/paper-radar). paper-radar's `/paper-sync` dispatches
> a picked paper straight into `/paper-review` (🔬 quality) or `/paper-digest` (📚 content). Use them
> together, or either alone.

## Why it isn't just a clever prompt

Most "AI paper review" tools make two claims loosely — that they grade the evidence and that they
catch spin. Here those claims are made **true by real, deterministic code**. The split is the whole
point: **the language model does semantic judgement; a program does the logic and the arithmetic.**

### `grade_judge.py` — GRADE as arithmetic, not vibes
The model rates the five GRADE domains (risk of bias, inconsistency, indirectness, imprecision,
publication bias) as *not serious / serious / very serious*. A pure-stdlib script then **recomputes
the final certainty** from the starting level and the summed downgrades/upgrades, clamped to
[Very low … High]. The model's self-reported grade is advisory only; the script's number is
authoritative, and it warns when the two disagree. It also **enforces GRADE rules the model tends to
forget** — e.g. observational evidence can't be upgraded once any domain is downgraded.

### `argdown_lint.py` — inference gaps as a real gate
The model tags each supporting finding by premise type (`direct_rct`, `association`,
`surrogate_outcome`, `single_study`, `subgroup`, `secondary_outcome`, `mechanistic`,
`expert_opinion`). A stdlib script then **deterministically flags the illicit jumps** and exits
nonzero:
- surrogate outcome → hard-endpoint / causal benefit claim
- association → causal claim
- single study → "consistently shown"
- subgroup / secondary outcome only → benefit claim (classic spin)

### CrossRef existence gate
Before any semantic citation comparison, each selected reference is checked against the live CrossRef
API — catching fabricated DOIs and "right DOI, wrong paper" swaps that a purely semantic read misses.
(Unaudited LLM-written citations run ~40–80% accuracy; this is the cheap deterministic guard.)

### Delegated fan-out, and failures reported as gaps
The deep review keeps the intelligence-bound work (reading the paper once, appraisal, GRADE) in the
main context and **delegates the fan-out lookups** — author profiling, reference verification,
citation / PubPeer sweeps — to parallel subagents, so raw search dumps never bloat the analysis.
Every lookup that fails is **reported as an explicit gap** ("PubPeer sweep: FAILED / no hits"), never
silently dropped — an unrun check must not read as "nothing found".

### Design-routed risk of bias (not one checklist)
| Study type | Tool |
|---|---|
| RCT | Cochrane RoB 2 |
| Cohort / case-control / cross-sectional | ROBINS-I / Newcastle-Ottawa |
| Systematic review / meta-analysis | AMSTAR-2 + GRADE per outcome (+ PRISMA 2020 reporting check) |
| Diagnostic accuracy | QUADAS-2 |
| Prediction model | PROBAST |
| Guideline | AGREE II |
| Narrative review | SANRA + cherry-picking check |
| Case series / report | JBI checklist |

Observational studies additionally get checked against 35 bundled causal-inference doctrines
(`causal-appraisal.md`, digesting Hernán & Robins and the *Users' Guides to the Medical Literature*).

## Quick sanity check

```bash
cd paper-review
# GRADE: RCT starting High, two 'serious' domains → Low
echo '{"starting_level":"high","domains":[{"name":"risk_of_bias","rating":"serious"},{"name":"inconsistency","rating":"not_serious"},{"name":"indirectness","rating":"not_serious"},{"name":"imprecision","rating":"serious"},{"name":"publication_bias","rating":"not_serious"}]}' | python grade_judge.py -

# Argdown: surrogate premise → hard-endpoint claim → 1 gap flagged, exit 1
echo '{"claim":"Drug lowers fractures","claim_type":"hard_endpoint","premises":[{"id":"P1","type":"surrogate_outcome"}]}' | python argdown_lint.py - ; echo "exit=$?"
```

Both scripts are Python 3 stdlib only — no install, no dependencies, no network, no secrets.

## Install & configure

See **[SETUP.md](paper-review/SETUP.md)**. In short:

1. Drop `paper-review/` and `paper-digest/` into `~/.claude/skills/`.
2. `cp paper-review/config.example.yaml paper-review/config.yaml` and fill in your values.
3. Everything optional (vault paths, full-text resolvers, review-card site, clinical persona) is
   **off until you configure it**. The science core works with nothing configured.

Then in Claude Code: `/paper-review <DOI>` or `/paper-digest <DOI>`.

## Honest scope

This is a **reference implementation**, published as a one-time share and updated occasionally — not
a maintained product. It grew inside one person's Obsidian + Zotero + self-hosted review-site setup;
those couplings now live behind `config.yaml`.

- **Portable and dependency-free:** `grade_judge.py`, `argdown_lint.py`, `causal-appraisal.md`, the
  RoB routing table, the CrossRef gate, and the three-layer digest method work for anyone.
- **Yours to fill in:** vault paths, your library's full-text resolver, an optional review-card
  site, your clinical persona.

**Not medical advice; not a replacement for reading the paper.** It is a structured second reader
that refuses to let a plausible-but-wrong appraisal stand.

## Repository layout

```
paper-review/
  SKILL.md                 the appraisal skill
  fulltext-acquisition.md  shared full-text route ladder
  causal-appraisal.md      35 bundled causal-inference doctrines (no external dependency)
  grade_judge.py           deterministic GRADE recompute (stdlib)
  argdown_lint.py          deterministic inference-gap linter (stdlib)
  config.example.yaml      copy → config.yaml, fill in
  SETUP.md                 setup guide
  journal_cache.json       optional local cache to avoid repeat lookups
  author_cache.json        optional local cache
paper-digest/
  SKILL.md                 the content-digest skill (reads paper-review/config.yaml)
```

`config.yaml` is git-ignored — only `config.example.yaml` ships.

## Credits & licence

Deterministic GRADE and the CrossRef / argument-gate ideas are ported from and inspired by
[htlin222/robust-lit-review](https://github.com/htlin222/robust-lit-review). RoB tools, GRADE, and
PRISMA are the standard EBM instruments; the causal doctrines digest Hernán & Robins, *Causal
Inference: What If* and Guyatt et al., *Users' Guides to the Medical Literature*.

Licence: MIT (see `LICENSE`). The bundled EBM/causal content summarizes published methodological
literature for personal study use; cite the primary sources, not this repo, in academic work.

---

<a name="繁體中文"></a>

# 繁體中文

兩個 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill，用來把一篇論文「好好讀完」。
一個負責評「這篇可不可信、做得好不好」，一個負責「這篇講了什麼、怎麼最快吸收」。由一位臨床醫師
為自己的 journal club 與臨床決策打造，再抽掉私人設定後對外分享。

> [English](#paper-review--paper-digest) · **繁體中文**

## 這是什麼

把論文讀好，其實是兩件不同的事，會讀的人會把它們分開：

| Skill | 回答 | 做什麼 |
|---|---|---|
| **`/paper-review`** | *這篇可不可信、做得好不好？* | journal club 等級的評讀：期刊可信度、作者背景、**用 CrossRef 即時查證每篇引用是否存在**、依研究設計路由的偏差風險評估、spin／論證結構稽核、**確定性 GRADE**、被引用影響力分析。 |
| **`/paper-digest`** | *這篇講了什麼、我怎麼最快吸收？* | 教學式的內容整理，三層漸進揭露，依論文類型換骨架，最後生出主動回憶的自我測驗卡。**拿不到全文就硬停**（不做只靠摘要的假整理）。 |

兩者獨立，同一篇論文可以都跑。

> **這是一條 pipeline 的一端。** 這兩個 skill 負責「讀」。負責「發現」的另一端，是一個個人文獻雷達：
> 每天抓幾十個期刊 RSS + PubMed，依你的興趣模型評分排序，把挑中的論文交棒出來評讀／整理，那就是
> [**paper-radar 論文學習雷達**](https://github.com/drpwchen/paper-radar)。paper-radar 的
> `/paper-sync` 會把你勾選的論文直接派給 `/paper-review`（🔬 品質）或 `/paper-digest`（📚 內容）。
> 可以一起用，也可以各自單獨用。

## 為什麼它不只是一段厲害的 prompt

大部分「AI 幫你看論文」的工具，都鬆散地宣稱兩件事：它能評證據等級、它抓得到 spin。這個專案把這兩個
宣稱用**真正的確定性程式碼**做成真的。核心理念就一句話：**語言模型做語意判斷，程式做邏輯與計算。**

### `grade_judge.py`：把 GRADE 變成算術，不是憑感覺
模型只負責評五個面向（risk of bias、inconsistency、indirectness、imprecision、publication bias），
每項給「不嚴重／嚴重／很嚴重」。接著一支純標準庫的程式，**根據起始等級加總升降級、算出最終證據等級**，
並 clamp 在 [Very low … High]。模型自報的等級只當參考，程式算出來的才是準的，兩者不一致時程式會警告。
它還會**擋掉模型常記錯的 GRADE 規則**，例如觀察性研究只要有任一面向被降級，就不准再升級。

### `argdown_lint.py`：把結論的邏輯漏洞變成可檢查的 gate
模型負責把每個「支撐結論的發現」標上前提類型（直接 RCT 證據／相關性／替代指標／單一研究／次族群／
次要 outcome／機轉／專家意見），程式再**確定性地標出不合法的推論跳躍**，有漏洞就以非零結束：
- 用替代指標的改善 → 宣稱對真正臨床終點有效
- 用相關性 → 宣稱因果
- 用單一研究 → 宣稱「一致地顯示」
- 只靠次族群／次要 outcome → 宣稱有療效（典型 spin）

### CrossRef 存在性 gate
在做任何語意比對之前，先拿每篇被選中的引用去 CrossRef 即時查證，抓出假 DOI、以及「DOI 對但論文不對」
的張冠李戴。（未經稽核的 AI 引用正確率約四到八成，這是最便宜的一道防呆。）

### 委派 fan-out，失敗一律當缺口回報
深度評讀把「吃智力」的工作（讀論文本體一次、appraisal、GRADE）留在主脈絡，把**扇出型的查詢**
（作者側寫、引用查核、citation／PubPeer 掃描）**委派給並行的子代理**，讓原始搜尋結果不會塞爆主分析。
每一個查不到的項目都會**明確標成缺口**（「PubPeer 掃描：FAILED／無結果」），絕不默默丟掉，因為
「沒跑」不可以被當成「沒找到問題」。

### 依研究設計路由的偏差風險評估（不是一張萬用 checklist）
| 研究類型 | 工具 |
|---|---|
| 隨機對照試驗 | Cochrane RoB 2 |
| 世代／病例對照／橫斷 | ROBINS-I／Newcastle-Ottawa |
| 系統性回顧／統合分析 | AMSTAR-2 + 逐 outcome GRADE（+ PRISMA 2020 報告完整性檢查） |
| 診斷準確度 | QUADAS-2 |
| 預測模型 | PROBAST |
| 臨床指引 | AGREE II |
| 敘事型回顧 | SANRA + cherry-picking 檢查 |
| 病例系列／報告 | JBI checklist |

觀察性研究另外會對照 35 條內建的因果推論 doctrine（`causal-appraisal.md`，濃縮 Hernán & Robins 與
*Users' Guides to the Medical Literature*）。

## 快速驗證

```bash
cd paper-review
# GRADE：RCT 起始 High、兩項 serious → 算出 Low
echo '{"starting_level":"high","domains":[{"name":"risk_of_bias","rating":"serious"},{"name":"inconsistency","rating":"not_serious"},{"name":"indirectness","rating":"not_serious"},{"name":"imprecision","rating":"serious"},{"name":"publication_bias","rating":"not_serious"}]}' | python grade_judge.py -

# Argdown：替代指標前提 → 硬終點宣稱 → 標 1 個漏洞，exit 1
echo '{"claim":"Drug lowers fractures","claim_type":"hard_endpoint","premises":[{"id":"P1","type":"surrogate_outcome"}]}' | python argdown_lint.py - ; echo "exit=$?"
```

兩支腳本都是 Python 3 純標準庫，免安裝、零依賴、不連網、不碰任何金鑰。

## 安裝與設定

詳見 **[SETUP.md](paper-review/SETUP.md)**。簡單講：

1. 把 `paper-review/` 與 `paper-digest/` 放進 `~/.claude/skills/`。
2. `cp paper-review/config.example.yaml paper-review/config.yaml`，填入你自己的值。
3. 所有選用功能（vault 路徑、全文解析器、複習卡網站、臨床 persona）**沒設定就是關的**；科學核心不設定也能跑。

然後在 Claude Code 裡：`/paper-review <DOI>` 或 `/paper-digest <DOI>`。

## 誠實的定位

這是一個 **reference implementation（參考實作）**，以一次性分享的形式釋出、偶爾更新，不是一個持續維護的
產品。它長在某個人的 Obsidian + Zotero + 自架複習網站上，這些耦合現在都收進 `config.yaml` 了。

- **可移植、零依賴**：`grade_judge.py`、`argdown_lint.py`、`causal-appraisal.md`、RoB 路由表、
  CrossRef gate、三層整理法，對誰都能用。
- **要你自己填**：vault 路徑、你所屬機構的全文解析器、選用的複習卡網站、你的臨床 persona。

**這不是醫療建議，也不能取代你自己讀論文。** 它是一個會拒絕讓「看起來有道理但其實錯了」的評讀過關的第二讀者。

## 專案結構

```
paper-review/
  SKILL.md                 評讀 skill
  fulltext-acquisition.md  共用的全文取得路徑階梯
  causal-appraisal.md      35 條內建因果推論 doctrine（無外部依賴）
  grade_judge.py           確定性 GRADE 重算（標準庫）
  argdown_lint.py          確定性推論漏洞 linter（標準庫）
  config.example.yaml      複製成 config.yaml 後填寫
  SETUP.md                 設定指南
  journal_cache.json       選用本地快取，避免重複查詢
  author_cache.json        選用本地快取
paper-digest/
  SKILL.md                 內容整理 skill（讀 paper-review/config.yaml）
```

`config.yaml` 已被 git 忽略，只有 `config.example.yaml` 會進版控。

## 致謝與授權

確定性 GRADE 與 CrossRef／論證 gate 的概念，移植並啟發自
[htlin222/robust-lit-review](https://github.com/htlin222/robust-lit-review)。RoB 工具、GRADE、PRISMA
皆為標準實證醫學工具；因果 doctrine 濃縮自 Hernán & Robins 的 *Causal Inference: What If* 與 Guyatt 等人的
*Users' Guides to the Medical Literature*。

授權：MIT（見 `LICENSE`）。內建的實證醫學／因果內容為個人學習用途的方法學文獻摘要；學術引用時請引原始出處，
而非本 repo。
