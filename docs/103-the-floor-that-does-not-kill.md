# The producer quantum: the floor is necessary and not sufficient

Measured against `docs/102`'s eight predictions. **Four passed, two
failed, one was never reached, and one I declined to predict and simply
measured.**

**The headline: the floor works and the death does not follow. At a
quantum of 1e-3 worker-days the drained component producer is idled on
251 of 1200 days — a fifth of its life — and its longest *consecutive*
idle run is one day. `bankruptcy_idle_days` needs thirty in a row. The
producer oscillates with a period of two and never dies.**

**Why: idling repairs the purse. A producer that runs nothing pays no
wages and buys no inputs, but it still receives revenue, because in our
model revenue comes from demand meeting stock rather than from
employment. In Wright, M1 generates revenue when an *employee* samples
the market — a firm with no employees samples nothing and receives
exactly zero, so idling cannot repair anything and death follows. The
divergence is not that revenue is a draw. It is that our revenue is
decoupled from employment.**

## 1. The scorecard

| # | prediction | verdict |
|---|---|---|
| 1 | inert by default; 322 metrics unchanged | **pass** |
| 2 | inert where the purse does not bind; bit-identical | **pass** |
| 3 | a window exists where the zombie dies and others do not | **fail** — no window |
| 4 | bankruptcy dated after day 550 | **fail** — deaths only at collapse quanta, from day 3 |
| 5 | money conserved through a bankruptcy | **pass** — 4.07e-10 with 102 of them |
| 6 | the macro effect is negligible | **not reached** — see §4 |
| 7 | something downstream notices | measured, §5 |
| 8 | the bare wage share does not move | **pass**, strikingly — §6 |

## 2. The sweep

`cash_circuit`, 1200 days. "Peak idle" is the longest run of *consecutive*
idle days reached by the component producer; `bankruptcy_idle_days` is 30.

| quantum | bankruptcies | components peak idle | components idle days | employment | curtailment |
|---:|---:|---:|---:|---:|---:|
| 0 (off) | 0 | 0 | 0 / 1200 | 0.31819 | 1.4515 |
| 1e-04 | 0 | 0 | 0 / 1200 | 0.31819 | 1.4527 |
| **1e-03** | **0** | **1** | **251 / 1200** | 0.31844 | 1.4633 |
| **3e-03** | **0** | **1** | **258 / 1200** | 0.31780 | 1.5044 |
| 5e-03 | 4 | 2 | 291 / 1200 | **0.04366** | — |
| 1e-02 | 102 | 29 | 796 / 1200 | **0.00000** | 516.2591 |

Read the two bold rows against the two below them. At 1e-3 and 3e-3 the
floor is unmistakably working — a producer that was never idle for a
single day now idles for a fifth of them — and the death counter never
gets past **one**. At 5e-3 four producers die and regional employment
falls by 86%. At 1e-2 the economy ceases to exist.

**There is no window.** The transition is not from "the zombie dies" to
"too much dies"; it is from "nothing dies" to "everything dies", with
nothing in between. `docs/102` predicted a window bounded below by
components' affordable employment and above by the smallest healthy
producer's. Both edges are real; there is simply no gap between them,
because the quantum that idles a producer *permanently* is the same
quantum that exceeds its whole employment, and nearly every producer in
the circuit employs less than 1e-2 worker-days a day.

## 3. Why the floor does not kill

The component producer under a 1e-3 quantum, sampled:

| day | purse | affordable runs | worker-days | after the floor | runs |
|---:|---:|---:|---:|---:|---:|
| 0 | 11.938 | 0.313 | 0.0652 | 0.312 | 0.00190 |
| 300 | 5.525 | 0.145 | 0.0301 | 0.144 | 0.00190 |
| 600 | 0.237 | 0.00596 | 0.00124 | 0.00480 | 0 |
| 700 | 0.164 | 0.00404 | 0.00084 | **0** | 0.00303 |
| 900 | 0.256 | 0.00647 | 0.00135 | 0.00480 | 0 |
| 1199 | 0.204 | 0.00509 | 0.00106 | 0.00480 | 0.00315 |

Once the purse falls near the cliff, the producer's affordable employment
straddles one quantum. On a day it falls below, the floor gives zero and
the producer runs nothing — and **its purse then rises**, because it has
bought no inputs and paid no wages while its stock continues to sell. The
next day it is above the cliff again and runs. Idle, run, idle, run.

