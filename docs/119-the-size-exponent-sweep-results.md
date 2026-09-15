# The size-exponent sweep: results

> **Annotated by `docs/123` §1.** §5–6 attribute the `drawn > market` clamp to Wright. It is ours; his draw is bounded by [0, V] by construction. The cap counts stand; the attribution and "safety check" framing are withdrawn.


Measures `docs/118`. 20 values of β over [0, 1.5] × 50 seeds = 1000 runs,
120-month burn-in then a 180-month window, fitted per seed at n ≈ 21,900.
Reproduce with `python -m economy_lab.size_exponent out.json 50`.

**The outcome key in `docs/118` §6 did not contain the answer.** The
question "basin or knife edge" presumes β is a free parameter with two
sides. It is not. Wright's model cannot represent a size exponent above
1, and the line that stops it reads like a safety check.

## 1. The table

Per-seed medians, except the two the 1Y rule leaves too short to fit
alone. `*` marks a reading inside its band from `docs/118` §4, fixed
before the run. `cond` counts seeds whose largest firm exceeds 500.

| β | α | f.kurt | g.kurt | demise | λ | inc.α | share | unemp | large | firms | cond | held |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.00 | *(n/a)* | −0.369 | 0.047 | 10.08 | 1.082* | 1.506* | 0.501* | 0.144 | 14 | 208 | 0 | 3 |
| 0.10 | 4.988 | −0.331 | −0.018 | 10.22 | 1.099* | 1.514* | 0.505* | 0.139 | 14 | 206 | 0 | 3 |
| 0.20 | 4.590 | −0.300 | 0.031 | 10.45 | 1.213* | 1.532* | 0.508* | 0.139 | 17 | 203 | 0 | 3 |
| 0.30 | 4.475 | −0.239 | −0.117 | 10.68 | 1.214* | 1.547* | 0.513* | 0.136 | 17 | 198 | 0 | 3 |
| 0.40 | 3.997 | −0.156 | −0.150 | 10.96 | 1.125* | 1.560* | 0.515* | 0.139 | 18 | 194 | 0 | 3 |
| 0.50 | 3.830 | −0.041 | 0.215 | 11.45 | 0.981* | 1.576* | 0.520* | 0.142 | 22 | 185 | 0 | 3 |
| 0.60 | 3.581 | 0.108 | 0.070 | 11.92 | 1.268* | 1.593* | 0.523* | 0.143 | 26 | 179 | 0 | 3 |
| 0.70 | 3.178 | 0.296 | 0.220 | 12.57* | 1.208* | 1.619* | 0.527* | 0.151 | 30 | 169 | 0 | 4 |
| 0.80 | 2.673 | 0.697 | 0.145 | 13.47* | 1.125* | 1.635* | 0.529* | 0.159 | 40 | 159 | 0 | 4 |
| 0.85 | 2.371 | 1.033 | 0.032 | 14.12* | 1.001* | 1.642* | 0.533* | 0.154 | 52 | 152 | 0 | 4 |
| 0.90 | 2.007 | 1.540 | 1.447* | 15.07* | 1.085* | 1.466* | 0.534* | 0.154 | 63 | 143 | 0 | 5 |
| 0.95 | 1.672 | 2.286* | 5.165* | 16.27* | 1.262* | 1.332* | 0.536* | 0.157 | 78 | 133 | 2 | 6 |
| **1.00** | **1.296\*** | **3.889\*** | **2.747\*** | **17.95\*** | **1.227\*** | **1.188\*** | **0.539\*** | 0.158 | 103 | 116 | 1 | **7** |
| 1.05 | 1.094* | 5.596* | 1.679* | 19.54* | 1.175* | 1.073* | 0.540* | 0.170 | 145 | 112 | 5 | 7 |
| 1.10 | 0.993* | 6.530* | 1.484* | 20.82* | 1.233* | 1.043* | 0.543* | 0.163 | 166 | 108 | 6 | 7 |
| 1.15 | 0.942* | 7.339* | 0.820 | 21.21* | 1.142* | 0.998* | 0.543* | 0.172 | 175 | 102 | 6 | 6 |
| 1.20 | 0.902* | 7.705* | 1.018* | 21.36* | 1.213* | 1.007* | 0.550* | 0.168 | 242 | 97 | 8 | 7 |
| 1.30 | 0.872* | 8.560* | 1.451* | 22.05* | 1.160* | 0.981* | 0.551* | 0.173 | 239 | 101 | 8 | 7 |
| 1.40 | 0.867* | 8.575* | 0.189 | 22.12* | 1.144* | 0.975* | 0.552* | 0.163 | 232 | 93 | 7 | 6 |
| 1.50 | 0.885* | 9.076* | 0.873 | 22.28* | 1.145* | 0.969* | 0.545* | 0.171 | 202 | 106 | 8 | 6 |

