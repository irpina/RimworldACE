# Project handoff — Labor Content and Economy

**Last updated:** 2026-09-12  
**Repository:** `C:\Users\PintS\OneDrive\Documents\Projects\snlt`  
**GitHub:** `https://github.com/irpina/RimworldACE`  
**Current branch:** `master`  
**Latest Stage 0 model commit:** `HEAD` (wages off the value of labor-power)
**Behavioral baseline:** `HEAD` (322 metrics; 22 wage-deviation, 20 habituation, 20 producer-cash, 12 posted-price, 17 procurement, 19 entry-on-margin and 22 exit-on-return readings)
**Docking with Wright's *Social Architecture of Capitalism* design / results:** `docs/97`, `docs/98` — the two models have **no observable in common**, so docking is an audit of *wiring*, not a comparison of outputs. Five of nine predictions passed, two failed, one half. **The finding: our wage share does not move** — 0.036090 in every 30-day window of a 720-day `complete_market` run (purses, posted prices, procurement, entry and exit all on, 107 exits), spread 2.5e-08, and `s/v` = 26.708 in all four scenarios. Capacity churns and the class distribution of the product never notices. Also: **no producer can die of its wage bill** (0 deaths against 107 exits on return), and `fund_wage_support` is 1e-13 everywhere — the fund's top-up branch is **latent, never taken**, which corrects `docs/97`'s own headline. `Region.labor_pool` is a fixed `1.0`, not `inf` as `docs/97` predicted. The instrument, `economy_lab/social_architecture.py`, is stdlib-only, integer-coin, deterministic, and **imports nothing from `model.py`**; 16 tests. Its reconstruction failed three times, and the third failure is the result: **firing on *current revenue* gives a stationary economy with a persistent ~33% reserve army; firing on *accumulated funds* gives 5 firms and one employing 992 of 1000 actors.** One rule decides whether a capitalist economy has a reserve army — and it is the rule our lab lacks. **The rule bodies are a reconstruction, not a transcription:** every full-text route was egress-blocked, so obtaining the paper (`arxiv.org/abs/cond-mat/0401053`) is the highest-value next action.
**The wage share — a correction to `docs/98`:** `docs/99` — **`docs/98`'s headline was wrong.** The wage share *does* move: **4.2%** of its level over a demand boom with bargaining on (realized share 0.036090 → 0.037660, peak premium +0.0784). `docs/98` measured four scenarios where `wage_bargaining_strength` defaults to `0.0`, so `_bargain` returned before touching anything and no premium ever formed — the same "*a default is not a scenario*" error `docs/98` catches in its own prediction 4, committed eleven paragraphs earlier. **A6 passes; the dock scorecard is six of nine, not five.** What survives is sharper: `necessary ÷ living` is an **identity**, `value_of_labor_power ÷ ticks_per_worker_day` (866.169930456 / 24000 = 0.036090414 against 0.036090369 measured — the employment quantum accounts for the last digits). **No quantity rule can move it** — not the wage bill binding, not entry, exit or worker mobility — and only the value of labor-power (habituation, technical change in wage goods) or the length of the working day can. That is the classical relative/absolute surplus-value distinction holding by construction, not a defect, and it **retires `docs/98` §5 step 4** before it was built. Six tests in `tests/test_wage_share.py` pin the identity, its escape via habituation, and the fact that the channel is off by default. **The rule added: before reporting that a rule does not do something, show the rule running** — this is the third time unreached code has presented as a finding (`docs/96`, `docs/98` prediction 4, this).
**The paper arrived — `docs/98` §3 refuted:** `docs/100` — the PDF (arXiv:cond-mat/0401053v2) was supplied and `economy_lab/social_architecture.py` is now a **transcription**, not a reconstruction. **`docs/98` §3's central finding is backwards.** Wright's rule F1 fires on `u = max(|W_a| − ⌊m_a / ⟨w⟩⌋, 0)` — the firm's **money holdings**, the rule `docs/98` rejected — and his model is stationary: ~130 firms, ~17% unemployment, firm-size Hill ≈ 1.2 across three seeds and 300 months at his own parameters (N=1000, M=100000, ω=[10,90]). The rule `docs/98` *adopted* (trailing revenue), put back in, collapses it to **27 firms and 50% unemployment**. "One rule decides whether a capitalist economy has a reserve army at all" is **withdrawn**. **Six rule bodies were wrong**, not three (`docs/100` §2): H1's threshold is tested *after* the weighted draw so a hire can fail; E1's spender is a *different* actor `b ∈ A−{a}`; F1 tests money holdings not revenue; wages are **redrawn at every payment** and the bill reckoned at `⟨w⟩`; W1 pays the **whole payroll when the employer acts** and part-pays when short; money is `m_i ∈ R+`, not integer. Confirmed correct: H1's candidate set `C ∪ U`, its wealth weighting, all of M1, SR1's order. **No single error reproduces the monopoly** — it needed the whole broken combination (`docs/100` §4), which is why isolating it by reasoning failed. The lesson: **a rule body chosen because it reproduces the target's published output cannot then be evidence about the target's mechanism.** Lab-side audit unaffected — six of nine predictions stand. 23 tests in `tests/test_social_architecture.py`, checking F1, H1, W1 and the class partition against the paper line by line. **Still open:** §3's figures are single-snapshot Hill readings, not fits against Wright's reported exponents.
**A3 — the constraint that cannot kill:** `docs/101` — **`docs/98`'s A3 finding is wrong.** "No rule makes the wage bill a solvency constraint" is false: `_produce` has curtailed output to what the purse affords since `docs/55`, and `_outlay_per_run` = inputs + `direct_labor × wage_rate / ticks_per_worker_day`. **For five of the circuit's nine processes — chemfuel, steel, wood, meals, herbal_medicine — the wage share of outlay is exactly 1.0000**, so the purse constraint *is* the wage bill and the rule is Wright's F1, bar one thing. **F1 floors: `⌊m_a / ⟨w⟩⌋`, so a firm below one average wage fires everybody and dies. Ours is continuous, so a purse of any positive size buys positive runs, which make sales, which refill the purse to sustain exactly those runs.** Measured: `cash_circuit`'s component producer drains 11.938 → **0.083** (0.7% of its 11.90 target) over 600 days, then holds at 0.082951 / 0.00189832 runs unchanged to day 1199; `liquidity_idle_days` never exceeds **0** against a `bankruptcy_idle_days` threshold of 30. A zombie: permanently insolvent, permanently alive. **The bankruptcy branch is unreachable for any producer that sells anything** — the `docs/96` defect class again, this time hiding under a finding that said the rule did not exist. Curtailment is 0 in `equilibrium`/`gravitation`/`complete_market` and 1.451509 in `cash_circuit`. **`docs/100` §7 is withdrawn** — it proposed building a rule that already exists. Six tests in `tests/test_wage_solvency.py`. **Next: (a) quantize employment at the producer** so F1's cliff appears and `_bankrupt` becomes reachable (gated off by default — it changes a committed scenario's outcome); **(b) A7 is the deeper divergence** — a producer whose revenue cannot fail has a purse that cannot empty — but revenue-as-a-draw needs a PRNG reproducible bit-for-bit across CPython and Mono under `docs/53`'s contract, **which is a decision to take before anything is written.** **Fourth instance of one failure: asserting a negative from an incomplete reading** (`docs/96`, `docs/98` pred. 4, `docs/99`, this). The rule added: *before reporting that a rule is absent, search for it.*
**The producer quantum design / results:** `docs/102`, `docs/103` — F1's floor, built and measured. **Four of eight predictions passed, two failed, one never reached.** The rule works and **the death does not follow**: at a 1e-3 worker-day quantum the drained component producer is idled on **251 of 1200 days** and its longest *consecutive* idle run is **1**, against a `bankruptcy_idle_days` threshold of 30. It oscillates with period two and never dies. **Why: idling repairs the purse** — a producer that runs nothing pays no wages and buys no inputs but **still receives revenue**, because our revenue comes from demand meeting stock rather than from employment. **There is no window** (prediction 3 failed): 0/1e-4/1e-3/3e-3 → 0 bankruptcies; 5e-3 → 4 deaths and employment 0.31819 → **0.04366**; 1e-2 → **102 deaths, employment 0.00000**. Nothing dies, then everything does — because a quantum that idles a producer permanently is one that exceeds its whole employment, and `wood` employs 0.000014 worker-days/day against `components`' 0.000395: "small" and "insolvent" are unrelated in this circuit. **Third distinct way this branch has been found unreachable** (`docs/101`: continuous curtailment; here: self-limiting idleness). **`docs/99`'s identity confirmed through a collapse**: bare wage share 0.036090610 with 102 bankruptcies and zero employment, against the identity's 0.036090716. **A7 restated precisely: in Wright revenue is produced *by employment* (M1 fires when an employee samples the market, so a firm with no employees receives identically zero); in ours revenue is produced *by demand meeting stock*.** That decoupling is why purses do not empty and why idleness repairs them — both attempts at endogenous firm death have now failed on it. Rule kept, gated off, inert where the purse does not bind. 10 tests in `tests/test_producer_quantum.py`. **Next is a decision, not a rule:** couple revenue to employment (Wright's form needs a PRNG bit-exact across CPython and Mono under `docs/53`), or the weaker form first — **make sales conditional on having produced**, which breaks the oscillation with no randomness at all, and is a modelling judgement rather than a technical one.
**Sales that follow production — THE FIRST ENDOGENOUS FIRM DEATH:** `docs/104`, `docs/105` — **six of eight predictions passed, and both failures are more interesting than the passes.** On **day 582** of `cash_circuit` both regions' component producers go bankrupt **because they cannot pay their wage bill**. That is the first endogenous firm death in this model's history: every previous retirement was `_exit` withdrawing capital from a sector below the going return; this is a firm that ran out of money and could not make payroll, which is Wright's F1. **The two rules are only jointly effective** — quantum alone: 0 bankruptcies, peak consecutive idle **1**; flag alone: 0; **together: peak idle 29, then `_bankrupt` on the thirtieth.** The leak was one line: `_supply_shares` fell back to apportioning by **capacity** when nobody ran, paying the sole component producer 100% of sales on its idle days. **Prediction 3 failed: the opening day has no yesterday** — the fallback condition holds exactly 18 times in 1200 days, once per commodity per region, **all on day 1**, when nothing has been produced yet. I wrote a `self.day > 0` guard, measured it, found the fallback fires on day **1** not 0, and **reverted rather than change it to `> 1`** — that would have fitted a magic number to make my own prediction retroactively true (`docs/100` §6's error). The unguarded behaviour is the better reading anyway: day 1's inventory is seeding, produced by nobody in-model. **Prediction 8 failed the other way and it matters: employment 0.31844 → 0.10914, a 66% collapse.** The producer was marginal in *employment* (0.12%) and **structural in *function*** — it was Department I. `capacity_lost`: components **0.125**, psychoid_leaves **104.03**, yayo 13.00, chemfuel 8.10, meals 1.30. A sector can be arbitrarily small in labour and still be what everything else is built out of. **A7 does not need to be built:** `docs/103` argued coupling revenue to employment required Wright's draw and a PRNG bit-exact across CPython/Mono under `docs/53`; it did not — the part that mattered was **conditionality, not randomness**. A draw would add revenue *uncertainty*, a different property, no longer on the critical path for firm death. **The A3 thread is closed. A5 (worker mobility) is the remaining `docs/50` critical-path divergence and the one the gameplay layer needs.** 9 tests in `tests/test_sales_follow_production.py`, including one pinning prediction 3's failure.
**Worker mobility — the last critical-path divergence, closed:** `docs/106`, `docs/107` — **all eight predictions hold**, the first document in this series where nothing was refuted, and `docs/107` says plainly which of the eight were tested and which merely did no harm. `Region.labor_pool` was a parameter that never moved; `_migrate` now runs at the start of each day, before `_produce` and before `_bargain` reads the employment rate whose denominator it changes. A region's **pull** is `(wage − mean) ÷ mean`; negative pulls send `strength × (−pull) × labor_pool` capped at `labor_pool − worker_days_earned`, positive pulls receive in proportion, and the last recipient takes the remainder so conservation is **exact** (drift 1.78e-15 over 1200 days). **The economics: in `demand_boom(bargaining=True)` at strength 0.05, Dust Basin's peak wage premium falls 7.84% → 4.25% (a 46% reduction) and the terminal wage gap falls from 5.10 silver/worker-day to 4.3e-14** — equalized — as **11% of Green River's pool** moves to the boom. Without mobility that 5.10 gap is one nothing in the model could close, because nobody could move to collect it. **Two predictions hold without being tested, and `docs/107` §2 says so:** the employment cap never came near binding (max rate 0.3657 against 1.0), and conservation is exact by construction rather than discovered. **What it is not:** not the colony as first mover — this moves an abstract pool between two laboratory regions, and a pawn arriving at a settlement is a gameplay-layer concern; and **not entry into or exit from the workforce** — total labour is conserved, so the unemployment the lab reports is still bounded by a supply no rule sets. Off by default, `equilibrium` with the rule **on** is bit-identical to it off measured by `==` on floats (both pulls exactly `0.0`, `labor_migrated` empty rather than small), 322 baseline metrics unchanged, 16 tests in `tests/test_worker_mobility.py`. **With A5 measured, `docs/50` §5's critical path has no remaining divergence from `docs/97`'s audit. The RimWorld mod implementation is next.**

**Closing the dock — two corrections to the record:** `docs/108` — before moving to the mod I re-read the audit's own instructions and found two items whose status had changed under later work without anyone re-measuring them. **(1) A2 is live, not latent, and `docs/97`'s prediction 2 passes.** `docs/98` measured `fund_wage_support` at 3.73e-13 and called the branch dead; **it is 9.75e-04 in the configuration `docs/105`'s deaths live in, and dust in every other** (quantum only 8.03e-13, flag only 3.53e-13). The same joint condition that makes A3 live makes A2 live — both are the purse actually binding, seen from two sides. It does **not** prevent the death: 3.86e-08 of the wage bill, machinists still dead on 582. **The support begins day 549 and runs to day 1200, six hundred days past the failure** — the `docs/105` cascade has a monetary shadow that does not close, and `fund_wage_support` is keyed by region alone so nothing says whose. **Widen that ledger before building on it.** The companion to `docs/101`'s rule: *before reporting that a branch is dead, find the configuration that would reach it.* **(2) A6 re-measured as `docs/98` §5 asked, and the answer is the wrong way round.** Twenty 30-day windows on `demand_boom(bargaining=True)`, realized share: **mobility off 4.2095%, mobility on 3.8102%** — the share still moves and **moves less**, because mobility's whole effect is to damp the premium that (with bargaining and no habituation) *is* the realized share's only movement. An endogenous reserve army **regulates the one channel already there rather than adding one**. Both runs share the same floor, 0.0360904 — the `docs/99` identity — so mobility lowers the ceiling and leaves the floor: the signature of damping rather than shifting. A6 survives at 3.81%; the *account* of why it moves is one channel narrower. `docs/98`'s prediction rows 2 and 3 are annotated in place. 7 tests in `tests/test_dock_closing.py`. **The audit is closed: all seven propositions measured, every divergence named.** Three things remain and none is the audit — `docs/100` §3's open loose end (the SA instrument's stylized facts are single-snapshot Hill readings, never fitted against Wright's reported exponents; the paper is in hand, and it validates the instrument not the lab), and **A4 plus the unclosed half of A5, which are both the mod** (A4 wants a colony that can *become* an employer; A5 is closed only between regions, so reported unemployment is still bounded by a total supply no rule sets). **That convergence is the audit's actual result: the remaining divergences did not scatter, they collected on the work that was always next.**

**The ablation grid — three findings, four refuted predictions:** `docs/109`, `docs/110` — the ten gated rules crossed over every combination the model permits. **Prediction 1 failed at once and usefully: 640 of 1024 cells threw**, not from a defect but because **the model validates rule prerequisites** (`procurement` needs `producer_cash` and `posted_prices`; `exit_on_return` needs `procurement`). **The rules are a dependency stack, not a cube** — 6 market-stack levels × 2 entry × 2⁵ = **384 cells**, exactly what survived. `docs/109` described them from their defaults rather than their validation; the rule this adds, after `docs/101`'s and `docs/108`'s: **before crossing two rules, check whether the model lets you.** Prediction 9 dies with it — procurement × posted is **not measurable**, no cell has one without the other. **(1) THE LARGEST INTERACTION IN THE LAB IS ONE RULE SWITCHING ANOTHER'S MECHANISM OFF.** Procurement × quantum on bankruptcies, **58% of spread**, negative: under `cash+posted` the quantum takes mean deaths **0 → 29.4**; under `+procurement` it takes them **1 → 1**, no effect at all. Procurement routes sales through producers' own stocks (`docs/59`) and purses stop draining. **(2) `docs/105`'s two deaths were the threshold, not the scale.** Same two rules, by regime: bare 0, posted 0, cash 8–10, **cash+posted 8–51**, +procurement 1, +exit 2. A **25× range** dominated by `posted_prices`, which `docs/105` never varied — which is also why quantum × sales-follow scores only **+0.031** pooled and ranks far below procurement×quantum (0.576), procurement×entry (0.414), cash×quantum (0.335). Its qualitative claim stands; its magnitude was one configuration. **(3) Worker mobility reverses sign, and `docs/107` is now annotated in place.** Dust Basin's net migration by regime: bare +0.055…+0.106 (**0/32** losing), cash +0.055…+0.212 (0/32), posted −0.19…+0.68 (8/32), cash+posted −0.22…+0.89 (6/32), +procurement −0.39…+0.47 (16/32), **+exit −0.94…−0.50 (32/32)**. The boom region **loses** labour in **62 of 192** mobility-on cells. Exit withdraws Dust Basin's capacity, employment collapses to 0.177, the premium goes **negative**, and mobility follows the wage *out*. `docs/107` measured the `bare` regime and stated a property of the model — the same error as `docs/98`'s wage-share headline. **A1 is now tested 384 times instead of five**, worst residual 2.14e-08. **Additivity is regime-dependent, 0.19 to 1.00** (`employment` 0.33 and `yayo_price` 0.41 under `+procurement`; `wage_share` 0.94–1.00 everywhere), so **a player-facing toggle can be reasoned about alone in a bare economy and cannot once procurement is underneath it** — which is `docs/109`'s stated worst case for the mod, arriving conditionally. Harness `economy_lab/grid.py` (process pool, order-independent output), raw cells in `economy_lab/grid_results.json`, 12 tests in `tests/test_ablation_grid.py`. No rule added or altered; baseline unchanged at 322. **The standing instruction this leaves: before a finding about the model goes into a document, run it across the regimes.**