`liquidity_idle_days` resets to zero on every day with positive runs, so
a period-two oscillation pins it at one forever. The thirty-day counter
is not approached, let alone reached.

This is the third distinct way this project has found the same branch
unreachable. `docs/101` found it unreachable because curtailment was
continuous. The floor fixed that, and it is *still* unreachable, now
because idleness is self-limiting.

## 4. What prediction 6 was for, and why it was never reached

`docs/102` predicted that killing the zombie would change nothing
measurable, because it had already shrunk to 0.12% of regional
employment — and said that prediction was the one most expected to hold
and least wanted. It was never tested, because the zombie never died
alone.

What the sweep shows instead is worse for the rule: the only quanta that
kill anything kill almost everything. At 5e-3, four deaths cost 86% of
regional employment; the producers that die are not marginal zombies but
ordinary members of the circuit whose entire employment happens to be
below one quantum. `wood` employs 0.000014 worker-days a day and `steel`
0.000145 — a quantum that is a cliff for `components` at 0.000395 is an
extinction event for both.

So the rule as built cannot discriminate. It is not that the window is
narrow; it is that the ordering it would need — marginal producers
failing before healthy ones — does not exist, because in this circuit
"small" and "insolvent" are unrelated.

## 5. What happened downstream (prediction 7)

Nothing raised. At 1e-2 the economy degrades rather than erroring:
employment reaches exactly 0.00000, 102 producers retire, and 516 units
of output are curtailed. The model does not object to an economy with no
production; it reports one. That is the right behaviour for a laboratory
and worth knowing.

## 6. The identity, through a collapse (prediction 8)

| quantum | bankruptcies | bare wage share | `VLP ÷ ticks_per_worker_day` |
|---:|---:|---:|---:|
| 0 | 0 | 0.036090636 | 0.036090716 |
| 1e-03 | 0 | 0.036090649 | 0.036090716 |
| **1e-02** | **102** | **0.036090610** | 0.036090716 |

`docs/99` claimed the bare wage share is an identity that no quantity
rule can move. Here it holds through a hundred bankruptcies and the
extinction of regional employment: the share of the product going to
labour is unchanged, to seven significant figures, in an economy that has
stopped producing. That is as strong a confirmation as the identity is
ever going to get.

## 7. What this means for docking

**The rule is kept.** It is correct as specified, it is gated off, it is
inert everywhere the purse does not bind, and it is a prerequisite for
anything that wants F1's cliff. But on its own it buys nothing, and
saying so is the point of having written the predictions down first.

**A7 is restated, more precisely than `docs/97` had it.** The original
wording was "the market is a common pool; revenue is a draw, not a
certainty", and `docs/98` marked it "partially holds". §3 locates the
part that does not:

> In Wright, revenue is produced *by employment*. M1 fires when an
> employee or an owner is the active actor, and transfers from the market
> pool to the firm. A firm with no employees has no one to sample, so its
> revenue is identically zero. Employment and revenue are the same act.
>
> In ours, revenue is produced *by demand meeting stock*. A producer that
> employs nobody today still sells what it made yesterday. Employment and
> revenue are separate acts.

That decoupling is why purses do not empty (`docs/101`), and why idleness
repairs them (§3 here). Both of this project's attempts to make firm
death endogenous have failed on it, in different places.

**So the next question is not a rule but a decision**, and it is the one
`docs/101` §7 flagged: whether to couple revenue to employment, which in
Wright's form means a draw from a common pool and therefore a
pseudo-random stream reproducible bit-for-bit across CPython and Mono
under `docs/53`'s contract. That is a commitment to a hand-rolled integer
PRNG transliterated like every other ported rule — perfectly possible,
and not something to start without deciding.

There is also a weaker form worth considering first, which needs no
randomness at all: **make a producer's sales conditional on its having
produced**, so that an idle producer cannot collect. That would break the
period-two oscillation in §3 without touching determinism, and it is a
much smaller change than A7 proper. Whether it is defensible as
*economics* — a firm really can sell from inventory while idle — is the
question, and it is a modelling judgement rather than a technical one.

## 8. What was changed

`producer_employment_quantum`, defaulting to `0.0`, threaded through
`ScenarioParameters`; one helper, `_quantize_employment`; one call site
in `_produce`'s affordability block. Ten tests in
`tests/test_producer_quantum.py`, including the two that pin this
document's negative result. `python -m economy_lab.baseline` reports 322
metrics with no nonzero delta.
