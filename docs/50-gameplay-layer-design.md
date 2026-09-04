# Phase D: hired workers and class consequences: design

Written before any of it is built, and before the Stage 1 port that will
have to carry it. `HANDOFF.md` has listed "Phase D has no design" among the
three things most likely to derail the project since the scale test, and
its advice was to write the design *early*, while the economics is still
malleable, "rather than discovering at the end that the simulation computes
the wrong things for the game." This is that document. It is a design for
what a player *does*, and it is deliberately written against the model that
exists rather than the one it might be nicer to have.

Two of the ten concepts in the project's stated direction have never been
started: *class consequences for workers and the player colony as
collective owner*, and *hired outside workers*. Everything else is either
demonstrated in Python or shipped as a static figure. Those two are the
ones that are gameplay rather than accounting, and this document is about
them only.

## 1. The player's position

The colony is a **collective owner**. Colonists are not wage workers and
this design does not make them any: they own their product jointly, they
are not paid, and nothing about their needs is tied to a wage. That was
decided at the start (`HANDOFF.md`, "Project direction") and it stands,
because a colony of wage-workers has no employer, and a game in which the
player is both employer and employed of the same pawns is a bookkeeping
fiction with no decision in it.

What the colony *can* do is enter three economic relations with the world
outside it, all of which vanilla RimWorld either lacks or leaves
illegible:

1. **Sell**, into a regional market with a price of its own, where the
   colony's output can matter.
2. **Hire**, taking on outside workers who are a distinct class: they are
   paid, they do not own what they make, and they leave.
3. **Own ground**, holding deposits whose cost advantage over the margin is
   rent, and whose exhaustion moves the margin.

Vanilla has the first in a degenerate form (a trader's stock is rolled and
discarded every thirty days, and nothing the player sells affects anything
later), has the second not at all (Ideology's slaves are the opposite of a
wage worker: unpaid and owned), and has the third as an infinite drill.

The design principle for all three is the one the whole project rests on:
**the four ledgers stay apart, and the player is shown which one a figure
comes from.** Labor value, market price, surplus value and rent are
different things, and a game that collapsed them into "profit" would be
teaching the wrong lesson with the right numbers.

## 2. What a player does

### 2.1 Hire a worker

A hired worker is a pawn who arrives under a **contract**: a term in days,
a wage per day, and a form of payment. They take work like a colonist
while the contract runs, are paid at the end of each day, own nothing they
make, and leave when the term ends, or earlier.

**The wage is not a slider.** It is the regional wage: the subsistence
basket at the region's current prices, times one plus the regional wage
premium, which is what the reserve-army rule in `docs/46` computes today.
The player sees it as an offer the region makes, and can offer above or
below it. Above the regional wage, workers come; at it, some come; below
it, fewer, and those who came leave sooner. The elasticity is a design
coefficient, not a fact about people, and it is swept rather than
calibrated, the way `docs/40` §1 treated the recreation quantity.

**Payment is silver or explicit in-kind, never implicit.** Silver leaves the
colony's stockpile as a stack, the way a trade does. In-kind payment is the
basket itself: so many meals, so much clothing, so much medicine, at the
quantities `docs/28` derived. A worker paid in-kind consumes the basket;
one paid in silver spends it in the regional market when they leave. Both
are the same wage in different forms, and the game says which form was
used. What is forbidden is the vanilla pattern, where a visitor eats the
colony's food and the food's cost is not recorded anywhere.