**Wright's seven facts, FITTED — `docs/100` §3 closed:** `docs/111`, `docs/112` — **seven of ten predictions hold, two refuted, one split, and both refutations are my estimator rather than his model.** 100 seeds, 120 months burn-in discarded, then his own 15-year window: **2.19M pooled firm sizes, 1.49M incomes, 158k firm-years of profit.** **THE HEADLINE — the sharpest number in the paper matches: he reports 18 demises/month and 216/year; we get 17.95 and 215**, a 0.3% agreement on the one quantity that is a raw count with no estimator between model and number, so nothing can be tuned to produce it. Plus **unemployment 0.171 vs his ~17%**, **wage share 0.539 vs his 0.55**. It retires `docs/111`'s flagged worry: the demise fork — count only *firings*, per his literal wording, not a firm losing its last employee to a poach — was right. **Recessions looked refuted at λ=0.688 by MLE; fitted HIS way (OLS on the log-linear histogram) it is λ=1.285 vs his 1.22.** The fact holds; my estimator was wrong — and **his own sentence is internally inconsistent**, since an exponential with λ=1.22 has mean 0.82, not the "1.22 simulated years" he glosses it as. Duration histogram 318/120/33/8/2. **Firm size is the one real residual gap: 1.399 (MLE, x_min=46) / 1.257 (his method) vs his 1.038** — but **single-seed α ranges 0.906–1.978 (median 1.297), so his value sits inside our spread and the two are not distinguishable on the evidence his paper presents**, since OLS on a log-log histogram yields no CI. Pooling across seeds steepens the tail; he reports one run. Shapes all hold: **firm growth excess kurtosis 3.922, GDP growth 2.491** (Laplace=3, Gaussian=0 — measured by a moment, not by eyeballing a tent), **income Pareto α=1.178 over the top 8.0%** where he says "at most 10%" (my 10–20% band was the careless half of prediction 9), Gini 0.491, **profit-rate skewness 61.4**. Money conserved to 1.28e-09 across all 100 seeds. **METHODOLOGICAL FINDING, not about him personally: two of his seven headline numbers change materially under a better estimator on the same data** (1.399 vs 1.038; 0.688 vs 1.22) — **anyone comparing a model to this paper must fit the way he fitted, or the comparison measures the estimator.** **What this licenses:** `docs/110` §4's challenge to his generality rested on a transcription checked only qualitatively; it is now quantitative — demises to 0.3%, unemployment 0.6%, wage share 2%, recession decay 5%. The instrument is Wright's model closely enough to argue with. **It does NOT validate our laboratory, and does NOT show Wright wrong about anything.** Built: `History` recorder (opt-in, **provably RNG-inert** across 3 seeds × 120 months), `start_recording()`, `economy_lab/distributions.py` (stdlib CSN power-law MLE with KS-chosen x_min, lognormal/exponential/Laplace fits, bootstrap CI, shape moments — **no OLS-on-histogram, which is why his figures carry no CIs**), `economy_lab/wright_fit.py`. **α_Wright = α_CSN − 1**, and every figure names its convention. 13 estimator tests against known distributions. **OPEN (`docs/112` §6): the x_min candidate grid is capped at 200 points, and the KS goodness-of-fit bootstrap is NOT implemented — we have fitted power laws without testing whether power laws fit.** 322 baseline metrics unchanged.

**Does a power law actually fit? THE LOGNORMAL WINS:** `docs/113`, `docs/114` — closes `docs/112` §6. **Five of seven predictions hold, one refuted, one split, and the refutation runs AGAINST the power law.** **HEADLINE: across 100 seeds at Wright's own scale (n≈21,868), a lognormal fits his firm-size data better than a power law in 51 seeds and worse in ZERO** (median normalised LR **−2.03**; undetermined in 49). The power law is *adequate* — not rejected in 64/100 — but **adequacy is not the claim; Zipf is a claim about which family.** **Three lines agree:** the lognormal wins; **the exponent drifts 1.084 → 1.223 → 1.248 → 1.406 as n goes 1k → 10k → 100k → 1M**, where a genuine power law's MLE would settle; and the pooled fit is rejected outright. **Defensible statement: a heavy right tail, exponent ~1.1–1.4 depending on sample size, which a lognormal fits at least as well.** **This also explains `docs/112`'s firm-size gap, which that document could only note: at n=1000 we measure 1.084 — Wright's 1.038 is what you get at Wright's sample size.** The gap was never his model vs our transcription, just the same estimator drifting on different data volumes. `docs/112` §4 now carries the qualification in place; §6 closed. **The sample-size trap, measured not asserted:** p falls 0.74/0.46/0.00/0.00 up the ladder, and the pooled rejection comes with **KS 0.0304 — smaller than the 0.0714 that passed at n=1000**. The statistic improved and the verdict reversed because the test got more powerful. **A p-value without its sample size is not interpretable.** **TWO OF MY OWN ERRORS, both in the null, both caught by validating against known answers:** (1) recession durations tested against a *continuous* exponential gave KS 0.4975, p=0.000 — apparently refuting fact 5; against a **geometric** (right null for whole years) it is **KS 0.0270, p=0.223, NOT rejected, λ=1.165 vs his 1.22**; (2) the discrete KS statistic itself read **0.6881 on data drawn from the very distribution being fitted**, because the continuous left-limit term compares F(1) against an empirical zero — dropping it gives 0.0088. Both pinned as tests. **Third time in two days an apparent failure of Wright's model was my estimator (after `docs/112`'s λ and its firm-size α). THE RULE: when a reimplementation disagrees with a paper, suspect the measurement before the model.** **None of this says Wright is wrong** and it is not peculiar to him — CSN re-analysed two dozen published power laws and most lost to a lognormal; his tail *is* genuinely heavy (the exponential loses 98/100). Every other `docs/112` fact stands. **What made it sayable is the validated transcription: the claim is about his model's behaviour, not our reading of his prose.** Built: `goodness_of_fit` (CSN synthetic bootstrap, **each synthetic refit with its own x_min** — fixing it makes p far too small), `likelihood_ratio` (Vuong vs lognormal/exponential, with a **truncated-lognormal MLE by grid search** — fitting it untruncated rigged the comparison and reported **+9.09 for the power law on lognormal data**), `exponential_goodness_of_fit`, `geometric_goodness_of_fit`. **Calibration fact worth keeping: on data drawn from a GENUINE power law the lognormal still is not beaten (+1.35, undetermined) — the families are barely separable even when the truth is known, which is why a passed GOF test is weak evidence.** 28 estimator tests. **STILL OPEN:** the income tail is the weakest result (not rejected in only **46/100**, lognormal undetermined in **99/100** — neither pass nor refutation), and `docs/112`'s capped x_min grid stands.

**IS M1 LOAD-BEARING? YES, AND ONE HALF OF IT DOES BOTH JOBS:** `docs/115`, `docs/116` — answers the question `docs/110` §4 put to Wright. His market rule M1 has two separable ingredients he names himself: **linearity** (sample once per employee, *"a bias justified by the law of value"*) and **contingency** (the amount is `U[0, V]`). Crossing them gives a 2x2 — `wright` (both), `neutral` (contingency only), `fixed` (linearity only), `fixed_neutral` (neither) — built as `market_rule` on `social_architecture.Economy`, default bit-identical. 4 cells x 50 seeds, 120-month burn-in, 180-month window; harness committed as `economy_lab/m1_ablation.py`. **Four of seven predictions passed.** **(1) `wright` IS NOT AN ARBITRARY POINT IN THE SPACE.** It is nearest Wright's reported value on **all six** scoreable targets — unemployment 0.173 vs ~0.17, demises 17.90 vs 18, wage share 0.540 vs 0.55, recession lambda 1.227 vs 1.22, income alpha 1.179 vs 1.3, and the thinnest firm-size exponent 1.337 — and the three mutants miss on every one. M1 as written is load-bearing, not incidental. **(2) PREDICTION 3 FAILED, BACKWARDS, AND IN WRIGHT'S FAVOUR.** I predicted contingency carries Laplace growth. It does not: the main effect of linearity on firm-growth excess kurtosis is **+2.52**, of contingency **-0.43** (wrong sign). Killing randomness leaves kurtosis at 2.59; killing the size bias collapses it to **-0.358**, below normal. Firm-size tail (alpha 1.337 -> 4.715 under `neutral`) and Laplace growth rest on the **same** ingredient — the one he labels the law of value. `docs/115` §5 called that outcome a vindication; it is, more completely than predicted. **(3) THE TWO HALVES ARE NOT SEPARABLE.** |L x R| is **0.24-0.79 of spread on every metric**; firm count is 79% interaction with main effects of -18.6 and +0.24. Any "X% of the result is the law of value" is not well-posed here. Corollary: **removing linearity alone is worse than removing both** — `neutral`'s largest firm is 14.2 against `fixed_neutral`'s 25.5, because flat revenue against a linear wage bill actively punishes growth. **(4) Two more predictions died small.** Demises are the most inelastic fact in the table (1.78x max move, prediction wanted 2x). The wage share is **not** the pure accounting ratio `docs/99` implied: linearity's main effect on it is **+0.000 exactly**, but contingency's is **-0.126**, so it leaves [0.45, 0.65] at `fixed_neutral` (0.667) — windfall draws feed hiring and the share follows employment. **The method rule this adds**, after `docs/101`, `docs/108`, `docs/110`: **the distribution of an input is not the distribution of the output; before attributing a moment to an ingredient, ablate the ingredient.** Nothing here revives the power law — `docs/114`'s lognormal result stands untouched, and "tail" means heavy-tailed, not Pareto.


**WHAT THE ABLATION ENTAILS — and the one experiment that would close it:** `docs/117` — interpretation of `docs/116`, no new runs. **(1) The deflation is real and does not dispose of the model.** M1's linearity makes expected revenue proportional to headcount while payroll is too; that is multiplicative growth, and multiplicative growth makes heavy tails — Gibrat/Yule/Simon, a fact about proportional growth, not about capitalism. But Gibrat gives a firm-size distribution only. It does **not** give wage share 0.540, unemployment 0.173, recession lambda 1.227 and an income knee in the top 8% **simultaneously from the same single proportionality, in a model whose ontology is actors and money**. The joint fit survives the deflation; what `docs/116` shows is that it is **not robust** — it lives at one corner and all three neighbours miss all six targets. **(2) THE OPEN QUESTION IS BASIN VS KNIFE-EDGE, AND IT IS CHEAP TO SETTLE.** A 2x2 samples four corners and no interior, so we tested whether M1 is load-bearing (yes) and **not** whether its fit survives small perturbation. Evidence so far favours specificity over tuning — mutants fail **directionally**, not randomly (`neutral` kills tails while leaving the wage share at 0.501; `fixed_neutral` blows up unemployment and share specifically) — which looks like subtraction, not scatter. **Next experiment, predictions first: make the size bias continuous**, sample `members ** beta` (beta=1 is `wright`, beta=0 is `neutral`), sweep [0, 1.5]. Wide good region = basin, Wright's claim about as strong as a model claim gets; good only at beta~1 = the joint fit is a tuning result. **Third outcome is live: the facts may not share a region at all — Wright reports seven facts but never reports that one parameter setting gives all seven at once, and we would be the first to check.** One parameter on the same harness. **(3) SCOPE RESULT FOR THE MOD.** The signature comes from *proportionality of revenue to labour employed*; Wright gets it by assumption (sample per worker), we get it by construction (colonists produce, goods sell). So our Marxian apparatus is **not required for the seven facts and not in conflict with them** — that is the docked conclusion — and our original work is precisely what he cannot pose: rent, technique choice, Department I, the transformation, regional wage differentials. **The mod does not need to reproduce his seven distributions to be sound; it needs the proportionality, which it gets for free. Its job is the value machinery.** **(4) NEVER SHIP INDEPENDENT BALANCE KNOBS.** Interaction dominance is now confirmed in two codebases with two ontologies (|LxR| 0.24-0.79 of spread on every metric here; procurement x quantum 0.576 and negative in ours) — likely a property of the domain. Single-factor ablations are near-uninformative without their regime, and **sign is not stable**: removing linearity alone gives largest firm 14.2, removing linearity *and* contingency gives 25.5. Expose few knobs or measured presets. **(5) THE CAUTION.** "We docked with Wright" must not become "our model is validated" — that chains his model matching stylized facts to ours matching his, and neither link carries it. This is **code archaeology on a theoretical claim**, not empirical economics; it catches mis-attribution and can never elevate a model toward truth. The dock was worth doing for the errors it found (`docs/99`, `docs/113`, `docs/114`), and those were real.


**BASIN OR KNIFE EDGE? the size-exponent sweep design:** `docs/118` — design only, nothing built or run; measured in `docs/119`. Answers the question `docs/117` §3 left open: a 2x2 samples four corners and no interior, so `docs/116` showed M1 is load-bearing without showing whether its fit survives small perturbation. **The instrument: `drawn = rng.uniform(0, market) / members ** (1.0 - beta)`**, so expected revenue goes as `members ** beta`; beta=1 is `wright`, beta=0 is `neutral`. **Division, not multiplication — measured, not assumed:** the natural `x * members ** (beta-1)` double-rounds and disagrees with `x / members` on **46,338 of 200,000 draws (23%)**, while the division form disagrees on **0** at both endpoints because `m ** 1.0` and `m ** 0.0` are exact. The model is chaotic (a one-ulp change to a draw changes the pool and every later draw), so an inexact endpoint would not reproduce the existing cells at all. Builds `market_rule="scaled"` + `size_exponent`, existing branches untouched. **METHOD FIX CARRIED IN: fits go per seed (n~21,900), not pooled.** `docs/114` showed the exponent drifts with sample size (1.084 at n=1k, 1.406 at n=1M), which is why `docs/116`'s pooled 1.337 is **not** comparable to Wright's 1.038. **Two facts cannot be per-seed and the code says why: `history.gdp` and `wage_shares` are yearly (rule 1Y), so a 180-month window gives 15 observations** — GDP-growth kurtosis and recession lambda stay pooled and are labelled so. Workers fit their own run and return ~12 numbers plus three small series; `docs/116`-style records would have been ~240 MB here. **Grid: beta over [0, 1.5] at 0.1 plus 0.85/0.95/1.05/1.15, 20 points x 50 seeds = 1000 runs, ~12 min on four cores — measured at 2.9 s/run, not guessed (`docs/115` guessed and was wrong).** **Seven acceptance bands fixed in the doc before the run**, set around Wright's reported values, not around our own readings. **Seven predictions; 6 and 7 are the substance.** (6) the all-seven region has width <= 0.3 and is narrowed by a **tail** fact at both edges. (7) it is non-empty and contains beta=1 — **the one with a real chance of failing, and failure would be the most consequential result here: no single setting of Wright's own model would produce all seven facts at once. He reports the seven facts but never reports that one setting yields all seven simultaneously, and nobody appears to have checked.** **Outcome key:** width >= 0.5 = basin, Wright robust; width <= 0.3 centred on 1 with thin tails below and condensation above = **critical point**, a knife edge but a principled one (beta=1 is the unique scale-free exponent), and "the law of value" becomes the checkable claim that economies sit at criticality; narrow but off-centre, or edges set by a non-tail fact = tuned, the damaging reading; empty = the joint fit never existed. **Named threat to predictions 3-4:** they reason from Gibrat-style theory, which is exactly the surface reasoning `docs/117` §8 catalogues four failures of — and the code has a feature the theory lacks, `U[0, market]` draws from the **current remaining pool**, so whoever is selected early can take all of it. That preferential depletion may dominate beta entirely, and if so that is the finding.


**THE MODEL CANNOT REPRESENT A SIZE EXPONENT ABOVE 1 — and the line that stops it looks like a safety check:** `docs/118`, `docs/119` — 20 betas x 50 seeds = 1000 runs, fitted **per seed** at n~21,900. **The `docs/118` outcome key did not contain the answer.** "Basin or knife edge" presumes beta has two sides; it has one. **(1) THE HEADLINE.** `_sample` ends with `if drawn > self.market: drawn = self.market`, which reads as an overdraft guard. Counting how often it fires (a capped draw leaves `market` at exactly 0.0, observable from outside): **0.0% at beta<=1.0, then 25.2% at 1.1, 71.2% at 1.5, 86.0% at 2.0, 95.3% at 3.0, 99.0% at 5.0.** **beta=1 is exactly the largest exponent at which the rule never saturates.** Above it the draw is clamped and the rule degenerates into *whoever is selected takes everything left* — and selection is uniform over actors, so a firm is still chosen in proportion to headcount, which **is beta=1 behaviour**. The model does not run away above 1; it **reverts**. That one mechanism explains all three surprises: no condensation, alpha flattening at ~0.87 instead of falling, and six of seven facts still holding at **beta=5** (alpha 1.053, demises 20.6, share 0.532, no monopoly). **So the apparent robustness above 1 is degeneracy, not a basin — that side of the sweep tests nothing.** **(2) SCORING: 4 clean passes, 1 decisive failure, 1 partial, 1 hollow pass.** P4 (condensation above 1.2) **failed decisively** — 8/50 seeds, never a majority, largest firm rises 103->242 then *falls* to 202. P6 passed on the number (width 0.10 <= 0.3) and **failed on the substance**: its upper boundary is set by `gdp_kurtosis`, which a 1000-resample bootstrap shows **cannot resolve the betas it separates** (95% intervals at 1.10/1.15/1.20 overlap almost entirely; the 1.15 gap is noise). Its **onset** is sharp though — P(>=1.0) is 0.00 for every beta <= 0.85 and jumps at 0.90 — so it is a present/absent indicator, not a ranking, and treated that way the all-seven region runs **contiguously from beta=1.0 upward**. P7 passed with a detail the design missed: **beta=1 is the region's lower endpoint, not its centre.** **(3) MEASUREMENT DEFECT FOUND AND CORRECTED (`docs/114`'s rule paid off again).** Raw sweep gave **alpha=0.629 at beta=0** against 4.812 at 0.1 — a discontinuity at the point that is bit-identically `neutral`. The KS-minimising **`x_min` collapses to 1** in 32/50 seeds at beta=0, 9 at 0.1, 8 at 0.2, none above; alpha then bifurcates (0.62 collapsed vs 5.6 not) and the *median flips* on seed count. Corrected to 4.790. **The wider limit is not fixable by dropping seeds: median largest / median x_min is 1.1x at beta=0.1 and under 2x everywhere below beta=0.9 — a power-law exponent fitted over less than one octave is not a measurement.** So **alpha is uninformative below beta~0.9** and the right statement there is "there is no tail to fit", not "alpha is large". **New rule for the collection:** *a fitted exponent needs a pre-registered range to be fitted over; without one, a fit spanning 1.1x reports a number as confidently as one spanning 14x.* **(4) WHAT IT DOES TO WRIGHT.** His attribution survives and is **overdetermined** — proportionality is enforced twice, once by the sampling rule he wrote deliberately and once by a budget constraint that looks incidental. But **his facts do not identify beta=1 from above, because nothing above beta=1 is reachable: the seven facts pin the law of value as an *inequality*, not the equality his prose asserts.** Visible only with the rule made continuous. **(5) OPEN.** The lower boundary is **not** a measured transition — alpha is continuous (1.672 at 0.95, 1.296 at 1.00) and "beta=1" is where it crosses a band *we chose*; the sharp thing at 1 is saturation onset, not the facts. And **the alpha gap at Wright's own setting is sharper, not closed: per seed at n~21,900 we get 1.296 where he reports 1.038, and beta~1.07 would match him.** `docs/114` blamed sample size; at this scale a gap remains and is unexplained.