Money conserved everywhere; worst error 1.50e-09.

## 2. A measurement defect, found and corrected

The raw sweep reported **α = 0.629 at β = 0** against 4.812 at β = 0.1 —
a discontinuity at the one point that is bit-identically `neutral`, whose
firm sizes run 1 to 14. `docs/114`'s rule applied (*suspect the
measurement before the model*) and it was the measurement.

The KS-minimising `x_min` **collapses to 1** in 32 of 50 seeds at β = 0,
9 at β = 0.1, 8 at β = 0.2 and none anywhere above. With `x_min = 1` the
"tail" is the entire body, and α bifurcates between two regimes — 0.62
when the selector collapses, 5.6 when it does not — so the *median* flips
according to which regime wins the seed count. Dropping the collapsed
seeds gives 4.790 at β = 0 and restores the trend. The table above shows
the corrected figures, and `(n/a)` where nothing survives.

The wider limit is worse and is not fixable by dropping seeds. The ratio
of the median largest firm to the median `x_min` — the range the fit
actually spans — is **1.1× at β = 0.1 and under 2× everywhere below
β = 0.9**. A power-law exponent fitted over less than one octave is not
a measurement. **So α is uninformative below β ≈ 0.9**, and the correct
statement there is not "α is large" but **"there is no tail to fit."**
That happens to support the same conclusion, which is why it did not
change any band verdict — but it is a different claim, and `docs/118`
should have pre-registered a minimum fitting range.

## 3. The seven predictions

| # | prediction | result |
|---|---|---|
| 1 | endpoints bit-identical | **pass** — β=1.0 ≡ `wright`, β=0.0 ≡ `neutral`, 3 seeds each |
| 2 | money conserved | **pass** — worst 1.50e-09 |
| 3 | α monotone, crossing 1.038 near β=1, >2 below 0.5, <0.8 above 1.2 | **partial** |
| 4 | condensation above β=1.2 | **fail, decisively** |
| 5 | non-tail facts hold over width ≥ 0.4 | **pass** |
| 6 | all-seven width ≤ 0.3, edges set by tail facts | **pass, for the wrong reason** |
| 7 | the region is non-empty and contains β = 1 | **pass** |

**P3.** Three clauses of four. After the §2 correction α falls
monotonically in trend (4.99 → 0.87) and exceeds 2 everywhere below
β = 0.5. It crosses Wright's reported 1.038 between β = 1.05 and
β = 1.10, so *near* 1 but not *at* it. The last clause fails: α does not
keep falling, it **flattens at ≈ 0.87** from β = 1.2 onward and turns
back up. §5 says why.

**P4 failed decisively and is the most useful failure.** Condensation
never happens: 8 of 50 seeds at β = 1.2, and still 8 at β = 1.5, never
the predicted majority. The median largest firm rises 103 → 242 and then
*falls* to 202. The runaway I predicted from proportional-growth theory
does not exist in this model.

**P6 passed on the number and failed on the substance.** The widest
contiguous all-seven run is [1.00, 1.10], width 0.10 ≤ 0.3. But the upper
boundary is set by `gdp_kurtosis`, and bootstrapping over seeds (1000
resamples) shows that statistic **cannot resolve the betas it is
separating**:

| β | g.kurt | 95% interval | P(≥ 1.0) |
|---|---|---|---|
| 0.85 | 0.032 | [−0.213, 0.285] | 0.00 |
| 0.90 | 1.447 | [0.108, 2.711] | 0.68 |
| 1.10 | 1.484 | [0.636, 2.541] | 0.79 |
| 1.15 | 0.820 | [0.302, 1.447] | 0.25 |
| 1.20 | 1.018 | [0.361, 1.640] | 0.47 |
| 1.40 | 0.189 | [−0.216, 0.662] | 0.00 |

The intervals at 1.10, 1.15 and 1.20 overlap almost entirely. The gap at
β = 1.15 is noise. What *is* sharply resolved is the **onset** — P(≥1.0)
is 0.00 for every β ≤ 0.85 and jumps at 0.90 — so GDP-growth kurtosis
works as a present/absent indicator and not as a ranking. Treating it
that way, the all-seven region becomes **contiguous from β = 1.0 to the
top of the sweep**, width ≥ 0.50.

**P7 passed, with a detail `docs/118` did not anticipate: β = 1 is the
region's lower endpoint, not its centre.** Every β below 1 fails; every
β above it passes.

## 4. The region is one-sided, and it does not end

Six of seven facts still hold far above the swept range (50 seeds each):

| β | α | f.kurt | demise | share | largest | cond | held |
|---|---|---|---|---|---|---|---|
| 2.0 | 0.926 | 8.20 | 21.4 | 0.543 | 170 | 4/50 | 6/7 |
| 3.0 | 0.956 | 7.07 | 20.9 | 0.539 | 249 | 6/50 | 6/7 |
| 5.0 | 1.053 | 6.38 | 20.6 | 0.532 | 183 | 4/50 | 6/7 |

