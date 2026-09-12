# Stage 1: the wealth coupling, and how not to break the game: design

Written before implementation. `HANDOFF.md` lists this as the project's
**second-largest remaining risk** and the only one of the three that is
a design problem rather than an engineering one: "a dynamic price system
feeding `MarketValue` changes raid strength, because storyteller wealth
reads it. Getting this wrong makes the mod feel broken rather than
interesting."

## 1. The mechanism, stated exactly

RimWorld's storyteller scales threats to colony **wealth**, and wealth
is computed by summing items' `MarketValue`. `MarketValue` is authored
per `ThingDef` or recursively derived from ingredient costs
(`HANDOFF.md`'s vanilla notes), and it is a *static* number: the same
steel is worth the same today and next winter.

This project's whole subject is that prices are not static. A model
whose yayo price triples in a glut is doing its job. If that price
reaches `MarketValue`, then a colony that did nothing has become three
times as rich, and the storyteller sends raids for a wealth the player
never accumulated. The player experiences this as the mod being broken,
and they are right — the raid is a real consequence of a fictional gain.

The inverse is worse in a subtler way: a crash in a commodity the player
stockpiles makes them *poorer*, the raids get easier, and the mod has
quietly turned a market simulation into a difficulty slider.

## 2. The rule

**The economy never writes `MarketValue`, and the default build never
influences wealth at all.**

That is the existing shell's posture — the tab says "Vanilla prices are
unchanged" — and this document's contribution is to make it a *checked*
property rather than a property that happens to hold because nothing is
wired yet.

Three modes, of which only the first is default:

| mode | what reaches wealth | for |
|---|---|---|
| `Observe` (default) | nothing | the mod as it ships |
| `Bounded` | a factor clamped to a band around 1.0 | a future opt-in |
| `Unbounded` | the model's price | never shipped; exists to make the danger measurable |

`Bounded` exists because "never couple" is a decision that should be
*revisitable with evidence*, and evidence needs a mode that produces a
number. Its clamp is the whole point: a price that has tripled
contributes at most the band's edge, so the storyteller sees a nudge
rather than a phantom fortune.

## 3. What is measurable without the game

Most of this risk lives in play. What does not, and what is worth
building now, is the **exposure calculation**: given the model's prices
and vanilla's authored values, what would the colony's wealth become?
That is a pure function of two price tables and a stock list, and it
answers the question a designer has to answer before enabling anything
— *how far off could this push a raid?* — without a raid.

So the deliverable is:

```
economy_mod/Source/Economy.Core/WealthCoupling.cs
```

- `WealthMode` — the three modes;
- `Factor(mode, modelPrice, authoredValue, band)` — what one unit
  contributes, relative to its authored value;
- `ProjectedWealthRatio(mode, stocks, modelPrices, authoredValues, band)`
  — the colony's wealth under the mode over its wealth under vanilla.

No RimWorld reference, so it can be tested here.

## 4. Predictions

4.1 In `Observe`, `ProjectedWealthRatio` is **exactly 1.0** for every
input — every stock list, every price table, including prices that have
tripled or collapsed. Not approximately: the mode must be provably
inert, because "the default build cannot affect raids" is the claim the
player is owed.

4.2 In `Bounded` with band `b`, the ratio lies in `[1/(1+b), 1+b]` for
every input, including a price table where everything has gone to ten
times or a tenth of authored. The clamp cannot be escaped by an extreme
price.

4.3 In `Unbounded`, a tripled price on the whole stock gives a ratio
near 3 — the mode exists to show the danger and must actually show it.
If it does not, the calculation is not measuring what it claims.

4.4 The laboratory is unmoved: 322 metrics at zero delta.

## 5. What would make this wrong

If 4.1 is only approximately 1.0, the default is not inert and the
claim on the tab is false. That would be the most serious possible
outcome here and it is the first thing to check.

If 4.2 can be escaped — a NaN price, a zero authored value, a negative
stock — then the clamp is a guideline rather than a bound, and a bound
is what the storyteller needs. The edge cases are the test, not the
ordinary path.

## 6. What this cannot do

It cannot tell you whether a bounded coupling *feels* right, which is
the actual question and needs play. It gives the person answering that
question a number instead of an intuition, and it makes the default
provably safe while they decide.

## 7. Cost

One C# file of about eighty lines, a property harness over extreme
inputs, and this document.