**CORRECTION — THE INEQUALITY WAS MY OWN BAND, AND beta=1 IS SHARPLY IDENTIFIED:** `docs/120`, `docs/121` — no new runs, re-reads the `docs/119` sweep. **`docs/119` §6 is WITHDRAWN.** It concluded the seven facts constrain **beta >= 1** (an inequality) because six of seven held at beta=5. That came from a band `docs/118` §4 registered as **firm-growth excess kurtosis >= 2.0 with the target written on the same line as "Laplace = 3"**. Laplace is a **point, not a floor**; a one-sided band cannot fail from above, so the one-sided region was **manufactured by the test**. Visible without any data — not the model surprising me. **New rule: a band must be able to fail in the direction the target can fail in.** **(1) GROWTH KURTOSIS DISCRIMINATES SHARPLY AND BINDS FROM ABOVE.** 2000-resample bootstrap, adjacent betas **do not overlap**: 0.95 -> 2.286 [2.20,2.41], **1.00 -> 3.889 [3.79,4.22]**, 1.05 -> 5.596 [5.31,5.89], 1.50 -> 9.076, 5.00 -> 6.384. Above beta=1 growth is **twice too heavy and getting heavier**, so every beta >= 1.05 is rejected decisively. `docs/119` §4's "six of seven at beta=5" is **five of seven** under a proper Laplace test, failing on one of the two facts Wright leads with. **(2) SATURATION SURVIVES, ITS INTERPRETATION DOES NOT.** The clamp counts are real (0.0% at beta<=1.0, 99.0% at beta=5) and it does pull **alpha** back toward 1 (1.053 at beta=5) — but it **rescues the cross-sectional fact and not the dynamic one**, so the model can tell beta=1 from beta=5 after all. **(3) THE BAND-FREE RESULT, which is the load-bearing one.** Scoring only against Wright's two reported firm-level numbers (alpha=1.038, Laplace kurtosis=3) with relative squared loss: **the optimum is beta=1.00 EXACTLY** (loss 0.150), and loss roughly **triples per 0.05 step** either way (0.430 at 0.95, 0.752 at 1.05). **His parameter is the joint optimum of his own facts — a stronger result than the paper claims for it.** **(4) BUT IT IS A COMPROMISE, NOT A FIT, AND THAT IS A NEW FINDING.** Alone, the firm-size exponent wants **beta=1.078**; Laplace growth wants **beta=0.972**; they **disagree by 0.106**, and at each one's optimum the other is off by ~2x (kurtosis 6.12 vs 3) or 45% (alpha 1.505 vs 1.038). At beta=1 **neither** target is met (alpha 1.296, kurtosis 3.889). **His two headline facts come from the same ingredient (`docs/116`) but want different strengths of it** — invisible from inside a single-setting model. **(5) THE IDENTIFICATION RESTS ON ONE FACT.** Four facts are indifferent to beta across the whole range (wage share, recession lambda, income alpha, unemployment), demises holds from 0.7 up, alpha from 1.0 up, GDP kurtosis is unresolvable — **firm-growth kurtosis alone supplies the upper constraint, and by `docs/116` it is the fact Wright credits to contingency when linearity carries it.** **`docs/121` is the synthesis we would actually put to Wright**, ordered by what would matter to him: two measurement defects (alpha needs its n beside it; fact 5 needs a geometric null, not a continuous exponential), one result weaker than stated (lognormal beats the power law 51/0 on his own output), three things found by varying what the paper holds fixed (M1 load-bearing; he under-credits the law of value for Laplace growth; his budget constraint enforces proportionality a second time), and the question we would most like to ask — **did he ever check that one setting gives all seven facts at once?**