The only fact missing at each is `gdp_kurtosis`, the one §3 shows is
unresolvable. At β = 5 — where a ten-member firm's draw is scaled by
10,000 — the economy still has α ≈ 1.05, ~20 demises a month, a wage
share of 0.53, and **no monopoly**.

## 5. Why: the model cannot represent β > 1

`_sample` ends with what looks like an overdraft guard:

    if drawn > self.market:
        drawn = self.market

Counting how often it fires (a capped draw leaves `market` at exactly
0.0, so it is observable from outside without touching the model):

| β | 0.0 | 0.5 | 1.0 | 1.1 | 1.5 | 2.0 | 3.0 | 5.0 |
|---|---|---|---|---|---|---|---|---|
| draws capped | 0.0% | 0.0% | 0.0% | 25.2% | 71.2% | 86.0% | 95.3% | 99.0% |

**β = 1 is exactly the largest exponent at which the rule never
saturates.** Above it the scale factor `members ** (β−1)` routinely
exceeds what the pool holds, the draw is clamped, and the rule degenerates
into *whoever is selected takes everything left*. Selection is uniform
over actors, so a firm is still chosen in proportion to its headcount —
which is **β = 1 behaviour**. The model does not run away above 1; it
reverts.

That single mechanism explains all three surprises: no condensation (P4),
α flattening at ≈0.87 instead of falling (P3's last clause), and a
"region" that extends to β = 5 and presumably beyond.

So the apparent robustness above β = 1 is **degeneracy, not a basin**. It
is not evidence that the facts tolerate super-proportional returns. It is
evidence that this model has no way to express them, because the budget
constraint binds first.

## 6. What this answers, and what it revises

`docs/117` §3 asked: basin or knife edge? **Neither, as posed.** β has
one usable side. The honest statement:

- **Below β = 1** the economies are genuinely different and the facts
  fail progressively — tails vanish first (α and both kurtoses), the
  wage share and recession λ never move at all. These are real
  measurements over real variation.
- **At β = 1** all seven hold.
- **Above β = 1** the model saturates back toward β = 1. That side of the
  sweep tests nothing.

This **revises `docs/117` §3's framing** rather than answering it. The
knife-edge worry was that the fit might be finely tuned. It is not
tuned — but neither is it robust in the way a basin would be, because
the region's width above 1 is an artefact of the clamp. The defensible
claim is one-sided: **the facts require revenue to be at least linear in
labour employed, and the model cannot test more than that.**

Two consequences for Wright:

1. **His attribution survives and is overdetermined.** Proportionality is
   enforced twice — once by the sampling rule he wrote deliberately, and
   once by a budget constraint that looks incidental. `docs/116` said
   M1 as written is load-bearing; the load is carried by two members.
2. **His facts do not identify β = 1 from above**, because nothing above
   β = 1 is reachable. The seven facts pin the law of value as an
   *inequality*, not the equality his prose asserts. Nobody could have
   read that off the paper, and it is visible only with the rule made
   continuous.

## 7. What this does not settle

The lower boundary's exact location is **not** a measured transition.
α is continuous in β (1.672 at 0.95, 1.296 at 1.00) and "β = 1" is where
it crosses the band edge *we chose* in `docs/118` §4. The genuinely sharp
thing at β = 1 is saturation onset, not the facts, which degrade
smoothly. Resolving the boundary more finely would measure the band, not
the model.

Nothing here revives the power law; `docs/114` stands, and α is a shape
reading. Nothing here concerns real economies. And the α gap at Wright's
own setting is now sharper rather than closed: per seed at n ≈ 21,900 we
measure **1.296** where he reports 1.038, and β ≈ 1.07 is what would
match him. `docs/114` attributed the earlier gap to sample size; at this
scale a gap remains, and it is unexplained.

## 8. Method notes

- `docs/118` pre-registered seven bands and they held as a discipline:
  the two predictions that failed, failed against numbers fixed in
  advance, and P6's hollow pass was only visible because the band was
  written down before the bootstrap was run.
- It did **not** pre-register a minimum fitting range for α, and §2 is
  the cost. **Adding to the rule collection:** *a fitted exponent needs a
  pre-registered range to be fitted over; without one, a fit that spans
  1.1× reports a number with the same confidence as one that spans 14×.*
- P4 was reasoned from proportional-growth theory, and `docs/118` §7
  named the exact reason it might fail — the pool depletes, competition
  is not in the theory. It failed for that reason. Naming the threat did
  not prevent the wrong prediction, but it made the failure legible in
  one step instead of sending us looking for a bug.
