# A review pass over the session's C#, and what it found

Not a design-then-measure slice: a read of about two thousand lines of
C# written in one session, looking for what the harnesses were not
pointed at. Tests find what you thought to check; a review finds what
you did not.

## 1. Why this was worth doing

Everything in Phase C is built and machine-checked, and the checks pass:
579 in `Economy.Core.Check`, 31 in `Economy.Drive`, both assemblies
through `verify.py`. That is coverage of the cases somebody enumerated.
It says nothing about the cases nobody did.

Three defects in this session were found by running (`docs/91` §3) and
one by reasoning (`docs/89` §4). All four were the same error —
reporting a failure for a case that does not apply — and a fourth
instance of a pattern is a reason to look for a fifth deliberately
rather than wait for it.

## 2. What it found: a latent false failure

**`RunSelfCheck` recomputed the mid-day resume verdict every time the
report was rebuilt.** The report is rebuilt once at load and again once
a day has been timed (`docs/89` §4), and the check compared the cursor
the *save* carried against the scheduler's *live* cursor.

At load those agree, which is the point. But after a resumed day
finishes, the live cursor is the phase count and the saved one is
wherever the save was taken, so the check reads:

```
FAIL mid-day resume: expected cursor 2, observed cursor 4
```

on a resume that worked perfectly. It is the same error as the three
before it, in the one place they had not been looked for: **not a case
that does not apply, but a case that has stopped applying.**

**Why the harness missed it.** `BuildPhases()` currently returns one
phase, so a day completes inside a single `AdvanceTick` and
`dayCursor` is never observed above zero. The scenario written to catch
this passed for that reason and not because the code was right — which
is worth recording, because a passing test that cannot reach the state
it names is worse than no test. Exercising the comparison directly
confirmed it:

```
after a resumed day completes, the check reads: FAIL
```

**Latent today, certain the moment the day has two phases** — which is
the next thing the port does, when the ported solvers replace the
placeholder phase. It would have arrived as a `FAIL` in the game's log,
at exactly the moment someone was trying to tell whether the new phases
worked.

## 3. The fix, and the shape of it

The resume verdict is now decided **once, at load**, and reused. It is
about a moment, and a check about a moment must not be recomputed from
state that has since moved.

That generalises past this instance, and is the fifth statement of the
family: a check is a claim about a particular time, and re-evaluating it
later against live state silently changes what it claims.

The harness now asserts the verdict does not drift as the day advances —
which is a check on the *check*, and is the only kind that would have
caught this through the public surface with a one-phase day.

## 4. What else the pass looked at and did not fault

- **`StateCodec`'s escaping.** Names are escaped on write and unescaped
  on read, and no name in the model contains a tab or newline; the
  round-trip is exercised over 2,078 real values.
- **`DayScheduler.BeginDay`'s guard.** It throws when a day is already
  in progress, which `ResumeAt` deliberately bypasses. Correct: a resume
  is not a begin.
- **`WealthCoupling`'s fallbacks.** Every degenerate input returns
  exactly 1.0 rather than propagating, checked over 2,526 combinations.
- **`EconomyReadout`'s sentinel.** `-1.0` for "uncomputable" is a
  magic number and it is confined to two methods that render it as
  `n/a`; a nullable would be cleaner and `net472` with `LangVersion 7.3`
  makes it noisier than it is worth.
- **The `"save schema"` check is nearly tautological.** By the time it
  runs, `ExposeData` has already upgraded `schemaVersion`, so it can
  only fail on a save from a *future* schema. That is a real case —
  forward-incompatibility — and the check's note oversells what it
  catches. Left as is, recorded here.

## 5. What a review cannot do

It cannot tell you the code is correct; it can only tell you what one
read of it found. The four defects this session found by other means
were each found because something ran. This one was found because
something was read, and it was the only one that no amount of running
the current code could have surfaced.

Both remain necessary. Neither substitutes for the game.

## 6. Cost

One read, one direct probe of a state the harness cannot reach, one
field, and one assertion about an assertion.