**Wage-deviation design / results:** `docs/46`, `docs/47`
**Habituation design / results:** `docs/51`, `docs/52`
**Producer-level cash design / results:** `docs/55`, `docs/56`
**Firm-posted prices design / results:** `docs/57`, `docs/58` (experimental, off by default)
**Procurement design / results / correction:** `docs/59`, `docs/60`, `docs/62` (built, off by default)
**Entry on margin design / results:** `docs/61`, `docs/63` (built, off by default)
**Exit on return design / results:** `docs/64`, `docs/65` (built and measured, off by default)
**Exit floor design / results:** `docs/66`, `docs/67` (built; the floor works, and it uncovered a second defect)
**Sell-out after the draw design / results:** `docs/68`, `docs/69` (built; the second defect is fixed and the scarcity signal works)
**The churn design / results:** `docs/70`, `docs/71` (diagnosed; the first rule was built, failed and was reverted — the cause is elastic demand)
**Stage 1 port, second slice (the basket and the wage) design / results:** `docs/72`, `docs/73` (written to the contract; **the C# is not yet built**)
**Stage 1 port, third slice (the reserve army and habituation) design / results:** `docs/74`, `docs/75`
**Stage 1 port, fourth slice (the regional price update) design / results:** `docs/77`, `docs/78` (bit-exact under Mono, `exp` included)
**Stage 1 port, fifth slice (the wage-cost refresh):** `docs/79` — **the planned model's arithmetic is now ported**, 4,151 readings, zero ulps
**The port compiled and run:** `docs/76` — every slice bit-exact under **Mono**, the runtime the game loads. No unbuilt slices remain.
**Stage 1 persistence design / results:** `docs/80`, `docs/81` — a codec with no RimWorld reference, 2,078 values exact; **not yet wired to `Scribe`**
**Stage 1 amortised tick design / results:** `docs/82`, `docs/83` — `DayScheduler`; spreading a day across ticks leaves it bit-identical at every budget and every save point
**Stage 1 wealth coupling design / results:** `docs/84`, `docs/85` — `WealthCoupling`; the default is provably inert and the bound cannot be escaped, 2,526 property checks
**The shipping binary verified:** `docs/86` — `net472` builds with the real SDK, 0 warnings; the committed check harness **has now run** and passes; the `net472` artifact reproduces the laboratory to the bit under Mono
**A review pass:** `docs/96` — reading the session's ~2,000 lines found a **latent false failure** the harnesses could not reach: the mid-day resume verdict was recomputed from live state, so a perfect resume would report `FAIL` once the day finished. Harmless while a day has one phase, certain the moment it has two — which is the next thing the port does. Fixed by deciding the verdict once, at load.
**The readout — value, price, surplus and rent, legibly:** `docs/94`, `docs/95` — the one clause of Phase C's own definition that had not been started. Worker-days for work-ticks, price÷value as a pure number that is exactly 1.0 at equality, `s/v` as a rate, rent as a share; nothing reaches a player as `NaN`. Built and checked; the rows are empty until the model is wired to the world.
**Both assemblies verified:** `docs/93` — `verify.py` now checks the ported model too (eleven types, and **no RimWorld/Verse/Unity reference at all**, which `docs/53` §2 claimed and nothing had ever checked), and fails when the mod assembly does not reference it, i.e. when it is stale. **It fails on a fresh checkout for that reason** — the committed `SocialProduction.Economy.dll` predates this session's wiring. Rebuilding it is step 1 and `verify.py` is how you know you did.
**The port's verification is repeatable:** `docs/92` — `dotnet run --project economy_mod/Source/Economy.Core.Check` now covers **all five** ported slices plus the codec, scheduler, wealth coupling, self-check and budget (546 checks), and `… Economy.Drive` runs the component's five scenarios (28 checks). Most of this session's verification had been done with throwaway drivers and was a claim nobody could re-measure.
**The component driven against a fake host:** `docs/90`, `docs/91` — the façade gained behaviour and the wiring was *run*, not only compiled: 28 assertions over five scenarios, and **three defects found that compiling and reasoning both missed**, all of them the self-check reporting a failure for a case that did not apply
**The in-game self-check:** `docs/88`, `docs/89` — the mod checks itself on load and after a timed day and **logs a report to paste back**; `TickBudget` turns `PhasesPerTick` from a guess into a measurement. A session at the game is now: build, start, save/reload, load an old save, paste three reports.
**The mod compiled against ground truth:** `docs/87` — `economy_mod/Source/Economy.Facade/` is the RimWorld surface read out of the last real build with `monodis`; the mod's game-facing code builds `net472` against it with 0 errors, which proves the new wiring **adds no RimWorld API the previous real build did not already resolve**
**The float boundary rule:** `docs/81` §4 — **never let a float cross an implementation boundary as decimal.** Mono reading Mono is fine; Mono reading CPython fails 1 in 2,072.
**Phase D (gameplay layer) design:** `docs/50`
**Stage 1 port, first slice (the value solve) design / results:** `docs/53`, `docs/54`
**Laboratory viewer design / results:** `docs/48`, `docs/49` (`python -m economy_lab.viewer`)
**Sensitivity sweep, re-run:** `docs/45` (124 parameters, 0 refusals, ranked by reach)
**Capital-goods design / results:** `docs/36`, `docs/37`
**Capacity-exit design / results:** `docs/38`, `docs/39`
**Recreation-basket design / results:** `docs/40`, `docs/41`
**Absolute-rent design / results:** `docs/42`, `docs/43`
**Latest Labor Content commit:** `db769fd` (stuff-aware stats, generated defs, dendrovore graze fix)
**Closed-analysis correction:** `db769fd` — `animals.py` `can_graze` now accepts `Dendrovore`;
one def of 653 moved, `Meat_Alphabeaver` 717.7 → 5.2 ticks. `out/embodied_labor.csv` regenerated.
**Sensitivity harness:** `f2c490c`  
**Pre-process predictions:** `cae1ba2`  
**Process design decisions:** `863ee42`  
**Process tests:** `57b05ed`  
**Process results:** `98ae17e`  
**Upstream behavioral baseline:** `e2a7c43`
**Hysteresis investigation:** `097e40c`
**Production-control design:** `cbeb720`
**Production-control results:** `3f9c20b`
**Cost-floor design:** `a3fcfe7`
**Cost-floor results:** `9867014`
**Reserve design:** `34bf3ba`
**Reserve implementation:** `6eed091`
**Reserve results:** `d640485`
**Wage-relation design:** `13ec465`
**Wage-relation implementation:** `27af376`
**Wage-relation results:** `5985878`
**Endogenous value design:** `0c5bbf6`
**Endogenous value implementation:** `9426caf`
**Endogenous value results:** `c3db687`
**Competitive transmission design:** `a475152`
**Competitive transmission implementation:** `a9c3016`, `9826489`
**Competitive transmission results:** `77c3078`
**Constant capital design:** `87ac0cc`
**Constant capital implementation:** `7bd916c`, `83a780a`
**Constant capital results:** `1f48794`
**Latest Stage 1 implementation:** `6794dfc`  
**Stage 1 verification checkpoint:** `906f63e`

Read this file first when taking over the project. Then read `FINDINGS.md` before
changing any labor figures or assumptions.

---

## Project direction

The long-term goal is a suite of RimWorld mods that makes economic relations
material and legible, with particular emphasis on Marxian concepts:

- embodied and socially necessary labor;
- wage labor and labor-power;
- necessary versus surplus labor;
- realization of surplus through sale;
- market-price deviations from labor value;
- resource scarcity, differential rent, and monopoly rent;
- regional markets, costly planetary trade, and arbitrage;
- class consequences for workers and the player colony as collective owner.

The player colony will eventually hire temporary outside workers rather than
turning ordinary colonists into wage workers. Hired workers remain a distinct
class, receive real silver or explicit in-kind compensation, and do not own
their output.

---

## Distance to the full suite

An honest assessment of how far the project is from the direction above.
Percentages are rough and weighted by *remaining effort*, not by concepts
ticked off — a Python demonstration is far cheaper than a shipped, save-safe,
performant, playable mod.

### The three components

| component | state | remaining |
|---|---|---|
| **Labor Content** (`mod/`) | 543 defs patched across six files (548 `<Operation>` elements, five of them expansion wrappers), plus one 40-line stat worker rendering multiple units | the in-game visual pass — needs a human looking at real items; the 104 generated meat defs are now *cheap* to reach, since the assembly the constraint forbade exists |
| **Stage 0 lab** (`economy_lab/`) | 183 tests, 182 frozen metrics, three closing ledgers, a classical price system that now carries fixed capital, nine commodities and two regions, and a harness that runs 647 × 100 | **Phase A is finished** (`docs/44`); what is left is optional, not structural |
| **Stage 1 runtime** (`economy_mod/`) | about 550 lines of real C#: a daily tick, deterministic settlement profiles, faction regions, a persisted reload determinism check, and a read-only tab that lists them | the economic model itself; this is still only the world it will run on |

**The economics is the part that is nearly solved. The engineering that would
make it a playable suite is barely started.** Labor Content is one visual pass
from shipping; the simulation is maturing; the bridge between them is a stub.

### Coverage of the stated goals

| concept | in the lab | reaching a player |
|---|---|---|
| embodied and socially necessary labor | done, solved endogenously | yes — Labor Content, static figures |
| wage labor and labor-power | done | no |
| necessary versus surplus labor | done | no |
| realization of surplus through sale | done — money and labor s/v measured apart | no |
| price deviations from labor value | done — prices of production solved (docs/27) | no |
| differential rent | done | no |
| monopoly rent | **not started** | no |
| regional markets, costly trade, arbitrage | done | no |
| **class consequences; colony as collective owner** | **not started** | no |
| **hired outside workers** | **not started** | no |

Seven of ten concepts are demonstrated in Python. None of the dynamic ones
reach a player. The two bolded rows are the ones that are actually *gameplay*
rather than accounting, and neither has been started.

### Remaining phases

**Phase A — finish the economics** (~2–4 sessions). Prices of production,
the enlarged subsistence basket and turnover are all **done** (docs/27,
docs/29, docs/31), and so is the capital-goods sector (docs/37). The
two numbers the project reports as rates of profit are now rates, and
the price system's is 0.518 per day rather than 1.17 because fixed
capital is finally inside it. Capacity depreciation and exit are done
too (docs/39), and so is recreation in the basket (docs/41). The
sensitivity sweep has been re-run (docs/45): 124 parameters, no
refusals, and the ranking now says what the model is — the working day
and the subsistence basket on top. Absolute rent is measured (docs/43),
and wages now deviate from the value of labor-power under a reserve-army
rule (docs/47), with a sustained premium becoming the habitual standard
(docs/52). Monopoly rent proper and credit and bankruptcy remain optional.

**Phase B — scale test: DONE** (docs/33, one session). The lab was six
commodities and two regions; the harness now runs 647 commodities across 100
regions. After one method changed, cost is **linear** in both — 10.1× the
commodities costs 10.9× the time where it cost 22.5× — so the CPU miss is a
constant factor rather than a scaling failure, and a C# port at a
conservative 20× lands under 20 µs a tick. Ledgers close, determinism holds,
and the labor value solve reproduces the closed analysis exactly for all 447
commodities the generator did not contaminate.

**That finding is now closed too** (docs/35). `record_history=False` and
`history_every=k` land the runtime's memory at a flat 54 MiB at 647
commodities and 100 settlements, instead of 3.8 GB over a run, with the
laboratory's full history unchanged by default.

**Phase C — runtime port** (~6–10 sessions, the bulk of the work). Port the
model to deterministic C#; settlement profiles and regional membership; the
full economic state through save and load; a UI that makes value, price,
surplus and rent legible; integration with vanilla trade without
destabilising `MarketValue`, which drives storyteller wealth. Two
constraints are now measured rather than guessed: the daily update must be
**amortised across ticks** (about 1.1 s of C# work per simulated day at full
scale, against a 60,000-tick day), and the history design must change before
anything is ported.

**Phase D — the gameplay layer** (~4–8 sessions). Hired-worker
contracts: pawns arrive, work, are paid in silver or explicit in-kind, do not
own their output, and leave. Then the class consequences. **The design now
exists** (`docs/50`): four decisions a player makes, what reaches them from
which ledger, and three Stage 0 omissions it puts on the critical path —
habituation (done), worker mobility, and producer-level cash.

### Rough position: 35–40% of the suite

About twenty sessions of Stage 0 work have produced a rigorous simulation,
one shippable read-only mod, and — since `docs/33` — a measured answer to the
question that could have invalidated all of it. The remaining fourteen to
twenty-two sessions are mostly C#, UI, save compatibility and game design —
different skills, and less amenable to the design-doc-then-measure discipline
that has worked here.

The move from 30–35% is not a session's worth of code. It is that the largest
open risk turned out to be a constant factor rather than a rewrite.

### The three things most likely to derail it

1. ~~**Scale.**~~ **Retired** (docs/33), and the memory finding it left
   behind is closed too (docs/35). Nothing has replaced it on this list:
   the two remaining risks below are both about Stage 1 and neither is
   about whether the model works.
2. **The wealth coupling.** A dynamic price system feeding `MarketValue`
   changes raid strength, because storyteller wealth reads it. Getting this
   wrong makes the mod feel broken rather than interesting. Already flagged
   under "What vanilla RimWorld's economy actually does"; it constrains the
   whole Stage 1 design.
3. ~~**Phase D has no design.**~~ It does now (`docs/50`), written while the
   economics is still malleable. What replaces it on this list is the
   design's own §8: whether the value solve runs per region at game scale in
   C#, which `docs/53` starts to answer.

### Recommended ordering

Finish prices of production, since it resolves the authored-price wedge and
is the natural culmination of the value work. Then **jump the queue and do
the scale test** before the remaining economics sessions: if scaling forces a
structural change, it is better to find out with four mechanisms to rework
than eight. Sketch Phase D's design document soon, so the laboratory is aimed
at a game rather than at itself.

---

## Closed analysis: do not re-derive

`FINDINGS.md` is the completed and validated analysis of RimWorld's existing
value system. Treat it as closed unless new runtime evidence directly
contradicts it.

Headline result:

- embodied labor was solved for 653 defs from extraction outward;
- no market value entered the labor derivation;
- RimWorld prices extraction labor several times above fabrication labor;
- the defensible typical-good estimate is roughly 3–4×;
- the total-value-weighted estimate is roughly 14×;
- the magnitude is estimator-dependent, but the direction is robust.

Seven modelling errors were already found and fixed. Important traps include:

- inherited XML defaults are often invisible;
- recipe `<count>` values are ingredient-value units, not thing counts;
- small-volume gold/silver and nutrition recipes require conversion;
- `gestationPeriodDays` defaults to -1;
- `MarketValue` inherits rounding over 200;
- butchery has flat work against body-size-scaled yield.

Do not install a decompiler. The repository contains its own ECMA-335
metadata/IL reader in `cli_reader.py` and `dump_method.py`, and that reader
is what `verify.py` uses to check both mods' built assemblies.

This rule used to forbid the .NET SDK as well. **It no longer does** — Stage 1
needs an SDK to build `economy_mod` at all, and both mods now build through
it. The reason for the original rule survives the change: the *analysis* of
RimWorld's own assemblies is done with the repository's own reader, not by
decompiling.

---

## Labor Content mod

Purpose: two read-only info-card stats on producible things:

- extraction labor;
- fabrication labor.

Constraints:

- no gameplay change;
- no save impact;
- no Harmony;
- **one small assembly** — the constraint that used to say "no assembly"
  was dropped deliberately, see below;
- RimWorld 1.6;
- graceful behavior with any combination of official expansions.

Validated scope:

- 543 XML-backed defs can be patched;
- all 543 XPath targets were validated against the def database — note that
  this is an *ownership* check, not a load check, and the distinction cost
  three weeks (see below);
- 104 generated meat defs have no XML node, so no patch can reach them.
  This was a v1.1 gap while the mod was XML-only; now that it carries an
  assembly it is a short `StaticConstructorOnStartup` that writes the two
  statBases onto the generated defs, and should be reconsidered.

### Current uncommitted packaging work

The working tree contains deliberate Labor Content changes that predate the
Stage 0 commits. Preserve them:

- `make_mod.py` now splits patches by Core and each expansion;
- the old combined `mod/Patches/SNLT_LaborContent.xml` is removed;
- six generated patch files replace it;
- expansion files use `PatchOperationFindMod` with expansion display names;
- all six patch files contain 543 unique operations in total, and
  `make_mod.py` now refuses to write them if they are not load-shaped;
- `About.xml` now uses the public name **Labor Content** and a parka-led
  description;
- the fabrication stat description says “several times,” not an unqualified
  14×.

These changes were XML-parsed and ownership-checked but not committed. Do not
mistake them for unrelated dirt or discard them.

### Display units: multi-unit rendering, and why there is now an assembly

Embodied labor spans five orders of magnitude — 22 ticks for a wood log,
404,812 for the dearest bionic — so **no single unit reads well across the
range**. Seconds are unreadable at the top; hours are all zeroes at the
bottom. `StatDef.formatString` takes exactly one value and cannot compute a
second, so XML cannot solve this. That is the whole reason the mod now
carries an assembly.

`mod/Source/LaborContent/StatWorker_LaborContent.cs` overrides one virtual
method, `StatWorker.ValueToString`, and renders every unit that says
something, coarsest first:

| def | extraction | fabrication |
|---|---|---|
| `Steel` | 47.5 ticks | 0 |
| `MealSimple` | 5 ticks | 5 work-s · 300 ticks |
| `Apparel_BasicShirt` | 20 ticks | 26.7 work-s · 1,600 ticks |
| `Apparel_Parka` | 40 ticks | 3.2 in-game h · 133 work-s · 8,000 ticks |
| `ComponentIndustrial` | 9.5 work-s · 570 ticks | 2 in-game h · 83.3 work-s · 5,000 ticks |

A unit below 1 is dropped from the front rather than printed as a leading
zero-point-something. Both conversions are exact and neither is a
convention: a work-second is 60 ticks (`GenText.ToStringWorkAmount`'s
divisor), an in-game hour is 2,500. There is deliberately no "colonist-day",
which would need an assumption about how much of a day a colonist works.

What the assembly costs, stated plainly: the mod is now coupled to a
RimWorld version. The coupling is as small as it can be — the built DLL
binds to exactly two RimWorld symbols, `RimWorld.StatWorker` and
`Verse.ToStringNumberSense` — and `formatString` and `toStringStyle` are
kept in the defs so the stat still renders if the worker ever fails to load.

**Build:** `sh mod/Source/build.sh`. It used to invoke the `csc.exe` that
Windows ships with the .NET Framework, because this document said not to
install the .NET SDK — a constraint that lapsed the moment Stage 1 needed
the SDK anyway. Since 2026-08-26 the build goes through
`mod/Source/LaborContent/LaborContent.csproj`, exactly as `economy_mod`'s
does, and works on macOS as well as Windows. `LangVersion` stays at **5**
so the source is still buildable by the old compiler on a Windows machine
with no SDK, which is why it has no interpolated strings.

**The build is reproducible now, and the DLL is committed.** The old csc
predated Roslyn's `-deterministic` and stamped a fresh MVID into every
build, so two builds of identical source differed in their bytes and the
committed binary could not be checked against the committed source by
hash. That is no longer true of builds made through the csproj: two
consecutive Release builds are byte-identical (verified 2026-08-26). The
committed DLL was last built by the old csc, so it does not match a fresh
build's hash — the first rebuild replaces it, and from then on the hash is
evidence.

The other thing that changed with the compiler is **encoding**. Roslyn
reads source as UTF-8, so the ANSI-codepage trap below no longer applies
to this build path. `verify.py` still checks the separator, because the
failure mode was real and the check is free.

What *can* be checked is content, and `mod/Source/verify.py` checks it
after every build using the repository's own ECMA-335 reader: that the
type the StatDefs name exists, that `ValueToString` is a public virtual
override, that the separator is U+00B7 rather than mojibake, and that the
assembly still binds to exactly two RimWorld symbols. The separator check
is load-bearing — corrupting it in a built DLL does make the verifier
fail.

**Encoding trap, already hit once:** the source has no byte-order mark, so
`csc` reads it in the ANSI codepage. A literal `·` in a string arrives in
the assembly as `Â·`. The separator is written `·` for that reason, and
the build is verified by looking for the UTF-16 bytes in the DLL.

**The visual pass is complete** (2026-08-25, RimWorld 1.6.4871 rev591, all
five expansions loaded), and a second pass verified the chain arithmetic on a
bolt-action rifle against the card's own rows: extraction 4,560 ticks is
60 steel x 47.5 + 3 components x 570, and fabrication 27,000 ticks is the
components' own 15,000 plus the rifle's 12,000 — which is the 200 shown in
"Work to make".

**Everything below is confirmed in game**, on the final build:

```
Plasteel knife                        Alpha thrumbo meat
  Extraction labor   3 in-game h · 125 work-s      0.5 ticks
  Fabrication labor  1.58 in-game h · 66 work-s    0
```

- the `SNLT_LaborContent` section renders with its own header, between
  Basics and the item's own category;
- the U+00B7 separator renders rather than mojibake;
- stuff-awareness works: the plasteel knife reads 125 work-s of extraction
  where the flat figure was 18.8, and its fabrication of 66 matches "Work
  to make: 66" on the same card — **both self-check identities close**;
- the 104 generated meat defs carry values, including expansion ones
  (alpha thrumbo is Odyssey);
- the corrected Alphabeaver figure is right;
- a `0` row is wanted rather than hidden, and the line fits at low
  resolution;
- no errors in the log.

**At most two units are shown**, because three wrapped onto a second row on
a rifle at 1080p. The unit dropped is always the least useful one present —
ticks, once a thing is large enough to have hours. Small things still read
in ticks alone, which is exactly when ticks are the readable unit.

### Stuff-awareness and generated defs: both done

**The stat is stuff-aware.** `solver.py` treats stuff as a substitutable
input and picks the cheapest, so the knife's solved 1,125 ticks of
extraction is *obsidian's* — a plasteel knife was under-reporting its
material by 6.7×. The patches now ship a **stuff-free base** and
`GetValueUnfinalized` adds `costStuffCount ×` the stuff's own extraction
labor, which is already patched onto Steel, Plasteel, Obsidian and the
rest.

The subtraction has to reproduce the solver's choice exactly, so
`make_mod.py` recomputes it and the identity was checked across all **174**
stuffable defs with a `costStuffCount`: none went negative. A knife's
stuff-free extraction is **0.0** — a knife's extraction labor *is* its
metal — so a plasteel knife should read `3 in-game h · 125 work-s · 7,500
ticks` where it read `18.8 work-s · 1,125 ticks`.

**Fabrication is stuff-scaled too**, added right after, once the material
change was confirmed in game. RimWorld multiplies the work itself by a stuff
factor — Plasteel's `WorkToMake` factor is 2.2 — so a plasteel knife really
does take 2.2× the labor of a steel one. Leaving it unscaled while
extraction *was* stuff-aware made the two rows disagree with each other and
with "Work to make" three lines above them. The factor is read from
whichever of `WorkToMake` / `WorkToBuild` the def actually declares, so a
stuffed wall is not scaled by a factor meant for a weapon.

The payoff is that **the card now checks against itself**: a plasteel knife
reads 66 work-s of fabrication, and "Work to make" on the same card reads
66.

### What the two rows mean, and how to check one against the card

The two stats are **disjoint and additive**; neither contains the other.

- **Extraction labor** — all upstream mining, harvesting and butchery.
  Vanilla shows this *nowhere*.
- **Fabrication labor** — this thing's own work **plus all upstream
  fabrication**. Cumulative up the chain.
- RimWorld's **"Work to make"** is bench time for the final step only.

So the identity that makes a card self-checking is:

```
fabrication row  −  ingredients' fabrication  =  "Work to make"
```

| | fabrication row | ingredients' fab | "Work to make" |
|---|---:|---:|---:|
| plasteel knife | 66 | 0 (plasteel is mined) | **66** ✓ |
| bolt-action rifle | 450 | 250 (3 components) | **200** ✓ |

The knife's two figures coincide only because plasteel requires no
fabrication; the rifle shows the general case, where the row is more than
double the card's number because someone had to make the components first.
A plasteel knife's *total* embodied labor is 125 + 66 = **191 work-s**,
against the 66 vanilla admits to.

### How much vanilla hides — the mod's case, quantified

Across all 653 solved defs:

| | |
|---|---:|
| share of all embodied labor that is extraction | **22.0%** |
| defs where extraction **exceeds** fabrication | **250 of 653 (38%)** |
| defs that are pure extraction (`Work to make` absent or 0) | **175** |

The average understates it. `ToolCabinet` says "Work to make 30" and
embodies 188 work-s — **84% extraction**; `WaterproofConduit` is 93%;
`SunLamp` 85%. The clean counter-example is stone blocks at 0% extraction,
because chunks are free to pick up, so vanilla's figure there really is the
whole story.

This is the same seam `FINDINGS.md` measured from the other side. Vanilla
shows **work** for the last step and **value** for everything, and
`MarketValue` *does* recursively carry ingredient costs — so the price
system prices extraction's contribution while the interface never shows the
labor behind it. Putting the two rows side by side is what makes the split
visible, and on 38% of items the hidden half is the larger half.

### Verifying the numbers: `check_labor.py`

`python check_labor.py <defName> [stuff ...]` prints the working behind any
info-card row — the ingredient breakdown, the thing's own work, the shipped
stuff-free base, and what the card should read for each stuff. It renders
through the same precision and two-unit rules as the StatWorker, so its
output is directly comparable to the screen.

```
$ python check_labor.py Gun_BoltActionRifle
      60 x Steel                 ext  2,850   fab       0
       3 x ComponentIndustrial   ext  1,710   fab  15,000
                        subtotal ext  4,560   fab  15,000
this thing's own work: 12,000 ticks = 200 work-s
  Extraction labor    1.82 in-game h · 76 work-s
  Fabrication labor   10.8 in-game h · 450 work-s
```

Two identities make a card self-checking, and both hold on the rifle: the
extraction row is the ingredients' extraction, and fabrication minus the
ingredients' fabrication is the card's own "Work to make".

**Precision is six decimal places, not three.** Values ship in
work-seconds, and a sub-tick figure like alpha thrumbo meat — 0.5 ticks =
0.008333 work-s — rounded to 0.008 and displayed as **0.48 ticks**, a 4%
error. The smallest values are exactly the ones with no headroom, and they
are all in the generated-meat table. Caught by comparing a card against
`out/embodied_labor.csv`, which is the check `check_labor.py` exists to make
routine.

**The Alphabeaver outlier is a classification gap, not a finding.** Meat
extraction labor broadly tracks inversely with body size — Thrumbo 0.5
ticks, Elephant 0.6, median 6.5 — and **Alphabeaver is 717.7**, ten times
Cat's 66.4 despite the larger body. Flagged first as a possible instance of
the inherited-defaults trap; it is not.

Butchery work is only part of the labor. The rest is the cost of *raising*
the animal, and an alphabeaver's `baseHungerRate` is **3.0** — nearly twice
a thrumbo's 1.75 on a body a ninth the size, because it is a
`DendrovoreAnimal` designed to eat your trees. Feeding one to adulthood
costs **68.2 nutrition and yields 63 meat**:

| animal | nutrition to adult | adult meat | nutrition per meat |
|---|---:|---:|---:|
| Muffalo | 12.3 | 336 | 0.04 |
| Cat | 4.0 | 45 | 0.09 |
| Elephant | 78.3 | 560 | 0.14 |
| Thrumbo | 155.2 | 560 | 0.28 |
| **Alphabeaver** | **68.2** | **63** | **1.08** |

Thirty times worse than a muffalo. That much is real — the hunger rate is
extreme by design, because alphabeavers exist to strip a forest fast enough
that a player wants them gone.

**But it does not explain the 717.7, and an earlier note in this file
claiming it did was wrong.** `animals.py` charges feed labor only to
animals that cannot graze, and the test is one string:

```python
can_graze = "Rough" in food      # foodType
```

RimWorld has exactly three dendrovores. **Thrumbo** and **AlphaThrumbo**
list `VegetarianRoughAnimal, DendrovoreAnimal`, match "Rough", graze for
free, and come out at **0.6 and 0.5 ticks**. **Alphabeaver** lists
`DendrovoreAnimal` alone, misses the test, and is billed 68.2 nutrition of
**hay it cannot eat** — giving **717.7**.

So one animal, one string test, and the entire 1,435× spread across the 104
meat defs. The module's own justification for the graze rule is that
"pasture is finite, but that is differential rent, not labor content" — and
a wild forest is a free gift of nature on exactly the same terms. Whichever
way it is resolved, treating two dendrovores differently because one of
their `foodType` lists happens to also say "Rough" is not defensible.

**Fixed (2026-08-25), on the user's decision.** `can_graze` now accepts
`Dendrovore` as well as `Rough`. The blast radius was measured by diffing
the whole solve before and after:

| | |
|---|---|
| defs whose embodied labor moved | **1 of 653** |
| `Meat_Alphabeaver` | 717.7 → **5.2 ticks** (−99.3%) |
| meat table spread | 1,435× → **179×** |

Alphabeaver meat now sits *below* the 6.50 median and correctly cheaper
per unit than Cat (66.4) or Husky (89.7), which is what a larger
free-feeding animal should look like. No leather ripple: the cheaper
carcass did not displace any other source of `Leather_Light`.

This is a `FINDINGS.md` correction. The headline conclusions are unaffected
— one meat def out of 653, and the extraction-versus-fabrication premium
does not run through it.

**The 104 generated meat defs are reached.** They have no XML node, so no
patch can touch them. `LaborContentTableDef` ships the solved figures and a
`[StaticConstructorOnStartup]` writes them onto the defs, logging how many
applied. Shipping the numbers rather than re-deriving them keeps generated
and patched defs from drifting apart.

### The expansion gating is correct, and here is the proof

`PatchOperationFindMod` calls `ModLister.HasActiveModWithName`, which
compares against `ModMetaData.Name` — and for official DLC that returns
`ExpansionDef.label`, not the About.xml name (the DLCs have no `<name>` at
all). Those labels are exactly `Royalty`, `Ideology`, `Biotech`, `Anomaly`,
`Odyssey`, which is what the patches ask for.

One caveat: `label` is translatable, so a non-English install may not match.
Untested.

### The expansion split never loaded, and why nothing caught it

The five expansion patch files applied **nothing** from the day they were
generated until 2026-08-25. Only Core's 281 defs were ever patched; the 262
defs belonging to Royalty, Ideology, Biotech, Anomaly and Odyssey were not.

The cause is one element name. A direct child of `<Patch>` must be
`<Operation>`, but an entry in a `PatchOperationSequence`'s `<operations>`
list is an ordinary list item and must be `<li>`. The generator emitted
`<Operation>` in both places. Core has no `PatchOperationFindMod` wrapper,
so Core was correct by accident and the bug was invisible in the only file
anybody looked at closely.

RimWorld says so plainly — *"List item found with name Operation that is not
`<li>`"*, five errors, counts 27/55/63/50/67, exactly the five files' def
counts — but only in the log, and only at load.

**Everything the project checked was true and none of it was the right
check.** The XML parsed. The XPaths resolved against the def database. The
def counts reconciled to 543. All of that can hold while the file applies
nothing, because the failure is in how RimWorld deserializes a list, which
no amount of parsing or counting can see.

`make_mod.py` now validates structure after every write and refuses to ship:
root must be `<Patch>`, its children must be `<Operation>`, `<operations>`
entries must be `<li>` carrying a `Class`, and plain string lists like
`<mods><li>Anomaly</li></mods>` are deliberately exempt. Reintroducing the
exact shipped bug makes it refuse.

### Deployment: junction, not a copy

`RimWorld/Mods/SNLT` is a **directory junction** to this repository's `mod/`,
matching how `SocialProductionEconomy` points at `economy_mod/`. Rebuild or
regenerate and the game sees it; there is no copy step to forget.

On macOS the same two names are **symlinks**, and the `Mods` folder is
inside the app bundle:

```sh
MODS="$HOME/Library/Application Support/Steam/steamapps/common/RimWorld/RimWorldMac.app/Mods"
ln -sfn "$PWD/mod"         "$MODS/SNLT"
ln -sfn "$PWD/economy_mod" "$MODS/SocialProductionEconomy"
```

Because they live inside the bundle, a Steam validation or update can remove
them. If the game stops seeing either mod, check the links before anything
else — and re-read the false-pass story below, because a missing link is the
same class of failure as a stale copy.

This was not always so, and it cost a false pass. The first in-game check of
the multi-unit stat worker *looked* correct — the rows rendered plausible
`work-s` figures — but `RimWorld/Mods/SNLT` was a real directory copied on
11 August, three weeks before the assembly existed. What was on screen was
the `formatString` fallback doing exactly its job. The values were only
wrong in the sense of being the wrong feature, which is the hardest kind of
wrong to notice.

Two lessons worth keeping. A graceful fallback hides the failure it degrades
from, so **verify a new feature by a reading only the new code can produce**,
not by the absence of errors. And the deployed copy is part of the test
setup: check what the game is loading before trusting what it shows.

The stale copy was moved out of `Mods/` rather than deleted in place —
leaving it there would have created a duplicate `packageId` conflict with
the junction.

### Gameplay idea parked: the alphabeaver as a consumer

**No gameplay change was made and none is planned in this mod.** The
alphabeaver's `baseHungerRate` of 3.0 is untouched; only the labor
*accounting* changed.

But the observation that produced this fix is worth keeping for the
gameplay layer. An alphabeaver is a pure consumer: it converts a colony's
standing timber into nothing the colony can use, at nearly twice a
thrumbo's appetite on a ninth of the body. The player's economic interest
is to kill it before it eats the trees, and the meat is incidental — that
is *defence of stock*, not production, and it is a different economic act
from harvesting.

The suite has nowhere to say that yet. A QoL feature could: surface which
map fauna are net consumers of colony resources and what they are costing
per day, so "clear the alphabeavers" becomes a legible economic decision
rather than folk knowledge. It fits the same shelf as the gated-information
mod below — information about one's own economy that the colony has to
work to obtain.

### Planned successor mod: gated economic information

A separate mod, deliberately not this one. Labor Content shows every figure
to every player for free; the successor makes economic information something
a colony has to *produce*.

- research and technology prerequisites before the figures are legible at
  all;
- an actively-worked station, in the shape of a research bench, whose work
  maintains the accuracy of the colony's financial information — so
  knowledge of one's own economy is itself a product of labor, and decays
  without it.

This is a gameplay mod and belongs after the Stage 1 runtime, not before it:
the thing it gates has to be dynamic before gating it means anything. Recorded
here so the design is not re-derived from scratch. It also pairs naturally
with Phase D — a colony that must labor to know its own costs is already
halfway to the class-consequences material.

---

## What vanilla RimWorld's economy actually does

The installed target is RimWorld **1.6.4871 rev590**.

Vanilla contains material trade transactions but not a persistent market
economy:

- `MarketValue` is authored or recursively calculated from input prices plus
  `workAmount × 0.0036` silver per tick;
- normal trade begins around 1.4× MarketValue when the player buys and 0.6×
  when the player sells, then applies negotiation, difficulty, and trader
  modifiers;
- settlement stock is randomly generated from `StockGenerator` XML rules;
- settlement stock is discarded and regenerated every 30 days;
- player sales enter the current temporary stock but do not affect later
  production, demand, capacity, or prices;
- settlements have no persistent population, consumption, industry, input
  requirements, wages, investment, or economic specialization;
- surface and deep deposits are locally finite, but scanners repeatedly create
  new opportunities;
- deep drills can fall back to effectively unlimited base stone.

Keep vanilla `MarketValue` separate from the future dynamic `MarketPrice`.
`MarketValue` also drives storyteller wealth and other balance systems, so
making it volatile by default would couple price bubbles to raid strength.

---

## Economy design decisions already made

### Four separate ledgers/concepts

Never collapse these into one number:

1. **Labor value:** socially necessary labor embodied in a commodity.
2. **Market price:** current exchange price.
3. **Surplus value:** living labor beyond the reproduced value of labor-power.
4. **Rent:** income from ownership of scarce or unusually productive natural
   conditions.

Money profit is also not identical to surplus value. A commodity can contain
surplus labor and fail to realize it during a glut.

### Market topology

Markets clear regionally. Planetary trade is possible but expensive,
capacity-limited, risky, and delayed.

This resolves the scale problem:

- a player colony can dominate its local market;
- the same output barely affects distant regions;
- price differences create arbitrage opportunities;
- arbitrage consumes route capacity and pushes prices toward convergence;
- roads, caravans, pods, gravships, danger, and faction access can matter.

There are no hard regional borders. Any trade is possible when the spread
covers freight and risk.

### Socially necessary labor

The planned operational definition is output-weighted labor per unit among
active, normally functioning producers. This is an **average** production
condition.

Rent and market price may instead depend on the **marginal** producer required
to satisfy demand. The UI must label the two reference points separately:

- labor value reference: average socially necessary conditions;
- price/rent reference: marginal supply conditions.

### Resource accounting

- renewable resources have sustainable flows and possible overuse;
- minerals use finite reserve tranches with different grades;
- depletion moves extraction toward higher-labor marginal reserves;
- differential rent belongs in the money/rent ledger, not labor value;
- vanilla infinite base-stone drilling must become a large explicit bedrock
  reserve or be labelled as an open external reservoir.

### Mod compatibility

Use a closed default. Auto-classify a modded good only when its mapping is
unambiguous. Otherwise it remains outside the simulated economy, retains
vanilla behavior, and is labelled **unmodelled commodity**. It must not silently
satisfy simulated material demand.

---

## Stage 0 implementation

Stage 0 is a dependency-free deterministic Python laboratory. It exists to
validate economic behavior before RimWorld runtime work.

Locations:

- `economy_lab/model.py` — market, region, producer, route, shipment, and
  ledger mechanics;
- `economy_lab/scenarios.py` — seeded scenarios;
- `economy_lab/__main__.py` — JSON scenario runner;
- `economy_lab/viewer/` — the browser viewer: `http.server` endpoints, one
  JSON document per cached run, a standard-library Markdown renderer, and a
  single page with hand-rolled SVG charts (docs/48, docs/49);
- `tests/test_economy_lab.py` — behavioral and accounting tests;
- `economy_lab/README.md` — current scope and commands;
- `docs/06-stage0-economy-lab.md` — short design note;
- `docs/07-accounted-input-predictions.md` — forecasts, recorded before the fact;
- `docs/08-accounted-input-design.md` — process-model decisions and alternatives;
- `docs/09-accounted-input-results.md` — what the forecasts got wrong and why.
- `docs/10-upstream-observation-results.md` — upstream metrics, hysteresis
  investigation, and observation limits.
- `docs/11-upstream-production-control.md` — demand-control decision and
  rejected alternatives, recorded before implementation;
- `docs/12-upstream-production-control-results.md` — complete 53-metric delta
  table and acceptance rationale;
- `docs/13-cost-floor-and-investment-design.md` — cost floor, construction-fund
  investment, and buffer-deficit investment decisions;
- `docs/14-cost-floor-and-investment-results.md` — 53-metric comparison,
  prediction scorecard, convergence verification;
- `docs/15-resource-reserves-design.md` — finite reserves, grade depletion,
  marginal extraction cost, and differential rent decisions;
- `docs/16-resource-reserves-results.md` — prediction scorecard, depletion
  scenario timeline, permanently displaced inventory explanation;
- `docs/17-labor-power-and-surplus-design.md` — the wage relation: subsistence
  basket, labor supply, surplus ledger, treatment of the old unit cost, and
  the exact-stationarity floating-point engineering;
- `docs/34-history-detail-design.md` — history as an optional output,
  and the claim about what reads it that turned out to be false;
- `docs/36-capital-goods-sector-design.md` — Department I, and the finding
  that the model's six authored machines were already bills of materials;
- `docs/38-capacity-depreciation-design.md` — capacity falls only where a
  replacement failed, and why shedding all idle capacity has no rest point;
- `docs/39-capacity-depreciation-results.md` — a loss-making sector is
  disciplined rather than deleted, and the third accounting mismatch;
- `docs/40-recreation-in-the-basket-design.md` — the workers' basket holds
  the workers' own product, and why the quantity is swept not calibrated;
- `docs/41-recreation-in-the-basket-results.md` — basicness is binary, its
  economic weight is not, and a correction to how docs/37 read its own
  biggest result;
- `docs/42-absolute-rent-design.md` — Marx's condition for absolute rent as
  something the model can test rather than assume;
- `docs/43-absolute-rent-results.md` — it holds exactly without fixed
  capital and breaks with it; the bound is 75.7% of chemfuel's value;
- `docs/37-capital-goods-sector-results.md` — six predictions right, one
  wrong by sixteen, and 89.6% of the fixed capital that moves nothing;
- `docs/35-history-detail-results.md` — memory flat at ~60 MiB instead
  of 3.8 GB over a run, and the material ledger stopped reading its own
  report to find its opening stock;
- `docs/32-scale-test-design.md` — the size question, the budget fixed
  before measuring, and the depth histogram that shaped the whole test;
- `docs/33-scale-test-results.md` — linear after one method changed,
  memory as the architectural failure, and the value solve validated at
  447 commodities;
- `docs/30-turnover-design.md` — profit charged against capital
  advanced rather than consumed, turnover read off each commodity's
  own inventory life, and the correction of `docs/29`'s envelope
  recorded before measuring;
- `docs/31-turnover-results.md` — the rate is 1.17 per day and the old
  number is the gross markup; realized turnover is 56.8 days because
  the final product's stock is in no cost flow; three sections that
  are corrections rather than results;
- `docs/28-enlarged-subsistence-basket-design.md` — clothing and
  medicine from the closed analysis, the powered tailoring bench that
  makes chemfuel basic, and the prediction that this would *not* be
  enough, recorded before it was measured;
- `docs/29-enlarged-subsistence-basket-results.md` — every ratio built
  on v falls 30% and the value rate of profit 2%; the rank-one identity
  breaks; and the constraint is RimWorld's productivity, not the
  bundle;
- `docs/26-prices-of-production-design.md` — the classical eigen-system,
  the physical wage closure, the omission of fixed capital, and the
  hand-derived predictions recorded before any code existed;
- `docs/27-prices-of-production-results.md` — meals as the only basic
  commodity, the corn-model profit rate, the aggregate invariance
  failure, and why the subsistence basket is now a prerequisite;
- `docs/25-stage0-arc-summary.md` — the narrative summary of the Stage 0
  arc to the scale test: what each layer measured, the three
  thesis-relevant results, the wrong predictions, and the standing caveat
  on every ratio built on v;
- `docs/44-phase-a-arc-summary.md` — the continuation, covering docs/36 to
  docs/43. Sixteen predictions right and seven wrong; the four times a
  ratio measured in one accounting was quietly reused in another; and why
  the exactly-zero equilibrium requirement is the most productive
  constraint in the project;
- `docs/23-constant-capital-and-the-overhead-design.md` — fixed capital,
  the reclassification of the operating overhead, and the c/v/s ledger
  decided in advance;
- `docs/24-constant-capital-and-the-overhead-results.md` — the overhead
  measured as the authored-price wedge, and surplus produced against
  surplus realized;
- `docs/21-competitive-transmission-design.md` — the cost-aware price
  anchor, cost-weighted order allocation, and the cost-competition
  scenario decided in advance;
- `docs/22-competitive-transmission-results.md` — the value/price contrast,
  transmission strength, and the overhead residual named as the next
  structural problem;
- `docs/19-endogenous-labor-values-design.md` — the value equation, the
  iterative solve, output-weighted social scope, and the technique-change
  scenario decided in advance;
- `docs/20-endogenous-labor-values-results.md` — validation against the
  closed analysis, relative surplus value, and the value/price divergence;
- `docs/18-labor-power-and-surplus-results.md` — s/v and its determination,
  prediction scorecard, the glut-as-layoff finding, wage-push non-propagation.

Commits:

- `54d88ce` — Add deterministic Stage 0 economy laboratory
- `d284af9` — Report Stage 0 shock extrema
- `5ae57f7` — Freeze Stage 0 behavior before input-output production
- `f2c490c` — Add Stage 0 parameter sensitivity harness
- `cae1ba2` — Record pre-process behavioral predictions
- `863ee42` — Record accounted-input design decisions before implementing
- `f52fcd0` — Replace free production with accounted input-output processes
- `57b05ed` — Add process-level material-balance tests and input-shortage scenario
- `98ae17e` — Record accounted-input results
- `e2a7c43` — Freeze newly observed upstream behavior
- `097e40c` — Document the upstream hysteresis control bug
- `cbeb720` — Decide damped upstream replenishment control
- `c028cd6` — Add damped demand-led production planning
- `3f9c20b` — Record demand-led production deltas
- `05996ae` — Refresh baseline for demand-led replenishment
- `a1e95db` — Record long-run producer-loss convergence
- `a3fcfe7` — Record cost-floor and investment design decisions
- `e0e3dc7` — Add cost floor: producers pay for inputs via effective unit cost
- `e513b0e` — Make capacity investment consume silver
- `9f9825b` — Add buffer-deficit investment motive
- `9867014` — Record cost-floor and investment results
- `faa554b` — Refresh baseline for cost floor and buffer investment
- `34bf3ba` — Record resource reserve and differential rent design decisions
- `6eed091` — Add finite resource reserves with grade depletion and differential rent
- `aa22edd` — Add depletion scenario and reserve tests
- `d640485` — Record resource reserve results
- `13ec465` — Record labor-power and surplus ledger design decisions
- `4e923fd` — Add wage-relation machinery: worker cash, basket, labor pool, surplus ledger
- `27af376` — Wire the wage relation into the circuit: meals, wages, and the surplus ledger
- `5985878` — Record labor-power results: nine of fifty-three metrics moved, s/v is 38.344
- `ecf757c` — Refresh baseline for the wage relation
- `1b74e6d` — Freeze newly observed labor and subsistence quantities
- `0c5bbf6` — Record endogenous labor value design decisions
- `9426caf` — Solve labor values endogenously from the process graph
- `fc4e06d` — Add technique-change scenario and endogenous value tests
- `36ac2a3` — Freeze ten newly observed labor value quantities
- `c3db687` — Record endogenous labor value results
- `a475152` — Record competitive transmission design decisions
- `a9c3016` — Part A: the price anchor reads cost
- `9826489` — Part B: the order book goes to the cheaper producer
- `577c869` — Refresh baseline for competitive transmission
- `213d1cd` — Freeze ten newly observed competitive transmission quantities
- `77c3078` — Record competitive transmission results
- `87ac0cc` — Record constant capital and overhead design decisions
- `7bd916c` — Fixed capital transfers its value to the product
- `83a780a` — Add the value ledger: constant capital and the price wedge
- `73d115a` — Refresh baseline for fixed capital
- `7102ca4` — Freeze sixteen newly observed value ledger quantities
- `1f48794` — Record constant capital results

### Current vertical slice

The model has a four-commodity circuit, two regional markets, and one
expensive planetary route:

```
chemfuel ──┬──> psychoid farm ──> psychoid leaves ──> drug lab ──> yayo
           └────────────────────────────────────────────^
provisioners ──> meals ──> workers ──> labor-power ──> every producer
```

Meals are the subsistence commodity (MealSimple: reference 15, 305 embodied
ticks); the provisioners' raw-food feedstock sits outside the boundary like
chemfuel's organic inputs.

It supports:

- accounted input-output production: producers own a `Process` and must source
  real inventory; one that cannot is rationed, not subsidised;
- **cost floor**: producers' effective unit cost includes input prices at
  current regional rates, driving the utilization curve; the drug lab
  curtails on cost before running out of physical inputs;
- demand-led production planning: wanted output follows current final and
  productive outflow plus a damped correction toward material stock targets;
- daily production and price-sensitive consumption;
- persistent regional inventory and cash;
- damped local price formation from stocks and unmet demand;
- costly, delayed, capacity-limited arbitrage;
- destruction of productive capacity, upstream or downstream;
- **construction-fund investment**: capacity investment consumes silver from
  the regional pool at `construction_cost_multiplier × effective_unit_cost`
  per unit of daily capacity;
- **buffer-aware investment**: when a commodity's stock is persistently below
  target and surplus capacity cannot close the gap within
  `buffer_refill_horizon_days`, additional capacity is built;
- **finite resource reserves**: extraction producers draw from a bounded
  regional endowment with ordered grades; when the cheapest grade exhausts,
  the marginal cost rises and the utilization curve responds;
- **differential rent**: the cost advantage of infra-marginal regions over
  the most expensive active extractor, tracked as a separate quantity in the
  ledger (not collapsed into labor value or profit);
- **the wage relation**: workers are paid the subsistence basket (2 meals)
  at current regional prices; the wage enters effective unit cost through
  the cost-floor machinery; silver cycles producer → wage → worker → basket
  purchase → producer revenue and conserves exactly;
- **a fixed regional labor pool** with pro-rata rationing when planned
  labor exceeds it (never binding in the seeded scenarios);
- **the surplus ledger**: living, necessary, and surplus labor in
  work-ticks per region, observational, with the silver wage bill and
  basket shortfall recorded beside them — money profit is not surplus
  value, and the money wage is not necessary labor;
- **fixed capital that transfers value**: each sector carries its real
  RimWorld building (`DrugLab`, `HydroponicsBasin`, `BiofuelRefinery`,
  `ElectricStove`) in both silver and embodied labor, depreciating by use
  over a service life. This repairs the omission `FINDINGS.md` recorded in
  vanilla — where fixed capital transfers nothing — and measures it as
  0.353% of constant capital;
- **the value ledger**: c (circulating plus fixed), v, and s in work-ticks,
  with the organic composition and the value rate of profit. A third
  closing identity beside material and silver: value of output = c + v + s;
- **the price decomposition**: every unit's price split into inputs, wages,
  capital consumed, and the **unattributed wedge** — the gap between
  RimWorld's authored price level and anything the model can account for.
  Surplus is reported as two readings that name their assumption, never as
  a single number;
- **a cost-aware price anchor**: the anchor moves with the sector's
  output-weighted average cost relative to its seeded cost, blended by
  `competitive_price_intensity` (default 0.5, and 0 restores the
  authored-reference anchor exactly). Upstream cost now propagates to
  downstream prices, which `docs/16` recorded as impossible;
- **cost-weighted order allocation**: a commodity's order book is shared
  among its producers by `(cost/cheapest)^-epsilon`, capped by each
  producer's own limit, with the residual redistributed by water-filling.
  `competitive_share_elasticity = 0` is a bit-exact no-op;
- **endogenous labor values**: transferred labor plus living labor per unit
  of output, solved from the process graph by iteration (so a cyclic graph
  is answerable and a non-productive one fails loudly), aggregated as total
  labor over total output across active producers. Per-region individual
  values sit beside the social value, which is where the average/marginal
  distinction becomes visible. `Commodity.labor_value` keeps the authored
  `FINDINGS.md` figure, untouched, for comparison;
- explicit commodity and silver balance checks, with productive consumption
  booked separately from final consumption, investment spending and reserve
  depletion tracked.

### Process-model decisions — read before changing

`docs/08-accounted-input-design.md` records each choice and its alternatives.
The load-bearing ones:

- **joint products are apportioned by mass**, not by value, because value
  apportionment would be circular in a laboratory whose purpose is to let
  prices form from material conditions. Implemented and unit-tested; no current
  process actually has a byproduct;
- **partial input availability is proportional** — 60% of inputs means 60% of
  output. `all_or_nothing` exists as a parameter. Proportional is the default
  because a regional producer is an aggregate of many small runs, and because a
  discontinuity here would manufacture limit cycles that look like economic
  results;
- **production is simultaneous** against opening stock, so results do not
  depend on producer list order. Cost: one day per stage of propagation delay;
- **contention is pro-rata by requirement**, single pass. A producer throttled
  by another input leaves slack unallocated that day; the slack stays in
  inventory, so nothing is destroyed and the ledger closes;
- **inventory targets scale by throughput demand** (final plus derived).
  Without this, intermediate goods would have a target of zero and collapse to
  the price floor;
- **freight goes to the widest spread first**, not alphabetically.

Per-unit ratios and reference prices are read from RimWorld defs. One link is a
flagged stylization: vanilla drug labs and psychoid fields do not consume
chemfuel. It is there because the circuit needs a commodity consumed by more
than one producer, and contention is where accounting bugs hide.

**Cost floor and investment decisions** are in
`docs/13-cost-floor-and-investment-design.md`. The load-bearing additions:

- **effective unit cost includes input prices**: `Producer.unit_cost` is now
  operating overhead only; `effective_unit_cost(prices)` adds inputs at
  current regional prices. The drug lab's operating overhead is zero (its
  prior 14.0 was entirely consumed by the 15.66 input cost);
