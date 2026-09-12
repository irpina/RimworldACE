# Stage 1: persisting the economy exactly: design

Written before implementation, which `docs/79` failed to do and this
document restores. Phase C's engineering half begins here, and this is
the piece of it that can be built and verified outside the game.

## 1. Why this first, and why it is not obvious

`HANDOFF.md` lists "the full economic state through save and load" as
Phase C work and the existing shell already persists something: schema
version, completed days, last tick, and the settlement profiles, through
`Scribe_Values.Look` and `Scribe_Collections.Look`. Extending that to
the economy looks like more of the same.

It is not, because of `docs/78` §3. **Mono's `double.Parse` is not
correctly rounded**, and `Scribe_Values.Look<double>` writes a `double`
as decimal text and reads it back with a parse. RimWorld runs on Mono.
So the obvious implementation silently loses the last bit of some
values on every save/load cycle, and this project's entire method — the
exactness `docs/44` calls "the most productive constraint in the
project", the 4,151 zero-ulp readings the port has just earned — stops
at the save file.

The failure mode is nasty in a specific way: it is *rare and
state-dependent*. Most decimals round-trip correctly. The one measured
in `docs/78` §3 needed sixteen significant digits. So a naive
implementation passes casual testing, passes a short reload check, and
breaks a long game months later in a way nobody can reproduce.

## 2. The rule

**Persist a double as its bits.**

    long bits = BitConverter.DoubleToInt64Bits(value);
    double value = BitConverter.Int64BitsToDouble(bits);

`long` round-trips exactly through `Scribe_Values` because it is written
as an integer and parsed as one, and integer parsing is exact. This is
not a trick; it is what the IEEE 754 interchange format is for.

Three consequences, stated so they are chosen rather than discovered:

- **Save files stop being human-readable for these fields.** A price
  becomes `4002661b3af514a2`. That is a real cost and it is accepted: a
  reader who needs the number can convert it, and a model that is
  bit-exact in the laboratory and not in the save is worse than an
  unreadable field.
- **The schema version must move.** A save written with decimal doubles
  and read as bits would be catastrophic rather than wrong-by-a-ulp.
  Schema 2 is the current shell; the economy state lands at schema 3 and
  a schema-2 save loads with no economy state rather than a garbled one.
- **It applies to every float that feeds the model**, not only prices:
  labor values, purses, capacities, expectations, the premium, the
  standard. A single decimal field is enough to break determinism.

## 3. What is built

```
economy_mod/Source/Economy.Core/StateCodec.cs
```

A codec with **no RimWorld reference**, so it can be tested here:

- `StateCodec.Encode(double) -> string` and `Decode(string) -> double`,
  the 16-hex-digit interchange form;
- `EconomySnapshot`, a plain object holding the state the model needs to
  resume — the labor values, and per region the prices, inventories,
  purses, premium and standard;
- `StateCodec.Write(EconomySnapshot) -> string` and
  `Read(string) -> EconomySnapshot`, a flat line-oriented format whose
  only floating-point representation is the hex one.

The RimWorld side — `Scribe_Values.Look(ref encoded, ...)` on the string
the codec produces — is a later step and needs the game. Keeping the
codec free of `Verse` is what makes the hard part testable now.

**Why a string and not `Scribe` per field.** One `Scribe_Values.Look` on
one encoded blob is one place for the format to be right, versus one per
field and a new chance to write a `double` directly every time someone
adds a field. The codec is the only thing that knows how a number is
spelled.

## 4. Predictions

4.1 Every double in the laboratory's committed fixtures round-trips
through `Encode`/`Decode` **to the bit** under Mono — every labor value,
price, inventory, purse and coefficient across all five fixture
directories, which is several thousand distinct values including the
one `docs/78` §3 caught Mono mis-parsing.

4.2 The same values round-trip through `Write`/`Read` on a whole
snapshot, so the container does not undo what the encoding gets right.

4.3 A decimal round-trip of the same values **fails** — at least one
value differs — under Mono. This is the control. If it passes, Mono's
parser is better than `docs/78` §3 measured and the codec is
unnecessary; that would be a good outcome and it should be measured
rather than assumed, because the whole design rests on that one defect
being real.

4.4 The laboratory is unmoved: 322 metrics at zero delta. Nothing in
`economy_lab/` changes.

## 5. What would make this wrong

If 4.3 passes — decimal round-trips exactly on every value tested — then
`docs/78` §3 found a single pathological literal rather than a general
defect, and a codec is over-engineering. The honest response would be to
keep the codec anyway *only* if a cheap argument shows the defect is
reachable in normal play, and to say so.

If 4.1 fails, `BitConverter` is not doing what it says, which would be a
Mono bug of a different and much more serious order.

If the encoded form turns out to be enormous — a 647-commodity, 100-
settlement economy is the scale `docs/33` measured — then the save-size
cost needs stating. Sixteen hex characters against a typical decimal's
eight to seventeen is roughly a doubling on the worst case and nothing
on the common one; it should be measured, not assumed.

## 6. What this still cannot do

It cannot save or load a RimWorld game. It builds the part that is
provably correct or not, leaves the part that needs `Verse` for a
session with the game, and gives that session a codec it does not have
to think about. The reload-determinism check already in
`EconomyWorldComponent` is the instrument that will confirm the join,
and it is already written.

## 7. Cost

One C# file, a round-trip harness over the existing fixtures, and a
measurement of the decimal control. No new fixtures: the port's five
directories are already thousands of real laboratory doubles, which is a
better corpus than anything invented here.
