# Stage 1: the wage-cost refresh in C#: design and results

Design and results in one, like `docs/62` — and, unlike `docs/62`, that
is partly an admission. **This slice was built before it was designed.**
The project's standing rule is design-then-measure and it was not
followed here: `WageCostSolver.cs` was written, compiled and verified
before a word of this document existed. It is recorded that way rather
than back-dated, because a design document written after the fact
predicts nothing and the only honest thing it can do is say so.

What mitigates it, and does not excuse it: the slice is twelve lines,
its contract was fixed by `docs/53` and unchanged since, and the
interesting decision in it — sharing the apportionment rather than
copying it — is visible in the diff. What does not mitigate it: a
prediction that is not written down cannot be wrong, and four of the
five port slices produced a finding precisely because something written
in advance failed.

## 1. What it is

`Economy._update_wage_costs`: the daily refresh that prices each
producer's living labor at the current basket cost. It is the wage's only
reach into what a producer's output costs, and with it the planned
model's arithmetic core is ported.

```
wage_per_tick = wage_rate / max(ticks_per_worker_day, EPSILON)
for each active producer:
    wage_cost_per_unit = process.labor_per_unit(commodity, commodities)
                       * wage_per_tick
```

The first ported rule that walks the **process graph**:
`labor_per_unit` is `direct_labor × share_of_cost / units`, and
`share_of_cost` apportions a joint process's cost across its outputs by
mass.

## 2. The one decision worth recording

`share_of_cost` was **already ported** — privately, inside
`LaborValueSolver`, where the value solve needs the same apportionment.
There were two options and the second was taken:

1. Copy it into `WageCostSolver`. Two implementations of one rule, and
   two things to keep in step with the laboratory the next time
   `docs/08`'s apportionment choice is revisited.
2. Widen the existing one to `internal` and call it.

Duplication is the kind of decision that looks free and is paid for
later — this project has a documented case of exactly that in
`docs/33`'s `+=`-against-`sum()` finding, where two ways of writing one
operation diverged in the last bit. One implementation.

The refactor touched `LaborValueSolver`, which was already verified, so
the value solve was re-run immediately: **4,060 readings, still zero
ulps.** Changing verified code is safe only when re-verifying it is
cheap, and the point of `docs/76`'s toolchain is that it now is.

## 3. What was measured

Three fixtures, one call per region, compared by **bit pattern** —
`docs/78` §2's rule, no decimal parser on the comparison path:

```
compared 43   mismatches 0
```

| fixture | why |
|---|---|
| `equilibrium_day60` | the six-commodity circuit |
| `capital_goods_day60` | nine commodities and Department I |
| `technique_change_day120` | two provisioners in one region on different techniques, so two producers of one good carry different labor per unit |

## 3a. And the coverage claim was wrong

This document's first draft said `capital_goods_day60` exercises the
joint apportionment "where joint outputs make the share something other
than 1.0". A test written to assert that — `docs/75` §3's rule, check
which branches a fixture *takes* — failed immediately. So the claim was
checked:

> **No process in any scenario in this laboratory has more than one
> output.** Not the six-commodity circuit, not Department I's nine, not
> the technique-change economy, not the 40-commodity synthetic one.

`share_of_cost` therefore returns `1.0` every time it is called, in
every scenario, and `labor_per_unit` is always `direct_labor / units`.
The mass-apportionment rule that `docs/08` chose deliberately, and that
this slice went to the trouble of sharing rather than copying, **has
never been exercised by anything** — including by the 2,988 value-solve
readings, which call the same function.

That is a finding about the *laboratory*, not the port. `docs/08`'s
choice is unfalsified because nothing has tested it, and a joint process
is the kind of thing a real economy has everywhere: a refinery making
two fractions, a butchering process making meat and leather. It belongs
on the laboratory's list of known omissions, and it is the second
coverage gap these port slices have exposed by asking what a fixture
actually touches (`docs/75` §3 was the first).

The test now pins the true state of affairs and fails when a joint
process is finally added, which is when the fixture will be needed.

## 4. The planned model's arithmetic is ported

| slice | docs | readings | exact |
|---|---|---:|---|
| the value solve | 53, 54 | 2,988 | .NET 8 and Mono |
| the basket and the wage | 72, 73 | 112 | Mono |
| the reserve army and habituation | 74, 75 | 960 | Mono |
| the regional price update | 77, 78 | 48 | Mono, `exp` included |
| the wage-cost refresh | 79 | 43 | Mono |

**4,151 readings, zero ulps**, against the runtime the game loads.

What is *not* ported, and is a deliberate boundary rather than an
omission: the market model's rules — posted prices, procurement, entry,
exit — which `docs/71` §5 leaves as an open question the laboratory has
not settled, and which would be premature to freeze in C# while the
reference still follows the planned model.

## 5. What is left in Phase C

All of the engineering half:

- **the daily tick amortised across ticks** — about 1.1 s of C# work per
  simulated day at full scale against a 60,000-tick day;
- **the full economic state through save and load**, now with
  `docs/78` §3's constraint on it: persist doubles as bits;
- **the UI**;
- **the `MarketValue` wealth coupling**, the project's second-largest
  remaining risk.

The first two can be built and tested outside the game and the second
two cannot. `docs/80` takes the persistence codec, which is the one with
a known trap already in it.

## 6. Cost

Twelve lines of C#, one widened access modifier, three fixtures, one
re-verification of the value solve, and this document — which should
have come first.