- **investment consumes silver**: `construction_cost_multiplier` (default 60)
  days of effective cost per unit of daily capacity, deducted when
  commissioned. If the region cannot afford it, the project scales down;
- **buffer-deficit investment**: when stock is below target and surplus
  capacity cannot refill within `buffer_refill_horizon_days` (default 60),
  additional capacity is built. The signal is proportional, not threshold;
- **input purchases are internal**: the silver payment for inputs stays within
  the regional pool (the producer buys from its own region). The behavioral
  effect comes through the utilization curve seeing a higher cost, not through
  a silver movement between entities.

**Resource reserve and rent decisions** are in
`docs/15-resource-reserves-design.md`. The load-bearing additions:

- **regional reserves with ordered grades**: each region has a
  `ResourceReserve` per extraction commodity with grade tranches ordered
  cheapest first. All extraction producers in a region share the same reserve;
- **dynamic marginal cost**: each day, extraction producers' `unit_cost` is
  updated to the marginal grade's cost before the utilization curve is
  evaluated. The cost floor machinery picks this up with no API change;
- **reserve rationing**: when total wanted extraction exceeds remaining
  reserve, all extraction producers are scaled down pro-rata;
- **differential rent**: the cost advantage of infra-marginal regions over
  the most expensive active extractor, accumulated in the ledger per commodity.
  Rent is observed, not transferred;
