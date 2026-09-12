# Stage 1: persisting the economy exactly: results

`docs/80` is the design. The codec is built, compiled and measured.
**Its central prediction failed, the control it named as the thing that
could refute the design did refute the design as argued — and a second
measurement rebuilt the case on different and better evidence.**

## 1. What held

**4.1** Every one of the **2,078 distinct doubles** in the port's five
committed fixture directories round-trips through `Encode`/`Decode`
under Mono to the bit. Zero failures.

**4.2** The same values through `Write`/`Read` on a whole snapshot, with
the labor values and three per-region tables populated and the scalar
fields set: zero failures. The container does not undo the encoding.

**4.4** The laboratory is unmoved: 322 metrics at zero delta, nothing in
`economy_lab/` touched.

**The size question from §5** is answered and is not a problem: 2,078
values encode to 51,492 characters, about 25 per record including the
name and the tag. A 647-commodity, 100-settlement economy would be a few
megabytes of save — large, and the same order as what the decimal form
would cost.

## 2. What failed: 4.3, the control

`docs/80` §4.3 predicted a decimal round-trip of the same values would
**fail** under Mono, and §5 said that if it passed, "`docs/78` §3 found
a single pathological literal rather than a general defect, and a codec
is over-engineering."

It passed. All 2,078 values survive `ToString("R")` → `double.Parse`
under Mono exactly.

That is not a contradiction of `docs/78` §3, and working out why is the
useful part. Mono's `ToString("R")` emits a **seventeen**-digit form
where CPython's `repr` emits the **shortest round-tripping** one — so
Mono reads back its own output correctly because its own output is
padded past the point where its parser goes wrong. The defect is not in
the round-trip. It is in **reading a decimal that some other
implementation wrote.**

## 3. The measurement that rebuilt the case

Every distinct decimal literal *as Python wrote it* into the committed
fixtures, parsed by Mono and compared with CPython bit for bit:

```
distinct python-written decimal literals: 2072
mono parses differing from python:           1
  2.299847713167259: mono 400266168eceab8e  python 400266168eceab8d
```

One in 2,072 — about 0.05%. So the position is:

| path | decimal safe? |
|---|---|
| Mono writes, Mono reads (a save reloaded in the same build) | **yes**, on this evidence |
| CPython writes, Mono reads (authored data, fixtures, seeds) | **no** — 1 in 2,072 |
| one runtime writes, a different one reads | **no**, by the same mechanism |

**So the codec stays, and the argument for it in `docs/80` §1 was
wrong.** It is not needed to stop a save/load cycle losing bits within
one build. It is needed because:

1. **The mod will be seeded from laboratory-authored data.** Every
   parameter, every reference price, every mass — written by CPython,
   read by Mono. At 0.05% and the 647-commodity scale `docs/33`
   measured, a divergence is not a risk but an arithmetic certainty,
   and it would land as a Stage 1 economy that is *almost* the
   laboratory's and never exactly it. That is the worst possible
   outcome for a project whose method is exact reproduction.
2. **The writer and the reader are not guaranteed to stay the same.**
   Unity has been moving off Mono; a save written by one runtime and
   read by another is case three above.
3. **It costs nothing now and is unpickable later.** The schema version
   is already moving.

`docs/80` §5 asked for "a cheap argument that the defect is reachable in
normal play" before keeping a codec whose control passed. Reason 1 is
that argument, it is measured rather than asserted, and it is a
*different* argument from the one the design was written on.

## 4. What this changes elsewhere

**The rule to carry forward is narrower and sharper than `docs/78` §3
stated it.** That document said "persist doubles as bits". The measured
rule is:

> **Never let a float cross an implementation boundary as decimal.**
> Mono reading Mono is fine; Mono reading CPython is not. Saves, seed
> data, fixtures, any hand-off between the laboratory and the game.

`docs/78` §3's advice is still right for persistence and it was right
for an incomplete reason.

**It also explains a puzzle in `docs/78` §2.** The one-ulp "failure"
there was the driver reading a *Python-written* fixture value through
Mono's parser — case two in the table above, met the first time anything
crossed that boundary. The diagnosis blamed the driver, correctly, and
did not generalise it. This does.

## 5. Where Phase C stands

| part | state |
|---|---|
| the planned model's arithmetic, five slices | ported, 4,151 readings, zero ulps under Mono |
| the persistence codec | built, 2,078 values exact, **not yet wired to `Scribe`** |
| the daily tick amortised across ticks | not started |
| the UI | not started |
| the `MarketValue` wealth coupling | not started |

The codec has no RimWorld reference, which is what let it be measured
here. Wiring it — one `Scribe_Values.Look` on the encoded string, the
schema bump to 3, and a schema-2 save loading with no economy state —
needs the game, as does everything left in the column above.

## 6. Cost

One C# file, one harness over the existing fixtures, and one extra
measurement written after the control came back the wrong way. The
extra measurement is the whole value of the document.