**The class relation is what the contract makes visible.** For every
contract the game can show, in work-ticks, the labor the worker performed,
the value of their labor-power (the basket at social labor values, from
the region's value solve), and the difference. That difference is surplus
value, and the colony appropriated it. The realized form, whether the
colony *sold* what the worker made and at what price, is a separate
figure, in silver, on a separate line, because a commodity can contain
surplus labor and fail to realize it in a glut (`docs/18`, the glut as
layoff).

The interesting decision is the one this creates: hiring is cheap when the
regional reserve army is large and the premium is negative, and dear when
the region is booming. A colony that hires a lot in a small region *is* the
boom: its own demand for labor raises the regional wage against it. That
is `docs/47`'s result — the premium reaches wage-good prices through demand
— arriving at the player as something that happens to them.

### 2.2 Sell into a market that remembers

The colony sells into its **region**, at the region's **market price**,
which is the Stage 0 price: formed from regional inventory and unmet
demand, anchored to cost, and separate from `MarketValue`. What the colony
sells stays sold: it is regional inventory, it lowers the regional price,
and a colony that dumps a quadrum of yayo on a small region sees the price
fall by the elasticity the laboratory has measured since `docs/06` and
recover on the timescale it has measured since. Distant regions barely
move, because the route is costly and slow, and arbitrage moves stock
toward the spread on the route's capacity.

Two readings sit beside the price whenever the player sells: the **labor
value** of the thing (the social value from the region's solve, which
Labor Content already shows as a static figure), and the **price of
production** (the classical price at a uniform rate of profit, from
`docs/26`). The player is not asked to understand either; they are shown
so that the player can notice, over time, that some things sell above
their value and some below, and that the direction is systematic. That is
the seam `FINDINGS.md` found, made a thing a player can see.

### 2.3 Own ground, and collect rent

The colony's tile holds deposits, with grades. Extraction by hired workers
draws down the cheap grade first and moves the marginal cost when it
exhausts (`docs/15`, `docs/16`). When the colony's deposit is cheaper than
the most expensive deposit the region is working, the colony earns
**differential rent** on every unit it extracts, and the game says so: the
income from a unit of chemfuel is wage, surplus value and rent, on three
lines, in the ledger each belongs to. Rent is in silver, because it is a
share of the price, and the surplus it is a deduction from is in
work-ticks, and they are not added.

The absolute rent bound (`docs/43`) is a reading, not an income, for the
reason `docs/42` §2 gave: nothing in the model has a landlord to pay. The
colony *is* a landlord, and this is the first place the model has one. So
the omission that blocks absolute rent as a flow, producer-level cash, is
on this design's critical path (§7).

### 2.4 Face the consequences

The consequences are the part the project has never specified, and they
are where the design is least sure of itself. Four are proposed; each is a
mechanism the model can already compute, attached to something a player
already cares about.

**Workers compare their wage to the standard.** A hired worker's mood
reads the wage against the regional *habitual* standard, not against the
colony's generosity. A wage below the value of labor-power is a grievance
that grows with its duration; a wage above it is not a joy that grows,
because the standard rises to meet it (`docs/51`, habituation). The game's
own mood system is the display; the model supplies the number.

**Workers leave, and take the wage with them.** A worker whose contract
ends, or who quits, returns to the region's labor pool and the region's
wage follows what the colony paid. Worker mobility between regions, which
`docs/46` §8 left out, is *exactly* what a hired worker is, and the colony
is the vehicle for it.

**Factions notice.** A faction whose members the colony pays below value
loses goodwill in proportion to the deviation and the head-count; one paid
above it gains, less. This is the cheapest consequence to build because
goodwill already exists, and the most dangerous to tune, because goodwill
already drives raids.

**The colony's own class position is reported.** A colony tab shows what
share of the colony's product was made by hired labor, how much surplus
value it appropriated, how much it realized, and what it paid in rent to
nobody. A colony that makes most of its product with hired labor is a
capitalist, and the tab says so in those words. What the player does about
that is the player's business. The game does not moralize; it labels.

## 3. What reaches the player, from where

| concept | already reaches a player as | this layer adds |
|---|---|---|
| labor value | Labor Content's two static info-card rows | the region's *solved* value beside the authored one, moving when techniques move |
| market price | nothing; `MarketValue` is static and drives wealth | a regional `MarketPrice` per commodity, never written back to `MarketValue` |
| price of production | nothing | a reading beside the market price on the sell screen |
| surplus value | nothing | per contract and per colony, in work-ticks, apart from money |
| rent | nothing | per deposit, in silver, on its own line |
| the wage | nothing (visitors eat for free) | the regional wage as an offer, the premium as a reading |

The two reference points the handoff insists on, average conditions for
value and marginal conditions for price and rent, are labelled wherever
they appear. Nothing here is a single "worth" number.

## 4. What it deliberately does not do

- **It does not turn colonists into wage workers.** Ever. A colonist's
  labor is counted in the colony's product at value; no wage is imputed to
  it and no surplus is computed on it. The class relation is between the
  colony and the people it hires, not inside the colony.
- **It does not touch `MarketValue`.** The regional price is a separate
  stat. Storyteller wealth reads `MarketValue` and raid strength reads
  wealth; a dynamic price fed into it would couple gluts to raids. That
  constraint is the second of the handoff's three derailers and this design
  leaves it exactly where it is.
- **It does not simulate the colony as a Stage 0 producer.** The colony's
  production is whatever the player's pawns actually did; the model reads
  it as a flow into regional inventory and does not plan it. The model
  plans the *other* producers in the region.
- **It does not model slaves.** Ideology's slavery is a different relation
  and it is the contrast case: no wage, ownership of the person, and the
  product owned outright. The class tab can count slave labor beside hired
  labor and colonist labor, so the three relations are visible together,
  but nothing about slavery is changed.
- **It does not roll dice for wages.** Who arrives, at what wage, for how
  long, is a function of the region's state and a stable fingerprint, the
  way `economy_mod` already derives settlement profiles. Determinism is
  the runtime's contract with the laboratory and the gameplay layer does
  not get to break it.
- **It does not price the closed-default goods.** A modded good that the
  classifier cannot place stays an *unmodelled commodity* at vanilla
  behaviour, exactly as decided in "Mod compatibility".

## 5. What Stage 0 must still provide

The design puts three of the standing omissions on the critical path, in
this order:

1. **Habituation of a sustained premium into the basket** (`docs/51`).
   Without it, a colony that pays above the regional standard raises
   worker mood indefinitely, and the "workers compare their wage to the
   standard" consequence has no standard to move.
2. **Worker mobility between regions**, in the narrow form of labor
   entering and leaving a region's pool with a wage attached. The colony
   is the first mover; the general case can wait.
3. **Producer-level cash**, so that the colony can be a producer that holds
   silver, pays wages from it, and collects rent into it. This is also the
   blocker for absolute rent as a flow (`docs/43`), and it is the largest
   of the three.

Not on the path: monopoly rent proper, credit and bankruptcy, moral
depreciation, more than two laboratory regions. None of the four decisions
in §2 needs them.

## 6. What Stage 1 must carry

The port (`docs/53`) has to bring across, in this order, because each is
what the next one reads:

- the value solve, per region, so that a hired worker's labor-power has a
  value;
- the basket and the wage, so that the offer has a number;
- the regional price, so that a sale has a price and the value has
  something to deviate from;
- the reserve-army premium and habituation, so that the colony's hiring
  moves the wage and the standard.

The price system (`prices_of_production`) is a reading and can come last.
Department I, exit, and the sweep never need to reach the game at all.

## 7. Predictions

Written so that the first playable slice can score them.

1. **Hiring will be the decision players engage with**, not selling.
   Selling is a vanilla habit with a new number beside it; hiring is a new
   act with a visible consequence. If players ignore the contract screen,
   the wage offer is not legible enough, not the concept.
2. **A small region will be dominated by a mid-game colony's hiring.** The
   laboratory's regional labor pool is one worker-day a day at three times
   equilibrium employment. A colony hiring five workers in such a region
   moves the employment rate by more than the boom scenario does, and the
   premium follows. This will need the pool sized from the settlement
   profile, not the laboratory constant.
3. **The goodwill consequence will be the one that needs retuning first.**
   It is the only consequence wired into a system that already has teeth.
4. **The class tab will be read as a score by some players and as an
   accusation by others.** The wording matters more than the arithmetic.
   The design says label, not judge, and the first wording will be wrong.
5. **In-kind payment will be preferred early and silver late**, because a
   young colony has meals and no silver and an old one the reverse. If it
   is the other way round, the basket quantities are wrong for the game
   even if they are right for the model.

## 8. What would make this wrong

If the value solve cannot run per region at game scale, the hired worker's
labor-power has no value and §2.1's central reading is gone; `docs/33`
says it can, at 647 commodities, in Python, and the port will say whether
it can in C#. If the regional labor pool cannot be sized from anything the
world provides, prediction 2 becomes a tuning problem with no ground
truth. And if the wealth coupling cannot be kept out, none of the market
side can ship, and the layer reduces to §2.1 alone, which would still be
worth having.