- **reserve depletion tracking**: `Ledger.reserve_depletion` equals production
  for extraction commodities (a testable accounting identity).

**Wage-relation decisions** are in `docs/17-labor-power-and-surplus-design.md`.
The load-bearing additions:

- **labor vs labor-power**: labor is the activity (a cost coefficient);
  labor-power is the commodity a wage buys, valued at its reproduction cost.
  Surplus value is only computable because the two are separate;
- **the wage is additive to effective cost**: the old operating overheads are
  reinterpreted as non-labor overhead. Splitting a wage out of them is
  numerically impossible (the drug lab's overhead is zero against 350 ticks
  of labor); the fat pre-wage margins implicitly contained the unpaid wage
  fund, and making labor-power a paid commodity moves that portion from
  measured profit into cost. The loud check is at seeding: any producer
  pushed below full utilization at reference prices raises;
- **wages today, bread tomorrow**: worker basket demand lags employment by
  one day, keeping the planning fixed point unchanged;
- **exact-stationarity engineering**: employment quantized to a 2^-20
  worker-day grid, power-of-two basket (2 meals) and provisioning capacity
  (1.0/day), and seeding at the exactly-repeating quantized fixed point.
  This is why the four-commodity equilibrium reports a price range of
  exactly zero rather than 1e-13;
- **s/v is closed-form at this stage**: (24000 − 610)/610 = 38.344, set by
  the working day and basket parameters plus the meal's embodied labor.
  It becomes emergent only with endogenous labor values, wage bargaining,
  or an endogenous basket — all deliberately later.

### Current calibrated behavior

- equilibrium remains exactly stable for four in-game years, now for four
  commodities including meals, with the wage circuit running daily;
- the equilibrium wage is **30 silver per worker-day**, employment is
  **0.314 worker-days/day** per region, and the rate of surplus value is
  **38.344** (labor-time ratio, constant through every shock);
- a glut equal to 25% of annual regional yayo consumption lowers the local
  price from 21 to **14.368** (shallower again — the wage raised the drug
  lab's curtailment threshold);
- the distant region only falls to **20.464**;
- arbitrage exports **11 units** before the spread closes;
- destroying 60% of regional capacity raises the price to **38.630**;
- replacement capacity restores at least 80% of baseline supply within the
  four-to-eight-quadrum target;
- post-shock upstream buffers refill to target rather than persisting as
  scar tissue (converges by day 400, identical endpoint to the pre-wage
  model);
- destroying 70% of one region's provisioning triples the meal price and
  the wage, records a 9-meal basket shortfall and forced worker savings,
  and rebuilds through ordinary investment — without moving yayo or leaf
  prices at all (wage share of cost is too small to curtail);
- all 183 tests pass;
- commodity and silver residuals close to floating-point zero for all four
  commodities, including investment spending and the wage circuit;
- identical inputs reproduce identical histories.

These are provisional gameplay targets, not empirical claims about real-world
elasticities.

### History of behavioral changes

**Accounted-input production** (`docs/09`): moved zero of thirteen original
metrics because the material constraint never binds at 20-day cover, capacity
entry was free, and gluts cannot be damped by an input constraint. But it
exposed upstream effects invisible to the yayo-only metrics: permanent
hysteresis and a 74% leaf price crash on downstream capacity loss.

**Demand-led production control** (`docs/12`): moved 39 of 53 metrics.
Resolved the glut hysteresis. Upstream prices stay at reference throughout the
glut. Producer-loss terminal values shift because investment targets follow
throughput demand.

**Cost floor and investment** (`docs/14`): moved 16 of 53 metrics. The cost
floor tightened the drug lab's margin (effective cost 15.66 vs prior 14.0),
causing the glut trough to shallow (14.34 → 14.36), recovery to accelerate
(11 → 9 days), and arbitrage volume to drop (12.38 → 11). The cost channel
pre-empts material rationing in the input-shortage scenario: the drug lab
curtails on cost before running out of leaves. Buffer-aware investment
resolves the post-shock upstream scar — prices return to reference by day 400
with stocks at their enlarged targets.

**Resource reserves and differential rent** (`docs/16`): moved zero of 53
metrics. The reserve infrastructure is invisible to existing scenarios (default
100,000-unit reserves at current operating overhead). The new depletion
scenario exercises grade transition: Dust Basin's cheap chemfuel grade (600
units) exhausts at day 100, marginal cost doubles, chemfuel price rises from
2.30 to 3.33. Downstream prices (leaves, yayo) are unaffected — the chemfuel
input share is too small (0.2/yayo, 0.05/leaf) for a 44% chemfuel price
increase to push downstream margins into curtailment. Green River earns
1,816 silver in differential rent over 300 days. All ledgers close.

**The wage relation** (`docs/18`): moved nine of 53 metrics, all through the
one designed channel (the wage in effective unit cost). The glut trough
shallowed (14.356 → 14.368) and half-recovery quickened (9 → 8 days);
producer-loss day-210 transients drifted 1–2% while the converged day-400
endpoint is identical. Equilibrium, the producer-loss peak, arbitrage, and
every upstream extremum are exactly unchanged. New findings: the glut is a
mass layoff (employment collapses to 0.0002 worker-days on day 62) that
subsistence production absorbs with a perfectly flat meal price; the
producer-loss cycle produces the first real-wage dynamics (wage 23.40 →
32.80); and wage-push does not propagate at this calibration because the
wage is ~2.7% of the drug lab's cost — the labor-side counterpart of the
chemfuel input-share finding in docs/16.

The `input-shortage` scenario exercises the material constraint: 70% of Dust
Basin's psychoid fields destroyed, leaf price up 2.6× and yayo up 1.66×.
With the cost floor, the drug lab curtails smoothly through cost rather than
waiting for physical leaf exhaustion.

Run:

```text
python -m unittest discover -s tests -v
python -m economy_lab all
python -m economy_lab input-shortage
python -m economy_lab depletion
python -m economy_lab subsistence-shock
python -m economy_lab technique-change
python -m economy_lab cost-competition
python -m economy_lab.baseline
python -m economy_lab.sensitivity
```

The sensitivity sweep has **not** been re-run since accounted inputs landed;
`sensitivity_results.csv` and `sensitivity_ranking.txt` describe the free-
production model. Re-run it once the model stabilizes, and expect the new
process ratios, derived-demand price rule, and exposed `replenishment_rate` to
change the ranking. The committed stale output covers 31 parameters; a fresh
run will include 32.

### Behavioral observation checkpoint

`economy_lab/behavior_baseline.json` freezes 65 current behavioral metrics:
thirteen final-good observations, forty upstream observations, and twelve
labor/subsistence observations. `python -m economy_lab.baseline` re-runs the
scenarios and prints reference, current value, absolute delta, and percentage
delta. It is deliberately a report rather than a pass/fail test; the 51-test
suite remains the authoritative invariant checks. Replace the reference only
with `--write-reference` after an understood behavioral change, and say why
the numbers moved in the commit message.

Current frozen headline metrics include:

- local glut trough: **14.367961** on day 66;
- distant glut trough: **20.464413** on day 80;
- local half-gap recovery: **8 days / 0.533 quadrums**;
- arbitrage exports: **11 units**;
- producer-loss peak: **38.630290** on day 119;
- 80% capacity recovery: **75 days / 5 quadrums**;
- equilibrium price range: **0** in both regions, all six commodities.

Current upstream headline observations include:

- glut leaf settlement: **1.900000 / 1,600 units**;
- glut chemfuel settlement: **2.300000 / 120 units**;
- producer-loss leaf trough: **0.693449** on day 70;
- producer-loss chemfuel trough: **1.918998** on day 69;
- producer-loss leaf terminal: **2.467308 / 1,454.371** (day 210, still in
  buffer-rebuild transit; converges to 1.900 / 1,891 by day 400);
- producer-loss chemfuel terminal: **2.917596 / 104.624** (same — converges
  to 2.300 / 151 by day 400).

Labor and subsistence observations (frozen at `1b74e6d`):

- equilibrium employment: **0.314065 worker-days/day**; wage **30 silver**;
- rate of surplus value: **38.344367** (labor-time ratio);
- meal settlement: **15.000000 / 12.751667**;
- glut employment trough: **0.000202** on day 62, meal price range **0**;
- producer-loss employment trough: **0.058332** on day 62; meal price
  cycles **11.697630 – 16.398671**.

The former glut hysteresis was a **control-law bug**, not a capacity reallocation
or ledger leak. It is resolved by the design in `docs/11`: planned output follows
intended outflow plus a 10% daily correction toward the existing material stock
target. The mutually dependent order plans converge deterministically from the
day's opening state, so production remains simultaneous. Leaves now stay at
1,600 and chemfuel at 120 throughout the glut, both at reference price.

The cash cost floor (`docs/13`, `docs/14`) does **not** replace this control.
Material planning answers how much output is wanted; the cost floor answers
whether the plan is profitable. Actual production is limited by both — the
minimum of what the demand-led plan requests and what the utilization curve
(now informed by input costs) allows.

Two interpretation notes:

- glut upstream extrema are degenerate by design: price peak and trough are
  both the reference price on day 61, and stock peak/trough both equal the
  unchanged buffer. They mean "no upstream excursion," not a timed trough;
- extending producer loss to day 660 now shows full convergence: leaves
  settle at **1.900 / 1,891** and chemfuel at **2.300 / 151**, both at
  reference price with stocks at target. The enlarged stocks reflect
  additional installed capacity from buffer-rebuild investment. The former
  permanent buffer scar (`docs/12`) is resolved.

Arbitrage is currently single-commodity by calibration, not design. Standard
freight is **3.85** after risk markup while the glut's widest intermediate spread
is about **0.2**. Falling freight or rising upstream volatility can therefore
switch multi-commodity arbitrage on abruptly, with goods competing for route
capacity.

Recovery-day metrics are quantized to daily threshold crossings. Add a
continuous complement—preferably area between the price path and baseline over
a fixed window—in a later observation session, without changing the existing
metric semantics.

`python -m economy_lab.sensitivity` deliberately runs a one-at-a-time ±10%
sweep over 31 exposed calibration parameters. It writes:

- `economy_lab/sensitivity_results.csv` — 806 detailed parameter/output rows;
- `economy_lab/sensitivity_ranking.txt` — parameters ranked by their strongest
  normalized output response.

The sweep did not reveal one overwhelmingly dominant coefficient. Daily demand
and productive capacity tied for the strongest response through arbitrage
volume; reference price and Dust Basin unit cost followed through a quantized
two-day movement in glut recovery. Investment timing and fraction most strongly
control capacity recovery. Integer scheduling makes the investment-interval
response phase-sensitive rather than smooth.

Twelve parameters produced no movement in the captured outputs at ±10%:
expectation smoothing, initial cash, investment margin threshold, labor value,
all three loss-route settings, both price clamps, River unit cost, speculative
inventory limit, and unmet-demand price pressure. These are scenario-local
findings, not proof that the parameters are globally irrelevant.

The sensitivity refactor exposed previously hard-coded coefficients through
`ScenarioParameters` while preserving every default. The baseline report
remains all-zero after the refactor and all eight tests pass.

Predicted changes from accounted-input production are frozen in
`docs/07-accounted-input-predictions.md`. The expected pattern is a shallower,
shorter glut; a higher, longer producer-loss shortage; and near-stationary
equilibrium. Compare actual changes against the prediction, but do not tune the
new model merely to make the forecast come true.

---

## Stage 1 runtime shell

Stage 1 has begun as an isolated read-only RimWorld 1.6 mod in `economy_mod`.
Commit `6794dfc` added the shell and `585bf09` the first real content:

- a persistent `EconomyWorldComponent` with a 60,000-tick daily cadence;
- a **deterministic profile per settlement** — faction, tile, biome,
  hilliness — read off the generated world, with **regions** assigned by a
  faction's first appearance in tile order;
- those profiles persisted, **re-derived on load and compared**, with the
  result shown in the tab. A mismatch means the derivation depends on state
  that is not in the save, which is invisible otherwise and fatal once the
  Stage 0 model is integrated;
- a read-only Economy main tab, ordered between Animals and Wildlife, now
  listing the profiles in a scrolling table;
- explicit UI copy that vanilla prices remain unchanged;
- no Harmony, no gameplay mutation, and **no `Rand`** — variation comes from
  hashing stable identity through the same SplitMix64 mixer
  `economy_lab/scale.py` uses, because `Rand` is global mutable state shared
  with the game's own generation.

`economy_mod/Source/verify.py` checks all of that against the *built
assembly*, the way `mod/Source/verify.py` does for Labor Content: the four
types the defs name exist, `Rand` and Harmony are absent, no
gameplay-writing API is on the binding surface, and the surface is exactly
the 30 expected symbols. Schema version is 2; a schema-1 save has no
profiles node and loads clean.

Runtime verification on RimWorld 1.6.4871 rev591 passed:

- the assembly built with zero warnings;
- the mod loaded beside Labor Content with no XML or assembly errors;
- the tab appeared and initially observed 105 settlements;
- after the player settlement appeared it observed 106;
- crossing one in-game day incremented the economy counter from 0 to 1;
- `Autosave-4.rws` serialized `completedDays=1`,
  `lastProcessedTick=60000`, and `observedSettlementCount=106`;
- all eight deterministic Stage 0 tests still pass after adding the runtime
  project.

Save serialization is confirmed. A deliberate save/reload read-back test has
not yet been completed, so do not report reload persistence as verified.

**That verification is now stale in two ways**, and both need a human at the
game. The "loaded beside Labor Content with no assembly errors" line was run
when Labor Content was XML-only; it carries its own assembly since `b3727f1`,
so the co-load needs redoing. And `585bf09` added the profiles, the regions
and the reload check, none of which has been seen running.

**What to test in game, in one sitting:**

1. **Co-load.** Both mods enabled together, new colony, no red errors. The
   startup log should carry one line naming the settlement and region counts
   and the determinism check.
2. **The tab.** Settlements listed with a region, faction, tile, biome and
   hilliness, grouped by region. Region numbers should be small integers
   with no gaps.
3. **Save and reload.** The tab's "Reload determinism" row should read
   `reproduced N/N on reload`. Anything else is the finding, and the log
   will name the first profile that disagreed.
4. **A day passing.** "Economy days simulated" increments, and the
   determinism row does *not* change (it is set at load, not per day).
5. **An old save.** A save written before `585bf09` should load clean and
   report `nothing saved to compare` rather than erroring.

The build toolchain is:

- .NET SDK 8.0.424 — at `C:\Users\PintS\Documents\Codex\tools\dotnet-sdk-8`
  on the Windows machine, at `~/.dotnet` on the Mac;
- target framework `net472`;
- official `Microsoft.NETFramework.ReferenceAssemblies` 1.0.3 build package,
  which is what makes `net472` a valid target on macOS without Mono;
- direct references to RimWorld's shipped managed assemblies.

The user explicitly approved installing these required build dependencies.

The mod is development-linked into RimWorld's `Mods` folder as
`SocialProductionEconomy`. The build command and overrideable game path are
documented in `economy_mod/README.md`.

### The project is now cross-platform (2026-08-26)

The repository is synced through OneDrive and is worked on from both a
Windows machine and a Mac. Everything needed to build, verify and run both
mods exists on both. What had to change:

- **`Economy.csproj` and the new `LaborContent.csproj` condition on the OS.**
  The managed assemblies are under `RimWorldWin64_Data/Managed` on Windows
  and `RimWorldMac.app/Contents/Resources/Data/Managed` on macOS, and the
  default Steam install path differs too. All paths use forward slashes,
  which MSBuild accepts on Windows and which are the only separator on Unix.
  Both projects now fail with a named error if the assemblies are missing,
  instead of a wall of unresolved types.
- **`mod/Source/build.sh` no longer calls `csc.exe`.** See the Labor Content
  build section above; the short version is that it uses the SDK now, is
  reproducible, and runs on either platform.
- **`verify.py` needs a venv on macOS.** `cli_reader.py` imports `pefile`,
  and Homebrew's Python refuses installs (PEP 668). `.venv/` is gitignored;
  `python3 -m venv .venv && .venv/bin/pip install pefile` is the whole setup.

**Line endings are an open trap.** The Windows checkout has
`autocrlf=true`, so OneDrive delivers CRLF files to a Mac that has no
`.gitattributes` — and `git status` there shows **every text file in the
repository as modified** with zero real changes. `git diff
--ignore-cr-at-eol --stat` is empty, which is how to tell. Do not mistake
this for uncommitted work, and do not "resolve" it by committing the
churn. The fix is a `.gitattributes` with `* text=auto` plus a
`git add --renormalize .`, in its own commit, on a clean tree.

**The installed game differs between machines**: the Windows machine is on
RimWorld 1.6.4871 **rev590/591**, the Mac on **rev595**. All five
expansions are present on both. Any in-game observation should record which.

This is intentionally a runtime shell, not integration of the incomplete
Stage 0 production model.

### The port has started: the value solve, to the bit (2026-09-04)

`economy_mod/Source/Economy.Core/` is a library with no RimWorld reference,
built for `net472` and `net8.0`, holding `_update_labor_values` ported line
by line — including CPython's compensated `sum()` where the laboratory
uses it. A `net8.0` harness (`Economy.Core.Check`) checks it against
fixtures `economy_lab/fixtures.py` writes from real economies, and every
fixture reproduces **to the bit**: 1,494 values, zero ulps, the
647-commodity solve in 4 ms (`docs/54`). The determinism contract for the
rest of the port is therefore *transliterate, do not translate*. The
library is not loaded by the game yet and `verify.py`'s surface is
unchanged; loading it needs a human at the game and a new expected
surface. `tests/test_port_fixtures.py` fails when the model moves and the
fixtures have not been regenerated.

### The port's second slice: the basket and the wage (2026-09-12)

`docs/72`, `docs/73`. `economy_mod/Source/Economy.Core/WageProblem.cs`
and `WageSolver.cs` hold the six wage readings and `_settle_labor`'s
non-cash path, transliterated; `Economy.Core.Check/WageCheck.cs` checks
them against `economy_mod/Source/Fixtures/wages/`, which
`economy_lab/wage_fixtures.py` writes from four real economies covering
every branch. The premium and the habitual standard are *inputs* to this
slice; the rules that move them are the next one.

