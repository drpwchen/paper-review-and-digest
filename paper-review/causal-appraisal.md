# Causal Appraisal Doctrines — bundled reference for /paper-review

Load this when appraising **observational studies** (and SR/MAs of them). Name the
doctrine explicitly when you flag a problem — that is what makes the review teachable.

Sources:
- Hernán & Robins, *Causal Inference: What If*
- Guyatt et al., *Users' Guides to the Medical Literature*, 3e

Two layers: **research-appraisal doctrines** (judging a paper) and **clinical causal
reasoning traps** (judging whether X caused Y for a patient). A good review uses both.

---

## Part A — Research-appraisal doctrines (18)

### Study design & methodology
1. **Target trial emulation** — evaluate an observational study as an attempt to emulate a hypothetical RCT. Specify eligibility, interventions, causal contrasts explicitly. Vague design → suspect.
2. **Consistency / well-defined intervention** — vague exposures ("obesity") have many versions → counterfactual ill-defined. Demand a specific, reproducible intervention.
3. **Non-inferiority trials need BOTH ITT and per-protocol** — ITT's bias toward the null falsely inflates apparent equivalence.

### Causality vs correlation
4. **Confounding vs selection bias (DAGs)** — confounding = common cause (backdoor path); selection bias = conditioning on a common effect (collider). Distinguish with a causal diagram.
5. **Never adjust for a collider** — adjusting for the common effect of two variables opens a spurious path. Watch for over-adjustment in multivariable models.
6. **Treatment-confounder feedback** — standard regression fails when a time-varying confounder is affected by prior treatment AND drives future treatment (CD4 → ART). Needs g-methods.

### Bias classification
7. **Loss to follow-up = selection bias**, not mere missing data. Censoring sharing unmeasured causes with the outcome destroys prognostic balance. Flag dropout >5–10%.
8. **Trials stopped early for benefit overestimate effects**, especially with <200 events. Treat with skepticism.
9. **ITT ≠ efficacy** — ITT measures effect of *assigning* treatment, not *receiving* it. Adherent-patient questions need per-protocol adjusted for prognostic factors.

### Treatment effects & clinical significance
10. **ARR/NNT over RRR** — RRR is misleadingly constant across baseline risks; always compute ARR and NNT at the patient's actual baseline risk.
11. **Deconstruct composite endpoints** — check components have similar importance and effect sizes; benefit may be driven only by the least important one.
12. **Reject unvalidated surrogates** — surrogate gains (HbA1c, BMD) often fail to translate to patient-important outcomes. Require within-class RCT validation. *(This is the doctrine argdown_lint's surrogate rule encodes.)*
13. **CI lower bound vs MCID** — judge significance by whether the CI's lower boundary clears the MCID, not by p alone. Below MCID = not definitive.

### Critiquing RCTs / observational / SR
14. **Subgroup claims are hypotheses** unless pre-specified, within-study, consistent across trials, and biologically plausible.
15. **Selective reporting** — compare published outcomes to the registry/protocol. Highlighted secondary outcomes when the primary failed = red flag.
16. **Heterogeneity** — I² >50% or non-overlapping CIs demands a clinical explanation, not just statistical pooling.

### GRADE-like reasoning
17. **GRADE factors override the design label** — RCTs can be low-certainty; observational bodies with huge consistent effects can be high.
18. **Evidence quality ≠ recommendation strength** — strong recs can come from low-quality evidence (life-threatening + safe/cheap); weak recs can follow high-quality evidence (balanced, value-dependent).

---

## Part B — Clinical causal-reasoning traps (17)

### Cause & effect thinking
1. **Reframe states as interventions** — "did obesity cause this?" → "would losing 5% BW via diet have prevented it?" Vague states aren't actionable causal questions.
2. **Prediction ≠ prevention** — a strong predictor need not be a causal target.
3. **No-interference assumption** — individual causal effect assumes one patient's treatment doesn't affect another's outcome. Breaks in infectious disease, vaccines, group/behavioral interventions.

### Counterfactual reasoning
4. **Two counterfactual worlds** — "did the drug cause this AE?" = "would *this* patient have had this event today without it?"
5. **Individual causal effects are unobservable** — one patient's recovery proves nothing; resist single-case causal claims.
6. **Dynamic strategies over static rules** — frame counterfactuals around realistic adaptive protocols ("treat until toxicity"), not "always vs never".

### Reasoning traps
7. **Confounding by indication** — treated patients are sicker → worse outcomes ≠ harmful drug. Always suspect in observational clinical experience.
8. **Survivorship / collider stratification** — clinic/hospital samples survived long enough to be seen; associations there may not exist in the full population.
9. **Don't control for post-treatment mediators** — adjusting for labs/symptoms caused BY treatment blocks the causal path → biased total-effect estimate.
10. **Hazard ratios flip over time** — early "weeding out" of susceptible patients makes treated survivors lower-risk → HR can flip even when treatment is uniformly beneficial/useless.
11. **Mismeasured treatment history creates false causality** — poor med-history documentation → unmeasured confounding.

### Intuition vs evidence
12. **Intuition fails with treatment-confounder feedback** — chronic treatment titrated on evolving labs (CD4, HbA1c) makes pattern recognition unreliable; needs formal causal methods.
13. **Surrogate vs causal effect modifiers** — "works better in group X" may reflect an unmeasured true modifier (physician quality, not nationality). Don't codify demographic rules without mechanism.
14. **Competing events ≠ censoring** — treating death as censoring assumes immortality to the competing event; distorts risk. Critical in geriatric/comorbid populations.

### Individual vs population
15. **Null average can hide opposing individual effects** — average = 0 doesn't mean no one benefits; look for effect modifiers.
16. **Transportability** — average effect depends on the population's modifier distribution; if your patient differs from the trial cohort, the estimate may not apply.
17. **ITT vs per-protocol for the individual** — ITT answers "what if I prescribe this?" (includes non-adherence); per-protocol answers "what if the patient takes it exactly?" Use ITT for policy, per-protocol for a motivated individual.
