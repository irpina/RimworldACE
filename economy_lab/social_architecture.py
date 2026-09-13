"""Wright's social-architecture model, as an instrument for docking.

Ian Wright, *The social architecture of capitalism*, Physica A **346**
(2005) 589-620.  This module exists to audit our own model's *wiring*
against his (``docs/97``), not to become part of it.  It imports nothing
from :mod:`economy_lab.model` and nothing outside the standard library,
and no rule here can reach the laboratory's behaviour.

**This is a reconstruction, not a transcription.**  ``docs/97`` section 0
grades what could be obtained: the ontology, the three parameters, the
nine rules' *names* and their order are corroborated across sources; the
exact body of each rule is **not**, because every full-text route was
blocked by the egress proxy.  The bodies below are the most natural
reading of the corroborated description, and they are marked
``RECONSTRUCTED`` where that is so.  Until the paper is read, results from
this module are evidence about *an SA-family model*, and become evidence
about *Wright's* model only once each body is checked.  No exponent from
here may be reported as agreeing with Wright before then.

Money is integer coins throughout.  Every rule is a transfer of coins
between two accounts, so conservation is exact rather than approximate --
which is the point of a model whose whole content is who may take money
from whom.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

#: An actor's employer index means: ``None`` -- unemployed; ``i`` itself --
#: the owner of a firm; any other ``j`` -- an employee of ``j``.
UNEMPLOYED = None


@dataclass
class Economy:
    """N actors, M coins, and a wage interval.  Wright's three parameters.

    ``seed`` makes a run reproducible; the model is stochastic by design,
    so a run is a draw and a *result* is a property of many draws or of a
    long one.
    """

    actors: int = 1000
    coins: int = 100_000
    wage_max: int = 100
    seed: int = 0

    #: Which actors may be drawn as the hirer (``docs/98`` section 3).
    #: ``"owners"`` -- only an actor who could own a firm, i.e. an employer
    #: or an unemployed actor.  Attachment is then proportional to the
    #: owner's wealth alone, which grows about linearly with firm size.
    #: ``"all"`` -- employees too, so a firm is drawn in proportion to its
    #: size *and* its owner's wealth.  That is super-linear preferential
    #: attachment, and it does not produce a power law; it produces a
    #: monopoly.  Which one Wright intends is **unobtained**.
    candidate_pool: str = "owners"

    #: What the firing rule tests the wage bill against (``docs/98`` s.3).
    #: ``"revenue"`` -- the firm's takings over the trailing month, which
    #: is the corroborated wording ("if *current revenues* do not cover
    #: the expected wage bill").  ``"funds"`` -- the owner's whole purse,
    #: which lets an owner who has accumulated one buffer indefinitely and
    #: sends the model to monopoly.
    firing_test: str = "revenue"

    money: List[int] = field(default_factory=list)
    employer: List[Optional[int]] = field(default_factory=list)
    wage: List[int] = field(default_factory=list)
    market: int = 0
    steps: int = 0

    #: Flows for the month in progress, reset by :meth:`month`.
    wages_paid: List[int] = field(default_factory=list)
    profit: List[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        share = self.coins // self.actors
        self.money = [share] * self.actors
        # Any remainder from the division sits in the market pool rather
        # than being silently lost, so `total_coins` is exactly `coins`.
        self.market = self.coins - share * self.actors
        self.employer = [UNEMPLOYED] * self.actors
        self.wage = [0] * self.actors
        self.wages_paid = [0] * self.actors
        self.profit = [0] * self.actors
        self._staff: Dict[int, set] = {}
        self.revenue = [0] * self.actors

    # ------------------------------------------------------------ state

    def total_coins(self) -> int:
        """Every coin in the model.  Invariant under every rule."""
        return sum(self.money) + self.market

    def employees(self, owner: int) -> List[int]:
        return list(self._staff.get(owner, ()))

    def _attach(self, worker: int, owner: int) -> None:
        self.employer[worker] = owner
        if worker != owner:
            self._staff.setdefault(owner, set()).add(worker)

    def _detach(self, worker: int) -> None:
        owner = self.employer[worker]
        if owner is not None and owner != worker:
            staff = self._staff.get(owner)
            if staff is not None:
                staff.discard(worker)
        self.employer[worker] = UNEMPLOYED
        self.wage[worker] = 0

    def firm_sizes(self) -> List[int]:
        """Employees plus owner, for every firm currently trading."""
        counts: Dict[int, int] = {}
        for i, e in enumerate(self.employer):
            if e is not None:
                counts[e] = counts.get(e, 0) + 1
        return sorted(counts.values(), reverse=True)

    def check_staff_index(self) -> bool:
        """The maintained index agrees with a scan of ``employer``."""
        scanned: Dict[int, set] = {}
        for i, e in enumerate(self.employer):
            if e is not None and e != i:
                scanned.setdefault(e, set()).add(i)
        live = {k: v for k, v in self._staff.items() if v}
        return live == scanned

    def classes(self) -> Tuple[int, int, int]:
        """``(employers, employees, unemployed)`` -- emergent, not assigned."""
        owners = {e for i, e in enumerate(self.employer) if e is not None}
        employers = len(owners)
        employed = sum(
            1
            for i, e in enumerate(self.employer)
            if e is not None and i not in owners
        )
        return employers, employed, self.actors - employers - employed

    def unemployment_rate(self) -> float:
        return self.classes()[2] / self.actors

    # ------------------------------------------------------------ rules

    def _hire(self, a: int) -> None:
        """H1 -- RECONSTRUCTED.

        An unemployed actor looks for work.  The hirer is drawn from every
        actor able to advance a wage, with probability proportional to the
        money it holds -- which is what makes a large firm more likely to
        grow than a small one, and is the candidate mechanism for the
        power-law firm size.  If the actor drawn is itself unemployed, a
        new firm is born; this is the "with lower probability, two
        unemployed actors form a small firm" branch, and it falls out of
        the same draw rather than needing a rule of its own.
        """
        if self.employer[a] is not None:
            return
        # "All employers hire if they have sufficient ex ante funds to
        # pay the average wage" -- the mean of the interval, not its top.
        # Against `wage_max` the model deadlocks at a symmetric start:
        # every actor holds exactly the mean and nobody clears the bar.
        threshold = self.wage_max / 2.0
        if self.candidate_pool == "owners":
            pool = (
                c
                for c in range(self.actors)
                if self.employer[c] is None or self.employer[c] == c
            )
        elif self.candidate_pool == "all":
            pool = range(self.actors)
        else:
            raise ValueError(f"unknown candidate_pool {self.candidate_pool!r}")
        candidates = [
            c for c in pool if c != a and self.money[c] > threshold
        ]
        if not candidates:
            return
        weights = [self.money[c] for c in candidates]
        hirer = self.rng.choices(candidates, weights=weights, k=1)[0]
        if self.employer[hirer] is None:
            # A new firm: the hirer becomes its owner.
            self._attach(hirer, hirer)
        # If the actor drawn is somebody's employee, its employer hires.
        owner = self.employer[hirer]
        self._attach(a, owner)
        self.wage[a] = self.rng.randint(1, self.wage_max)

    def _spend(self, a: int) -> None:
        """E1 -- RECONSTRUCTED.  Money leaves an actor for the common pool
        of latent demand.  Nobody spends *at* anybody: what a firm earns
        is not what its own customers paid it, which is the model's way of
        saying that a sale is social before it is bilateral."""
        if self.money[a] <= 0:
            return
        spend = self.rng.randint(1, self.money[a])
        self.money[a] -= spend
        self.market += spend

    def _sample(self, a: int) -> None:
        """M1 -- RECONSTRUCTED.  An actor in a firm draws revenue from the
        pool to its owner, bounded by what the pool happens to hold.  This
        is the sense in which an employee "adds value": the firm's income
        scales with how many actors draw for it, and is a *draw* rather
        than a certainty."""
        owner = self.employer[a]
        if owner is None or self.market <= 0:
            return
        sample = self.rng.randint(1, self.market)
        self.market -= sample
        self.money[owner] += sample
        self.profit[owner] += sample
        self.revenue[owner] += sample

    def _fire(self, a: int) -> None:
        """F1 -- RECONSTRUCTED.  The solvency constraint, and the whole
        reason firm death is endogenous here: an owner whose funds do not
        cover the wage bill sheds employees until they do, and an owner
        with nobody left stops trading.

        This is the rule ``docs/97`` A3 says our lab has no counterpart
        for."""
        owner = self.employer[a]
        if owner is None:
            return
        staff = self.employees(owner)
        staff.sort()
        if self.firing_test == "revenue":
            available = self.revenue[owner]
        elif self.firing_test == "funds":
            available = self.money[owner]
        else:
            raise ValueError(f"unknown firing_test {self.firing_test!r}")
        while staff and available < sum(self.wage[i] for i in staff):
            fired = staff.pop(self.rng.randrange(len(staff)))
            self._detach(fired)
        if not staff:
            # The firm ceases trading; its owner rejoins the unemployed.
            self.employer[owner] = UNEMPLOYED
            self._staff.pop(owner, None)

    def _pay(self, a: int) -> None:
        """W1 -- RECONSTRUCTED.  The owner advances the wage out of its own
        funds.  A month is N steps and each actor is selected about once,
        so a wage is paid about once a month."""
        owner = self.employer[a]
        if owner is None or owner == a:
            return
        due = self.wage[a]
        if due <= 0 or self.money[owner] < due:
            return
        self.money[owner] -= due
        self.money[a] += due
        self.wages_paid[a] += due
        self.profit[owner] -= due

    def step(self) -> None:
        """One application of the simulation rule, in Wright's order:
        select, hire, spend, sample, fire, pay."""
        a = self.rng.randrange(self.actors)
        self._hire(a)
        self._spend(a)
        self._sample(a)
        self._fire(a)
        self._pay(a)
        self.steps += 1

    def month(self) -> None:
        """N applications of the rule (Wright's definition of a month)."""
        self.wages_paid = [0] * self.actors
        self.profit = [0] * self.actors
        self.revenue = [0] * self.actors
        for _ in range(self.actors):
            self.step()

    def run(self, months: int) -> None:
        for _ in range(months):
            self.month()

    # -------------------------------------------------------- readings

    def incomes(self) -> List[int]:
        """The month's income per actor: wages for employees, the residual
        of draws over the wage bill for owners."""
        return [
            self.wages_paid[i] + self.profit[i] for i in range(self.actors)
        ]


# ------------------------------------------------------------ statistics
# Plain Python: the project has no third-party dependency and this slice
# does not introduce one (docs/97 section 6).


def gini(values: List[float]) -> float:
    """Gini coefficient.  0.0 when every value is equal."""
    xs = sorted(v for v in values if v >= 0.0)
    n = len(xs)
    total = sum(xs)
    if n == 0 or total <= 0.0:
        return 0.0
    weighted = sum((i + 1) * x for i, x in enumerate(xs))
    return (2.0 * weighted) / (n * total) - (n + 1.0) / n


def top_share(values: List[float], fraction: float = 0.1) -> float:
    """The share of the total held by the top ``fraction`` of holders."""
    xs = sorted((v for v in values if v > 0.0), reverse=True)
    total = sum(xs)
    if not xs or total <= 0.0:
        return 0.0
    k = max(1, int(len(xs) * fraction))
    return sum(xs[:k]) / total


def hill(values: List[float], tail: float = 0.1) -> Optional[float]:
    """Hill estimator of the Pareto tail index over the top ``tail``.

    Returned as a bare number.  ``docs/97`` section 0 forbids reporting it
    as agreeing with Wright's exponent until the paper is read; it is here
    to say whether a tail is heavy at all, not to match a figure.
    """
    import math

    xs = sorted((v for v in values if v > 0.0), reverse=True)
    k = int(len(xs) * tail)
    if k < 2:
        return None
    cutoff = xs[k]
    if cutoff <= 0.0:
        return None
    acc = sum(math.log(x / cutoff) for x in xs[:k])
    if acc <= 0.0:
        return None
    return k / acc