**The C# has not been compiled.** The session that wrote it had no .NET
SDK and could not install one, so the claim is "written to the contract",
not "meets it". Its order and arithmetic were checked by re-implementing
the C# in Python and running it against the fixtures — 112 readings,
zero ulps — which checks the part most likely to be wrong and checks
nothing about whether it builds.

**Do this first, on a machine with the SDK:**

```
dotnet run --project economy_mod/Source/Economy.Core.Check
```

It now runs both fixture directories and returns non-zero if either is
not bit-exact. `Program.Comparison` and `Program.Compare` were widened
from `private` to `internal` so `WageCheck` could reuse them; that and
the two new files are the whole compile surface. Build it before
starting the next slice: two unbuilt slices stacked means finding a
compile error in the first while debugging the second.

One finding from the fixtures worth carrying to every later slice: a
fixture must record the *state a magnitude is computed against*, not only
the magnitude. `Ledger.add` accumulates and `region.cash -= bill`
subtracts from a large purse, so the same wage bill posts +13.326840677261316
to the ledger and moves the purse by −13.326840677254950. A fixture of
differences would have let the port agree with the fixture while
disagreeing with the model.

---

## Immediate next work

Steps 1–10 are **done**.

1. ~~Add `Process` definitions with material inputs, outputs, direct labor,
   capacity, and unit operating cost.~~
2. ~~Add at least three linked commodities.~~ Done as a forking circuit:
   chemfuel feeds both the psychoid fields and the drug lab.
3. ~~Require production to consume accounted inventory.~~
4. ~~Add process-level material-balance tests and an input shortage
   scenario.~~
5. ~~Make investment consume a construction fund; add cost floor and buffer
   investment.~~ Done: producers' effective cost includes input prices,
   investment costs silver, buffer deficits trigger proportional investment.
6. ~~Add finite resource reserves, grade depletion, marginal extraction cost,
   and differential rent.~~ Done: chemfuel synthesis draws from a regional
   reserve with ordered grades; differential rent tracked in the ledger.

7. ~~Add the local subsistence basket and wage labor.~~ Done: meals are the
   fourth commodity, workers are paid the basket at current prices, the
   surplus ledger separates living/necessary/surplus labor from the money
   wage bill, and the silver circuit closes. Hired-worker *contracts* (the
   player colony hiring outside workers) remain a Stage 1 gameplay concern.

8. ~~Propagate labor values endogenously through the process graph.~~ Done:
   values are solved by iteration, validated against the closed analysis
   (exact for the two input-free commodities, high by exactly the stylized
   chemfuel link for the two downstream ones), and the rate of surplus
   value is now an outcome. A technique change in the wage-goods sector
   moves it from 38.344 to 43.944 with the working day and the basket held
   fixed — relative surplus value, emergent (docs/20).

9. ~~Add competitive transmission from cost to price.~~ Done: the price
   anchor reads the sector's cost and the order book goes to the cheaper
   producer. The `docs/16` displaced-inventory artifact is resolved (the
   depletion buffer returns from 63.8% of target to 100%) and downstream
   cost-push exists for the first time. Two contrasting scenarios now
   separate value from price numerically: labor-saving moves value 12.7%
   and price 0.47%; capital-saving moves price 14.3% and value not at all
   (docs/22).

10. ~~Give the operating overhead an economic interpretation.~~ Done, and
    the answer is negative in a useful way: it is the gap between
    RimWorld's authored price level and anything the model can account
    for. Fixed capital — now implemented from the real building data —
    explains 0.05% of it; two-thirds of the upstream price remains
    unattributed. The wedge is reported under its own name, surplus is
    given as two readings that state their assumption, and the classical
    magnitudes are computable at last: organic composition 20.67, value
    rate of profit 1.77 (docs/24).

**Scope note:** for where these sit against the whole mod suite — the
runtime port and the gameplay layer — see "Distance to the full suite"
above. The scale question that section carried as its largest open risk is
**retired** (step 14); what replaces it is narrower and known.

11. ~~Prices of production.~~ Done as an observation, and the result is
    negative in a way that reorders everything behind it. The classical
    system solves — `p = (1 + r)Mp` with the subsistence basket folded
    into the input matrix — and the uniform profit rate comes out of the
    technique and the real wage with no authored price in the derivation.
    But **meals is the only basic commodity** in the circuit, so `r` is
    fixed by the wage good alone and reduces to a corn model:
    `r = 38.344`, which is the rate of surplus value arrived at from the
    price side. A gross markup of 39.34 then meets yayo's two-stage input
    chain twice, pricing it at **71.6×** its authored ratio to meals.
    Nothing is wrong with the arithmetic; the input to it is. Also
    measured: total price can be made to equal total value, and total
    profit is then 1.526× total surplus (docs/27).

    Nothing feeds back. Prices, costs and the order book are untouched and
    the frozen reference did not move by a digit.

12. ~~An enlarged subsistence basket.~~ Done, and it settled the question
    `docs/27` opened by answering it in the negative. Clothing
    (`Apparel_BasicShirt`, 1620 ticks) and medicine (`MedicineHerbal`,
    400) join meals, every figure from the closed analysis. Necessary
    labor rises from 2.5% to **3.6%** of the working day; s/v falls
    **38.30 → 26.71**, c/v **20.67 → 14.42**, and the value rate of profit
    only **1.768 → 1.733**, because `c` is fourteen times `v` either way.
    The uniform profit rate falls **38.34 → 24.62** and yayo's deviation
    from its authored price **71.6× → 38.7×** — halved, and still
    unusable (docs/29).

    Two structural gains beyond the numbers. The tailors' bench is
    powered, which makes **chemfuel a basic commodity** and breaks the
    rank-one identity that had kept `r` exactly equal to s/v; the model
    has reached the general Sraffa case, with a control scenario that
    restores the identity when the link is removed. And `docs/24`'s
    refusal to read the money/labor agreement for meals as evidence can
    be **retired**: with three goods in the basket that identity
    dissolves and the wage goods straddle the labor-time rate instead.

    **The caveat this was meant to remove is only partly removed, and the
    reason is a finding rather than a shortfall.** `r ≈ T / (basket
    labor) − 1`, and one provisioner's working day feeds **39.3 workers**
    on RimWorld's own numbers. A profit rate near 1 needs a basket
    embodying half a working day — 39 meals a day. The
    `generous_basket` scenario bounds it: an indefensible bundle still
    leaves s/v above eleven. The rate of surplus value this project
    reports is roughly the game's own.

13. ~~Turnover.~~ Done, and both of the project's rates of profit are now
    rates. Capital is advanced for one production period plus the
    commodity's own inventory life, so `p_i = (1 + r τ_i)(M_i · p)`. The
    price system's rate is **1.1726 per day** and the number `docs/26`
    through `docs/29` reported survives as the **gross markup**, 24.62.
    The value ledger gains a rate of profit on capital *advanced* —
    **0.0305 per day** — beside the flow ratio it has printed since
    `docs/23`, and the two differ by the realized turnover.

    **Uniform turnover moves no relative price.** `1 + rτ` is a scalar,
    so it rescales the rate and redistributes nothing; the invariance is
    asserted bit-exactly, which is why the uniform case is solved in
    closed form rather than searched for. Only *differential* turnover
    moves a price, and `perishable_meals` — RimWorld's simple meals rot
    after four days — lifts the rate to 2.08 and widens every deviation,
    yayo from 54 meals to 476 (docs/31).

    Realized turnover is **56.8 days**, not the 21 the price system
    assumes, because yayo is nobody's input: its finished stock is 63% of
    all commodity capital and appears in no cost flow. Take it out and
    the figure lands at 22.1.

    Also: a **third seeding defect** of the `docs/29` family — stocks were
    seeded from the global inventory target rather than the commodity's
    own, invisible while they were equal. Caught only because the
    stationarity invariant is exact rather than tolerance-based.

14. ~~The scale test.~~ Done in one session, and the answer is better
    than expected for a different reason than expected (docs/33).
    `economy_lab/scale.py` builds an economy of any size from the real def
    population; it runs **647 commodities across 100 regions**.

    **The architecture is linear**, in commodities and in regions, after
    one method changed: `throughput_demand` is O(producers) and was being
    called once per commodity inside a fixed point, so a day was
    O(commodities × producers) several times over. `throughput_demands`
    computes them all in one pass. 10.1× the commodities now costs 10.9×
    the time where it cost 22.5×.

    **CPU fails in Python and would pass in C#.** 22.3 s per simulated day
    at full scale against a 50 ms budget — but linear, and amortisable
    across a 60,000-tick day. A conservative 20× port lands under 20 µs a
    tick.

    **Memory fails architecturally.** `Economy.history` grows ~16 MiB per
    simulated day at full scale, 3.8 GB over a run. That is a design
    decision, not an implementation cost, and it is now on the critical
    path for the port.

    **Everything correctness-shaped held**, and one result came free: run
    at 647 commodities rather than four, the labor value solve reproduces
    the closed analysis's embodied labor **exactly** for all 447
    commodities the generator did not contaminate. `docs/20` validated it
    on four.

    Also found: the equivalence test for the new batch method caught a
    one-ulp divergence the reasoning had missed, because CPython's `sum`
    compensates its float error and a `+=` loop does not. The frozen
    reference did not notice — it rounds to six decimals — and the test
    did.

15. **Next — two small sessions, then the economics resumes.**

    *~~Reshape `Economy.history`~~* — done (docs/35).
    `record_history=False` and `history_every=k`, defaulting to today's
    behaviour, put the runtime's memory at a flat 54 MiB instead of 3.8
    GB over a run. The design's claim that nothing reads history back was
    wrong — `commodity_balance` took its opening stock from `history[0]`
    — and the opening stock is state now.

    *`_allocate_orders`* is now the largest single cost in a simulated day.
    The **bit-identical** part is done: the commodity grouping is hoisted
    out of the fixed point instead of rebuilt on every iteration, one-
    element sectors skip their sort, and `id()` calls halved from 191,796
    to 94,260 over three days. It bought little — the cost is per-sector
    dictionary construction, not the bookkeeping around it.

    **The remaining win is not bit-identical, and that is the decision the
    session has to make.** The overwhelmingly common case is a sector with
    one producer, where the whole water-filling apparatus reduces to
    `min(wanted, ceiling)` — except that the loop computes
    `remaining * w / total_weight` with `total_weight == w`, and
    `x * w / w` is not exactly `x` in floating point. A fast path would
    move results in the last bits, so it needs a design document that
    says whether that is acceptable and a reference refresh that explains
    the movement. It is not a refactor.

    Then the economics, unchanged in order:

    *~~A capital-goods sector (Department I)~~* — done (`docs/37`). Three
    commodities read off the game, seven bills that reproduce their
    machines to the tick, and fixed capital inside the price system at
    last. Two things to carry forward from it:

    The rate of profit is **0.518** per day, not 1.17. The prediction was
    a 3.4% fall and the answer was 55.80%, because I estimated the price
    system's share of fixed capital from the *value ledger's* 3.54%. They
    measure different advances. Any future number quoted from one
    accounting into the other deserves the same suspicion.

    **89.6% of the economy's fixed capital moves the general rate of
    profit by nothing.** Yayo holds 67.3% of it and psychoid leaves 22.3%,
    and both are non-basic. The whole collapse comes from the other tenth,
    a third of it from the stove behind the workers' meals. This rests
    entirely on yayo and leaves staying non-basic: **if any later scenario
    makes yayo an input to anything, check `r` first** — nine tenths of
    the fixed capital stops being inert and the rate moves a long way.

    *~~Capacity depreciation and mothballing~~* — depreciation and exit
    are done (`docs/39`); mothballing is not, and is named there. Three
    things to carry forward:

    **A loss-making sector is disciplined, not deleted.** Components shed
    `1/L` a day for 2,200 days, and then stopped — the contraction raised
    the price 19.8% while the maintenance bill fell thirtyfold, and they
    met at exactly the point where the margin covers the upkeep. Nothing
    in `_shed_capacity` knows about prices. The design predicted a cascade
    and got an adjustment.

    **The price system cannot see idle plant**, by a convention `docs/36`
    introduced and `docs/39` §5 finally states: `social_fixed_capital`
    reports the technique's coefficient at full utilization. So the plant
    the price system implies (17,007 ticks) is 6.8% below the stock the
    ledger holds (18,255). **If anything ever makes that read the
    installed stock, `r` becomes utilization-dependent and every profit
    rate reported since `docs/37` needs re-deriving.**

    **Exit is necessary but not sufficient** for the social labor value to
    migrate off a superseded technique. A superseded producer with a
    positive margin covers its maintenance and never sheds. The missing
    piece is a cheaper rival driving that margin down, which belongs with
    `cost_competition`.

    *~~Recreation in the basket~~* — done (`docs/41`), and it produced a
    **correction to how the project had been reading `docs/37` §4.**

    That finding — 89.6% of the fixed capital sits in non-basic sectors and
    moves the general rate of profit by 6e-13 — stands. What does not is
    the inference `docs/37` §8 drew from it in writing, that making those
    sectors basic would move `r` "a long way". It moves it 4.3%.

    **Non-basic is a veto; basic is only permission.** How much a sector's
    plant then weighs is set by its `K/cost` ratio, not by the size of its
    stock. A sector can hold two thirds of the economy's fixed capital, be
    basic, and still barely touch `r`. Watch for this shape of error
    elsewhere: a category flipping is not a magnitude changing.

    The sharpest number: at **one part in four thousand** of a yayo per
    worker-day, every commodity in the model is already basic and `r` has
    moved 0.07%. It is frozen as
    `recreation.production.profit_rate_at_epsilon` beside
    `basics_at_epsilon`, because the pair is the whole argument.

    *~~Wage deviations from the value of labor-power~~* — done
    (`docs/47`). A reserve-army rule: the wage premium follows the
    employment rate against its seeded reference, proportionally and
    damped, off by default. Three things to carry forward:

    **The wage moved and the value did not**, to one ulp — the value
    solve's output weights differ between two runs whose investment
    differs, so "identical" is 1.3e-16 and the metric freezes the gap.

    **A wage above value reaches prices through demand, not cost.** A
    7.8% premium moved the meal price 4.0%; the cost-push part is 0.43%
    and the rest is workers eating more. `docs/22`'s "wages barely reach
    prices" measured the cost channel on a wage that could not move in
    real terms; the real-wage channel is eight times larger for wage
    goods and does not exist for anything else.

    **The deviation is permanent under a permanent shock.** ~~No rule yet
    lets a sustained premium become the habitual basket.~~ Done
    (`docs/52`): the standard follows the premium on a fifty-day habit,
    upward only, and the value of labor-power rises 7.5% while the
    premium is unchanged. **Read `docs/52` §3 before quoting the
    eight-to-one ratio above**: most of that demand-channel price rise
    was an inventory target that never followed the standard.

    Other candidates: labor content of resource grades; habituation of
    the wage premium; credit and bankruptcy.

The sensitivity sweep has been re-run (`docs/45`), and the harness that
runs it was repaired first: five integer parameters were being perturbed
to floats and reported as "refused", four metric groups and two scenarios
ignored the perturbation, and two scenarios had no metrics at all. Nine
parameters were being reported inert that are not. The ranking is by
*reach* now — how many readings a parameter moves — because the
elasticity divided by near-zero baselines and put `daily_demand` on top
for moving one denominator. `meals_per_worker_day` and
`meal_capacity_per_day` did **not** refuse at ±10%: the exact-stationarity
engineering (docs/17 §7) re-solves the fixed point for any basket, so
that caution was out of date. The sweep is not a per-commit check; it is
about half an hour, and `capacity_exit()` is most of it.

Two safe tracks can now proceed independently:

1. In Stage 0, replace free single-output production with accounted
   input-output processes in the order above.
2. In Stage 1, generate deterministic settlement profiles and regional
   membership, persist them, and display them read-only. Do not run a claimed
   production economy or alter vanilla prices until the Stage 0 material
   circuit is credible.

Before any behavior change, run the baseline reporter once. After the change,
run it again and record the deltas before deciding whether to update the
reference. Run the sensitivity sweep deliberately after the model stabilizes;
it is not intended for per-commit testing.

---

## Known Stage 0 omissions

- ~~capital-goods costs for capacity investment~~ — done;
- ~~producers paying cash for their inputs~~ — done via effective unit cost;
- ~~labor value propagated endogenously through processes~~ — done;
  `Commodity.labor_value` deliberately keeps the authored `FINDINGS.md`
  figure and the solved values live on the `Economy` beside it, so the two
  can be compared rather than conflated;
- ~~competitive transmission from cost to price~~ — done (`docs/22`);
  transmission strength is now a measured quantity, and it is small for
  labor-saving change because wages are 2-4% of money cost;
- ~~competitive *exit*~~ — done (`docs/39`). Capacity falls by exactly the
  part of a day's wear a replacement did not make good; there is no decay
  rule and no exit rule. Off by default, because turning the money rule on
  shrinks Department I thirtyfold over sixty-six years. The result is that
  a loss-making sector is *disciplined*, not deleted: it sheds idle plant
  until the price rises to where the survivor pays for itself. Exit turns
  out to be necessary but **not sufficient** for social labor value to
  migrate to a superseded technique — a superseded producer with a positive
  margin covers its maintenance and never sheds. That needs a cheaper rival
  driving the margin down, which is `cost_competition`'s territory;
- ~~an economic interpretation for the `unit_cost` operating overhead~~ —
  done, and the answer is that it is the authored-price wedge (`docs/24`);
  it is now named and measured, but not removed, and removing it means
  abandoning `MarketValue` as the price anchor;
- ~~a capital-goods sector~~ — done (`docs/37`). Steel, wood and components
  are produced; every sector's plant is a bill of materials in them plus
  construction work, and all seven bills reproduce their authored embodied
  labor to the tick. Plant is rebuilt from stock at the rate the ledger has
  charged since `docs/23`, and new capacity consumes the bill outright.
  What is *not* closed: a replacement shortfall is not throttled, and the
  value of newly built plant is not credited anywhere because the model
  keeps no plant stock account. Both are named in `docs/37` section 7;
- fixed capital in the price system: ~~absent~~ — in, since `docs/37`. It
  is 13.05% of the advance, not the 3.54% the value ledger reports, because
  the two measure different advances. And 89.6% of it sits in non-basic
  sectors where it moves the general rate of profit by nothing at all;
- equalization of profit rates across sectors: *computed* as an
  observation since `docs/27`, but not adopted — the cost anchor still
  freezes each sector's calibrated rate of profit rather than
  equalizing it. Enlarging the basket halved the deviations without
  making them usable (docs/29); turnover is the next candidate;
- ~~turnover~~ — done (`docs/31`). Capital is advanced for one
  production period plus the commodity's own inventory life, the price
  system's rate is 1.17 per day against a gross markup of 24.62, and
  the ledger reports a rate of profit on advances (0.0305/day) beside
  the flow ratio it has printed since `docs/23`;
- labor content of resource grades: a poorer deposit costs more silver but
  no more labor, so depletion moves cost and rent but not value;
- joint products in an actual scenario — the mass apportionment rule is
  implemented and unit-tested, but every current process has one output;
