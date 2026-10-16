# The law of value, second experiment: design

Written after `docs/148` scored the first experiment and before this one
is built or run. `docs/147` §5 said in advance that a change to the
mechanism after seeing the results is a second experiment, reported as
one. This is it.

## 1. What the first experiment showed went wrong

`docs/148` found two defects in the mechanism, not in the claim:

1. **Extinction was absorbing.** A producer or firm could move only to a
   sector another one already occupied, so an empty sector stayed empty.
   Its price then rose 2% a day for ever, every firm that needed it as
   an input planned no output, and 19 of 20 capitalist runs unravelled
   into one sector. Wright's 2008 rule moves an actor to a random
   sector, so it cannot do this. Ours lacked that.
2. **Input buyers held no buffer.** A simple-commodity producer ordered
   exactly one day's inputs. Every market was short on about two days in
   three, and on each short day the buyers downstream stood idle. Sectors
   that use inputs ran at 23 to 75% of capacity. Their incomes still
   equalised (prediction 7 passed), so their prices settled above value,
   by the labour stood idle.

## 2. The two changes, and nothing else

- **Exploration.** Each day, before the imitation step, every producer
  (SC, SH) or firm (CAP) independently, with probability `ε = 0.001`,
  moves to a uniformly drawn sector and keeps its own average. It is
  drawn from the same stream as imitation. At 500 producers that is one
  explorer every two days, so an empty sector is re-entered in about 24
  days on average. At 100 firms it is about 120 days. Either way, the
  price that rose while the sector was empty pays the entrant well.
- **An input buffer of `B = 5` days.** A producer's target holding of
  each input is `B` days of full-capacity need, and it orders the
  shortfall. A firm's target is `B` days of its planned output's inputs,
  and its input orders are scaled down, if needed, so that inputs and
  the wage bill together stay within `(1 − δ)` of its cash.

Every other parameter, the market, the measures, the twenty seeds, the
6,000 days and the 1,000-day window are those of `docs/147`. Both
changes are switches on `law_of_value.py`, off by default, so the first
experiment reproduces exactly.

Neither change lets anyone see a value or a cost. Exploration is blind.
The buffer is in physical units of the producer's own technique, which
it already used to order one day's inputs.

## 3. Predictions

`docs/147` §4's predictions 1 to 12 are restated with **unchanged
bands**. Re-fitting a band to what the first experiment showed would
make this experiment worthless. Three are added.

13. **Producers work**: in SC, the median across sectors of window
    output over capacity is at least **0.90** on every seed.
14. **No sector stays empty**: in SC and CAP, no sector is empty on more
    than **5%** of window days, on any seed.
15. **Prices track labour actually spent at least as well as technical
    labour**: in SC, `Δ(v_real) ≤ Δ(v) + 0.01` on every seed. Here
    `v_real` solves `v = l_eff + A v` with `l_eff_i = l_i / u_i`, and
    `u_i` is sector `i`'s window output over capacity. In the first
    experiment this was found after the fact. Here it is stated
    beforehand.

## 4. Reading the outcome

- **3 and 13 pass.** With producers working, prices settle on technical
  labour values. The first experiment's gap was idle labour.
- **13 passes, 3 fails, 15 passes.** Producers work, but something else
  holds prices off values, and labour actually spent still explains
  them better. That something must then be found.
- **13 fails.** The buffer does not stop idling, so prices cannot be
  expected to reach technical values. 15 is then the informative one.
- **14 fails.** Exploration is too slow at `ε = 0.001` for the
  capitalist arm, and 9 to 11 are void again.
- **CAP still collapses with 14 passing.** The capitalist arm fails for
  a reason other than extinction, and that is a finding about this
  economy that the results must name.