- ~~resource reserves, grades, and differential rent~~ — done for chemfuel;
- ~~absolute rent~~ — *measured* (`docs/43`), not collected. Marx's
  condition for it — a below-average organic composition implying a value
  above the price of production — holds **exactly** in a circulating-capital
  economy and is broken by fixed capital, because the markup gains a
  sector-specific `K/cost` term ranging 11.88 to 38.60 across sectors. The
  bound on chemfuel is 75.7% of its value, 229 ticks a day, and the
  deviations sum to floating-point zero, so rent can only ever be a
  deduction from surplus value. It could not become a *flow* until
  producers held cash; they do now (`docs/56`), so a landlord can be paid
  out of a purse in a later slice. Monopoly rent
  proper, price *above* value rather than up to it, is still absent;
- ~~labor supply and wages~~ — done: fixed regional pool, wage at the value
  of labor-power, surplus ledger;
- ~~the subsistence basket~~ — done, and enlarged to food, clothing and
  medicine (docs/29). Necessary labor is 3.6% of the working day rather
  than 2.5%, so the value of labor-power is still understated but the
  remaining understatement is small: shelter is under 20 ticks a
  worker-day and recreation was deferred deliberately. s/v is 26.71 and
  the honest reading is that it is roughly RimWorld's own figure;
- ~~wage deviations from value~~ — the reserve army is done (`docs/47`):
  the wage premium follows the employment rate, is a deduction from
  surplus value rather than a change in it, and reaches the price of
  wage goods through demand eight times more than through cost -- a
  ratio `docs/52` §3 shows to be a fact about buffer targets, not about
  the channel. Habituation is done (`docs/52`); worker mobility between
  regions is still absent, and `docs/50` puts it on Phase D's path;
- credit, bankruptcy, and liquidity-constrained consumption (workers are
  cash-constrained on the basket, but nothing else is);
- ~~capacity depreciation~~ — done (`docs/39`). Mothballing is still absent
  and deliberately so: arresting an idle plant's decay needs a rule about
  expected future demand, and expectations here are one exponentially
  smoothed price. Moral depreciation — plant devalued by a better technique
  appearing rather than by wear — is also still absent;
- ~~individual producer cash accounts~~ — done (`docs/56`), off by default:
  producers hold purses, pay inputs, plant matter and wages from them, are
  liquidity-rationed when they cannot, and distribute what they hold above
  their working capital to an owners' fund that buys the final good. Money
  profit is a flow now, and in the stationary circuit it is exactly what
  the fund spends (210 silver a day, Kalecki's identity measured). The
  component sector's purse takes 557 days to drain and then rests at 1.37×
  its authored price, rationed and not bankrupted. Transfer pricing and
  producer-level *inventory* are still absent — the pool is a consignment
  paid out by supply share — and belong to the procurement slice;
- more than six commodities or two regions;
- RimWorld save/UI/runtime integration.

Production consumes accounted inventory and pays a cost floor that now
includes wages. Capacity investment consumes silver. Extraction draws from
finite reserves with grade depletion and differential rent. Workers are paid
the reproduction cost of labor-power and buy real meals; surplus labor is
measured, not asserted. All material and silver ledgers close, with silver
now cycling rather than flowing one way. labor values are solved from the
process graph and reproduce the closed analysis exactly, save for the one
link `docs/08` declared stylized.

The reproduction circuit is closed in both directions: goods are made from
goods and labor, and labor is reproduced by goods. Cost reaches price, the
cheaper producer wins custom, and three ledgers now close to floating-point
zero — material, silver, and value.

What it lacks is a price system of its own. Two-thirds of every upstream
price is a wedge the model cannot account for, because prices are anchored
to RimWorld's authored `MarketValue` while costs are built from a wage the
authored prices never knew about. Every other component has been carved out
and named; what remains is the seam `FINDINGS.md` found, and closing it
means deriving prices rather than importing them.

**That work has started, under the ACE Trading World framing** (the three
imposed conditions named in `docs/55` §1). Producer cash is done
(`docs/56`). Firm-posted prices are built and measured (`docs/58`): exactly
stationary, cost passes through in full with every markup preserved — and
unusable as a default, because a posted price needs a stock its poster owns
to respond to, and a shared pool gives a contested sector the wrong signal;
shocks also leave their price level behind, because entry responds only to
shortfall and not to margin. Procurement is built too (`docs/60`): no production fixed point and no
pool, every producer planning from its own sales and stock and buying from
the sellers it can afford, exactly stationary from the reseeded state, all
three identities closing. Off by default. `docs/60` read every shock's
price level as permanent; `docs/62` found the stock target was the plan's
pool in disguise and corrected it — each producer now targets the
inventory life of its own expected demand, custom is split by what a
seller can serve, sell-outs restart a dry sector, and idle capacity with
a margin above a going one (`going_margin`, 0.50) cuts. The corrected
market gravitates from above: the glut returns to the reference, the
shortage settles within 2% of it, and a cost advantage is used down to
cost plus the going margin. Entry on margin (`docs/61`, `docs/63`) is the
capacity side of the same signal, built and off by default: capital
enters where the expected price clears the best technique's cost by more
than the going margin, copying that technique, with the intention
accruing to a project's worth. It brings the shortage's level below the
market's own and then overshoots on its lead time, because nothing
exits; with the going margin set inside the authored band
(`gravitation`), every sector in both regions ends within 0.06 of it.
**Exit is built and measured (`docs/64`, `docs/65`), and it is not
usable.** Its signal is right — a cost advantage draws the incumbent
down to its custom plus the reserve exactly, and the investment rule
reading the market's demand instead of the plan's throughput kills the
66-unit leaves entrant a shortage used to place, 66.2 → 9.7 against a
sector demand of 63.8. But its retirement clause deletes any sector
whose whole demand is below the minimum plant, and the seeded circuit
has two of them in each region: clothing and medicine leave the
subsistence basket on day 45 and no rule can rebuild them, because the
same constant is a build-side floor. The basket shortfall goes from 0.08
to 94.4 in the glut. `docs/66` designed the fix, `docs/67` measured it:
the floor works — the basket sectors rest at exactly 0.1 and the
gravitation shortfall goes to zero — and it uncovered a deeper defect it
had been hiding. A seller emptied by the very order it is answering
recorded no sell-out, because `_note_sellouts` counts only sellers
already empty when the order arrives and `_final_market` called it before
the stock was drawn down. So a provisioner serving half the basket
expected only what it sold, exit shrank the sector to fit its own supply,
and the workers went short every day at a price that never rose
(`docs/67` §5). `docs/68` moved every such call to after its pass's buy
and `docs/69` measured it: the glut's shortfall stops accruing around day
181, its level comes home to 1.0384× the reference, and meals in a
shortage are priced at 19.80 rather than 10.21. Two further findings
stand: nothing in this economy is outside the basket, so `docs/65` §2's
"clean readings" were not clean (`docs/67` §4); and entry and exit still
alternate in one region and converge in the other under identical rules
(`docs/65` §5, `docs/69` §4), which is `docs/64` §7's fourth mode and the
slice's one open finding. The `docs/58` §5 oscillation
turned out to be an entrant clamped to 18% of cost, corrected in
`docs/58` §5a.

---

## Handoff: Phase C, the arithmetic slices are done (2026-09-12)

Three slices of the model are ported, and **all three are compiled and
bit-exact under Mono**, which is the runtime RimWorld loads (`docs/76`):

| slice | docs | readings | exact |
|---|---|---:|---|
| the value solve | 53, 54 | 2,988 | .NET 8 and Mono |
| the basket and the wage | 72, 73 | 112 | Mono |
| the reserve army and habituation | 74, 75 | 960 | Mono |
| the regional price update | 77, 78 | 48 | Mono, `exp` included |
| the wage-cost refresh | 79 | 43 | Mono |

**The planned model's arithmetic core is ported**: 4,151 readings, zero
ulps, against the runtime the game loads. The market model's rules —
posted prices, procurement, entry, exit — are deliberately not ported
while `docs/71` §5 leaves the reference following the planned model.

`docs/74` §7's "no third unbuilt slice" rule is discharged; there are no
unbuilt slices. The price slice carried the port's first transcendental
and it agreed to the bit — contingently: CPython's `math.exp` and Mono's
`Math.Exp` both reach the platform's glibc here, and another platform's
libm may not. `exp` is answered for this machine, not settled.

**How, when `docs/72` §7 said it was impossible.** Microsoft's
distribution host is blocked by the network policy, but **Ubuntu's
archive is not, and it carries Mono**: `apt-get install -y mono-mcs`.
Two results documents wrote the gap off without checking whether a
*different* toolchain was reachable. Worth remembering: "the official
toolchain is unreachable" is not "no toolchain is reachable".

**Still needs a machine with the .NET SDK**, and it is a shorter list
than it was:

1. `dotnet run --project economy_mod/Source/Economy.Core.Check` — the
   harness itself has never run. It does not compile under Mono, and
   every error is `System.Text.Json` missing from Mono 6.8's BCL, with
   no syntax and no accessibility errors; it targets `net8.0` where that
   assembly exists.
2. A `net472` build. Mono 6.8's default profile is close and is not it.
3. Loading `Economy.Core` **in the game** — changes `verify.py`'s
   expected surface, needs a human at the game.

**Two rules for the rest of the port**, both now confirmed by the port
reproducing the readings they shaped:

- **A fixture carries the state a magnitude is computed against**, not
  only the magnitude (`docs/73` §2). `Ledger.add` accumulates and
  `region.cash -= bill` subtracts from a large purse, so the same wage
  bill posts +13.326840677261316 and moves the purse by
  −13.326840677254950.
- **A fixture is checked for which branches it takes**, not which its
  scenario contains (`docs/75` §3). Three bargaining fixtures never
  reached habituation's taken branch, because a sequence freezes
  employment and the premium then converges monotonically.

**The float boundary rule** (`docs/78` §3, corrected and sharpened by
`docs/81` §3). Mono's `double.Parse` is not correctly rounded, but the
danger is narrower and more specific than `docs/78` guessed:

| path | decimal safe? |
|---|---|
| Mono writes, Mono reads | **yes** — 0 of 2,078 values failed |
| CPython writes, Mono reads | **no** — 1 of 2,072 literals failed |
| one runtime writes, another reads | **no**, same mechanism |

Mono reads its own `ToString("R")` back correctly because that emits
seventeen digits, past where its parser goes wrong; CPython's `repr`
emits the shortest round-tripping form and Mono mis-reads one in two
thousand. So:

> **Never let a float cross an implementation boundary as decimal.**

That covers saves, seed data, fixtures, and every hand-off between the
laboratory and the game. The mod will be seeded from laboratory-authored
data, so at the 647-commodity scale `docs/33` measured this is a
certainty rather than a risk — a Stage 1 economy that is *almost* the
laboratory's and never exactly it. `StateCodec` (`docs/80`, `docs/81`)
exists for that, and it is measured: 2,078 values exact.

(None of this casts doubt on the port's exactness results: a mis-parse
can only manufacture a failure, never a pass.)

**A coverage gap in the laboratory, found by the port** (`docs/79`
§3a). **No process in any scenario has more than one output** — not the
six-commodity circuit, not Department I's nine, not the synthetic
economy. So `share_of_cost`, the mass apportionment `docs/08` chose
deliberately, returns 1.0 every time it is called and **has never been
exercised by anything**, the 2,988 value-solve readings included. It is
unfalsified because nothing has tested it, and a joint process — a
refinery making two fractions, butchering making meat and leather — is
something a real economy has everywhere. Belongs on the omissions list.
A test pins it and fails when a joint process is added.

**Phase C, what is built and what is not.**

| part | state |
|---|---|
| the planned model's arithmetic, five slices | ported and exact, 4,151 readings under Mono |
| the persistence codec (`StateCodec`) | built and exact, 2,078 values |
| the day scheduler (`DayScheduler`) | built, invariant holds at every budget and save point |
| the wealth coupling (`WealthCoupling`) | built, 2,526 property checks |
| wiring into `EconomyWorldComponent` and the tab | **written; compiled against a stub façade only** |

Everything in the first eight rows has **no RimWorld reference**, which
is exactly why it could be measured here. The last row is written and
compiles — the schema bumped to 3, the economy persisted as one encoded
string, `WorldComponentTick` replaced by a budgeted scheduler advance, a
mid-day save resuming at its cursor, two new tab rows — but it compiles
against a **hand-written stub façade** of the RimWorld API (kept in the
session scratchpad, not committed), not against RimWorld. That catches
syntax, types and call shapes; it does not catch a wrong signature and
it cannot run.

**Toolchain note.** Both Mono (`mono-mcs`) and the .NET SDK
(`dotnet-sdk-8.0`) install from **Ubuntu's archive**, even though
Microsoft's distribution host is blocked by the network policy — the
SDK needs `apt-get update` first or it 404s on a stale index. Three
separate documents wrote a verification off as impossible before
checking this. **A failure to obtain something is evidence about the
attempt, not about the thing.**

**What a session at the game has to do** — `docs/86` §5 closed the
first two of `docs/85` §6's five:

1. ~~Build `net472`; run the check harness.~~ **Done** (`docs/86`): the
   build is clean, the harness passes, and the `net472` artifact is
   bit-exact under Mono.
2. **Build the mod assembly** (`Economy.csproj`) against RimWorld's
   shipped managed DLLs — game files this environment does not have and
   should not. Much reduced by `docs/87`: the mod's game-facing code now
   builds `net472` against `economy_mod/Source/Economy.Facade/`, whose
   every member was read out of the last real build's reference tables
   with `monodis`. Because that façade contains nothing else, the build
   proves the new wiring **uses no RimWorld API the previous real build
   did not already resolve**. A real build is still the authority.
   (If someone calls a RimWorld member the mod has not used before, the
   façade build fails — that is deliberate, and keeps growth in the
   RimWorld surface visible in a mod whose posture is no Harmony, no
   gameplay mutation, no `Rand`.)
3. Start the game with both mods and **read the log**. The reports have
   been exercised against a fake host (`docs/91`), so a `FAIL` there is
   evidence about RimWorld rather than a coin-flip between a real
   problem and a mis-worded check — three such mis-wordings were found
   and fixed before they could reach the game; save, reload,
   **read the log**; load a pre-schema-3 save, **read the log**. The mod
   self-checks on load and again after a timed day (`docs/88`,
   `docs/89`) and prints a report naming what it expected, what it saw,
   and why any difference matters — so this step is paste, not inspect.
   The co-load check under "Stage 1 runtime shell" below is still stale
   and is step 2's real content.
4. ~~Profile the tick.~~ The self-check now measures it: the report's
   budget line recommends a `PhasesPerTick` for a 2 ms frame budget and
   says outright if no single phase fits. Set the constant from what it
   reports.

**What is left in Phase C**, and the balance has shifted. The
arithmetic slices are **done**. The engineering half is untouched and is now the
larger half: the daily tick amortised across ticks (about 1.1 s of C#
work per simulated day at full scale, against a 60,000-tick day), the
full economic state through save and load, the UI, and the
`MarketValue` wealth coupling — the project's second-largest remaining
risk. **None of those can be finished without the game running**, which
is a human's step. The in-game verification under "Stage 1 runtime
shell" is still stale and still first.

## Handoff: the cobweb (2026-09-12)

The churn is diagnosed (`docs/70`, `docs/71`). It is **not** entry and
exit alternating, and it is not a stock target fighting a flow reserve.
It is a cobweb: final demand is price-elastic at 1.35, and above unit
elasticity a price cut raises the sector's revenue, so capacity chases
the demand each cut creates until the stock drains and the whole loop
runs backwards. Period: hundreds of days. No rule against it is built,
deliberately.

**Done and committed.**
- `docs/70`, the design, with three findings that stand: entry on margin
  is not involved (with it off the cycle is bit-identical — same range,
  same capacity, same 488 exits); the investment rule's buffer branch is
  necessary to it as the trigger; and the cycle follows the **cheaper
  sector**, not the region, with the trade route irrelevant. Equal costs
  and both regions cycle identically; swap the costs and the cycle swaps
  regions.
- `docs/70`'s rule — exit's floor extended to the plant the investment
  rule would immediately rebuild — built, measured and **reverted**. Its
  scope predictions all held and its central one failed completely: the
  gravitation range did not move at all. Nine `exit.*` readings moved for
  nothing, so it is out.
- `docs/71`, the results and the correction, with the elasticity sweep:
  the bifurcation sits between 0.9 and 1.2, at unit elasticity, which is
  where the economics says it should be. `docs/70` carries a pointer to
  it, as `docs/60` does to `docs/62`.
- The reference is **untouched at 322**, every metric at zero delta,
  because the rule was reverted. The suite is green.

**Not done — the next session's task, in order.**
1. Decide what the laboratory is for here, and say it in the design
   before choosing a rule. `docs/71` §5 makes the case that a cheap
   sector overbuilding, crashing and rebuilding is not self-evidently a
   defect — `docs/64` §7 listed a real cycle among exit's possible modes,
   and this is one, with a threshold and a cause. Damping it and keeping
   it are both defensible; doing either by accident is not.
2. If it is to be damped, `docs/71` §5 names three candidates and prefers
   the first: the posted price cuts on *idleness*, and above unit
   elasticity idleness is self-replenishing because the cut creates the
   demand that removes it. A price rule that read the revenue it gives up
   would stop at unit elasticity by itself. That is the same kind of
   correction as `docs/62` — a rule reading the wrong quantity — rather
   than a new mechanism.
3. The buffer branch's regional pool is a separate and smaller question,
   named in `docs/70` §4: it reads `region.inventory`, a pool, in a model
   where `docs/59` gave every producer its own stock and `docs/62`
   removed the pool from every other target. Removing it outright is
   already measured and rejected — the glut's shortfall goes 21.6 → 29.3,
   because it is the market's only means of rebuilding a stock after a
   shock. Rewriting it per-producer is the open version.
4. The boom's meals collapse (`docs/69` §4) is still unexplained. Part of
   its yayo overshoot is the cobweb — turning the buffer branch off takes
   yayo from 35.40 to 12.10 — but employment only recovers from 0.2051 to
   0.3027 and meals capacity stays at 0.42 against 1.66. Something else
   takes the meals plant.

**One known failure that is not ours.** `tests/test_port_fixtures.py`
`test_the_committed_fixtures_are_current` fails on `scale_647_day3` with
a last-digit float difference. It predates this work and fails with every
change stashed — a machine difference, not a model one. Regenerate it
deliberately, on the machine that will keep it, or leave it.

**Standing rules that applied throughout:** no dependencies; no change
to default model behaviour (`python -m economy_lab.baseline` zero
deltas; `python -m unittest tests.test_economy_lab` green); design
before build; runs above a few seconds launched deliberately; no
decompiler.

## Working rules

- Keep commits small.
- Preserve unrelated working-tree changes.
- Ask before adding dependencies.
- Do not re-litigate the closed labor figures without new evidence.
- Keep labor value, market price, surplus, profit, and rent distinct.
- Express calibration tests as ratios of regional flows, not arbitrary item
  counts.
- Prefer deterministic scenarios and invariant checks before adding features.
- Update this file after every meaningful design decision or implementation
  checkpoint.
