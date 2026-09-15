"""Wright's Social Relations model, transcribed from the paper.

Ian Wright, *The social architecture of capitalism*, Physica A **346**
(2005) 589-620 (arXiv:cond-mat/0401053v2).  This module exists to audit
our own model's *wiring* against his (``docs/97``), not to become part of
it.  It imports nothing from :mod:`economy_lab.model` and nothing outside
the standard library, and no rule here can reach the laboratory's
behaviour.

**This is now a transcription, not a reconstruction.**  ``docs/97`` §0
graded the rule bodies *unobtained* and the first version of this module
guessed them; ``docs/100`` records the six places the guess was wrong and
what each cost.  The bodies below are the paper's, and each carries the
rule's own label so it can be checked line by line against §2 of the
paper.

Wright's ontology, from §2:

* ``m[i]`` -- actor *i*'s money, a **real** number in coins.  The total is
  a constant ``M``; with the market pool ``V`` holding what has been spent
  and not yet earned, ``sum(m) + V == M`` at every step.
* ``employer[i]`` -- the integer employer index ``e_i``, with
  ``0 <= e_i <= N`` and ``e_i != i``.  Here ``None`` stands for the
  paper's ``0``.
* The three classes are **derived**, never assigned: a capitalist has
  employees and no employer, a worker has an employer, an unemployed
  actor has neither.

Wages are drawn from the *discrete* interval ``[wage_min, wage_max]``
afresh at every payment -- the paper is explicit that wages are not fixed
per employment, and §2.6 defends the simplification.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

#: The paper's ``e_i = 0``: no employer.  Both capitalists and the
#: unemployed carry it; what separates them is whether anyone carries
#: *their* index.
NO_EMPLOYER = None


#: The exchange rules M1 can use (docs/115).  A 2x2 over Wright's two
#: named ingredients: revenue proportional to headcount (the law of
#: value) and a random draw (contingency).
MARKET_RULES = ("wright", "neutral", "fixed", "fixed_neutral")


@dataclass
class History:
    """What Wright's seven measures need, recorded as the run goes.

    The instrument was a state machine with no memory; four of the seven
    facts are about events over time (docs/111 section 1).  Firm sizes
    are pooled across every month, which is what his section 3.2 does --
    "data collected over 15 simulated years" -- and what makes the
    exponent an estimate rather than a snapshot.
    """

    #: Fact 1, every firm's size at every month end, pooled.
    firm_sizes: List[int] = field(default_factory=list)
    #: Fact 4, one count per month.
    demises_per_month: List[int] = field(default_factory=list)
    #: Facts 3 and 5, one gross M1 total per year.
    gdp: List[float] = field(default_factory=list)
    #: Fact 2, log size ratios, one per trading firm per year.
    firm_growth: List[float] = field(default_factory=list)
    #: Fact 6, one income per actor per year.
    incomes: List[float] = field(default_factory=list)
    #: Fact 7, one rate per firm trading at each year close.
    profit_rates: List[float] = field(default_factory=list)
    #: The shares, yearly.
    wage_shares: List[float] = field(default_factory=list)

    def gdp_growth(self) -> List[float]:
        """Log GDP growth, ``ln(X_t / X_{t-1})``."""
        return [
            math.log(self.gdp[i] / self.gdp[i - 1])
            for i in range(1, len(self.gdp))
            if self.gdp[i] > 0.0 and self.gdp[i - 1] > 0.0
        ]

    def recessions(self) -> List[int]:
        """Durations in years.  Wright: a recession begins when
        ``X_t/X_{t-1} < 1`` and ends when ``X_{t+k}/X_{t+k-1} >= 1``."""
        durations: List[int] = []
        running = 0
        for i in range(1, len(self.gdp)):
            if self.gdp[i] < self.gdp[i - 1]:
                running += 1
            elif running:
                durations.append(running)
                running = 0
        if running:
            durations.append(running)
        return durations


@dataclass
class Economy:
    """The SR model: ``N`` actors, ``M`` coins, and a wage interval.

    Wright's three parameters, at the paper's reported values -- "In all
    reported results, N = 1000 and M = 100000 ... the wage interval is set
    to omega = [10, 90]" (§3), so the average wealth is 100 coins and the
    average wage 50, half the mean wealth.
    """

    actors: int = 1000
    coins: float = 100_000.0
    wage_min: int = 10
    wage_max: int = 90
    seed: int = 0
    #: Which exchange rule M1 uses (docs/115).  ``"wright"`` is the
    #: paper's and the default; the others ablate one or both of its two
    #: ingredients -- sampling frequency proportional to headcount (the
    #: law of value) and a random draw (contingency).
    market_rule: str = "wright"

    money: List[float] = field(default_factory=list)
    employer: List[Optional[int]] = field(default_factory=list)
    market: float = 0.0
    steps: int = 0

    #: Flows for the month in progress, reset by :meth:`month`.
    wages_paid: List[float] = field(default_factory=list)
    revenue: List[float] = field(default_factory=list)

    #: Whether to record the history Wright's seven measures need
    #: (docs/111).  Off by default: recording allocates and appends but
    #: never touches the RNG, so a recorded run and an unrecorded one
    #: follow identical trajectories.
    record: bool = False

    def __post_init__(self) -> None:
        if not self.wage_min <= self.wage_max:
            raise ValueError("wage_min must not exceed wage_max")
        if self.market_rule not in MARKET_RULES:
            raise ValueError(f"unknown market rule {self.market_rule!r}")
        self.rng = random.Random(self.seed)
        # SR1: "Allocate M/N coins to each of the N actors.  Set e_i = 0
        # for all i (i.e. all actors are initially unemployed)."
        share = self.coins / self.actors
        self.money = [share] * self.actors
        self.employer = [NO_EMPLOYER] * self.actors
        self.market = 0.0
        self._staff: Dict[int, Set[int]] = {}
        self.wages_paid = [0.0] * self.actors
        self.revenue = [0.0] * self.actors
        #: Gross M1 receipts for the year, *before* wages.  Facts 3 and 7
        #: need revenue gross; ``revenue`` above is already net of the
        #: wage bill because ``_pay`` subtracts from it (docs/111 s2).
        self.year_gross = [0.0] * self.actors
        self.year_wages_out = [0.0] * self.actors
        self.year_wages_in = [0.0] * self.actors
        #: Demises in the month in progress: firms that fired everybody.
        self.month_demises = 0
        self.months_elapsed = 0
        self.history = History() if self.record else None
        self._traded_this_year: Set[int] = set()
        self._previous_year_sizes: Dict[int, int] = {}

    @property
    def average_wage(self) -> float:
        """``<w> = (w_a + w_b) / 2``."""
        return (self.wage_min + self.wage_max) / 2.0

    # ------------------------------------------------------------ state

    def total_coins(self) -> float:
        """``sum(m) + V``.  Invariant at ``M`` under every rule."""
        return sum(self.money) + self.market

    def employees(self, owner: int) -> List[int]:
        return sorted(self._staff.get(owner, ()))

    def _attach(self, worker: int, owner: int) -> None:
        self.employer[worker] = owner
        self._staff.setdefault(owner, set()).add(worker)

    def _detach(self, worker: int) -> None:
        owner = self.employer[worker]
        if owner is not None:
            staff = self._staff.get(owner)
            if staff is not None:
                staff.discard(worker)
                if not staff:
                    # "existing firms may cease trading when all employees
                    # are fired and the capitalist owner enters the
                    # unemployed class" -- which here is automatic: an
                    # actor with no employees and no employer is in U.
                    del self._staff[owner]
        self.employer[worker] = NO_EMPLOYER

    def is_capitalist(self, i: int) -> bool:
        """``C = {x : W_x != {} and e_x = 0}``."""
        return bool(self._staff.get(i)) and self.employer[i] is None

    def is_worker(self, i: int) -> bool:
        """``W = {x : W_x = {} and e_x != 0}``."""
        return self.employer[i] is not None

    def is_unemployed(self, i: int) -> bool:
        """``U = {x : W_x = {} and e_x = 0}``."""
        return self.employer[i] is None and not self._staff.get(i)

    def firm_sizes(self) -> List[int]:
        """Employees per trading firm.  The paper counts the employees;
        the owner is a capitalist, not an employee."""
        return sorted(
            (len(s) for s in self._staff.values() if s), reverse=True
        )

    def classes(self) -> Tuple[int, int, int]:
        """``(capitalists, workers, unemployed)`` -- derived, not assigned."""
        capitalists = sum(1 for s in self._staff.values() if s)
        workers = sum(1 for e in self.employer if e is not None)
        return capitalists, workers, self.actors - capitalists - workers

    def unemployment_rate(self) -> float:
        return self.classes()[2] / self.actors

    def check_staff_index(self) -> bool:
        """The maintained index agrees with a scan of ``employer``."""
        scanned: Dict[int, Set[int]] = {}
        for i, e in enumerate(self.employer):
            if e is not None:
                scanned.setdefault(e, set()).add(i)
        return {k: v for k, v in self._staff.items() if v} == scanned

    # ------------------------------------------------------------ rules

    def _select(self) -> int:
        """S1: "Randomly select an actor a from the set A according to a
        uniform distribution." """
        return self.rng.randrange(self.actors)

    def _hire(self, a: int) -> None:
        """H1(a).

        (a) ``H = {x : e_x = 0} = C u U`` -- the non-workers.  ``a``
            itself is excluded: the state constraint ``e_i != i`` forbids
            self-employment, and §2.4 says so in words.
        (b) ``P(c) = m_c / sum(m_x for x in H)`` -- weighted by wealth,
            "a stochastic bias that represents the tendency of firm growth
            to depend on accumulation of capital out of current profits".
        (c) **The threshold is tested after the draw, not before it.**
            If the actor drawn cannot cover the average wage, no hire
            happens this step -- the vacancy is not passed to someone who
            can. Filtering first instead is ``docs/100``'s error 1.
        """
        if not self.is_unemployed(a):
            return
        candidates = [
            x
            for x in range(self.actors)
            if x != a and self.employer[x] is None
        ]
        if not candidates:
            return
        weights = [self.money[x] for x in candidates]
        if sum(weights) <= 0.0:
            return
        c = self.rng.choices(candidates, weights=weights, k=1)[0]
        if self.money[c] > self.average_wage:
            self._attach(a, c)

    def _spend(self, a: int) -> None:
        """E1(a).

        (1) "Randomly select a consumer actor **b from the set A - {a}**"
            -- the spender is *not* the active actor.  Spending from ``a``
            instead is ``docs/100``'s error 2.
        (2) ``m ~ U[0, m_b]``.
        (3) ``m_b -= m; V += m``.
        """
        if self.actors < 2:
            return
        b = self.rng.randrange(self.actors - 1)
        if b >= a:
            b += 1
        if self.money[b] <= 0.0:
            return
        spend = self.rng.uniform(0.0, self.money[b])
        self.money[b] -= spend
        self.market += spend

    def _sample(self, a: int) -> None:
        """M1(a).  "If a is not unemployed": draw ``m ~ U[0, V]`` and
        transfer it to the firm's owner -- to ``e_a`` if ``a`` is an
        employee, to ``a`` itself if ``a`` is a capitalist.

        A firm therefore samples the market once per member per month on
        average, which is the model's "weak formulation of the law of
        value": revenue is statistically linear in labour expended.

        ``market_rule`` ablates that (docs/115).  Wright names M1's two
        ingredients himself -- sampling "once for every employee ... a
        bias justified by the law of value", and a random amount "to
        reflect contingency" -- so the variants remove one, the other or
        both.  ``"wright"`` is the paper's rule and the default, and it
        takes the same branch it always did so the model stays
        bit-identical.
        """
        if self.is_unemployed(a) or self.market <= 0.0:
            return
        owner = self.employer[a] if self.employer[a] is not None else a
        rule = self.market_rule
        if rule == "wright":
            drawn = self.rng.uniform(0.0, self.market)
        else:
            # The size a firm is neutralised against is its whole
            # membership -- the owner plus the staff -- because that is
            # how many times it samples per month under SR1.
            members = len(self._staff.get(owner, ())) + 1
            if rule == "neutral":
                drawn = self.rng.uniform(0.0, self.market) / members
            elif rule == "fixed":
                drawn = self.market / self.actors
            else:  # fixed_neutral
                drawn = self.market / (self.actors * members)
        if drawn > self.market:
            drawn = self.market
        self.market -= drawn
        self.money[owner] += drawn
        self.revenue[owner] += drawn
        self.year_gross[owner] += drawn

    def _fire(self, a: int) -> None:
        """F1(a), the one deterministic rule.

        ``u = max(|W_a| - floor(m_a / <w>), 0)``, then ``u`` employees
        chosen uniformly are released.

        **The test is against ``m_a``, the firm's money holdings** -- what
        it has, not what it earned this month. The paper's prose in §2.7
        says "if current revenues do not cover the expected wage bill",
        and that loose sentence is what every secondary source quotes; the
        formal rule is the floor above. Testing against trailing revenue
        instead is ``docs/100``'s error 3, and it was chosen in `docs/98`
        because it reproduced Wright's *results* -- from the wrong rule.

        Note also that the bill is reckoned at the **average** wage, not
        at what these particular employees will be paid: wages are redrawn
        at every payment, so there is no such thing as their wage.
        """
        staff = self._staff.get(a)
        if not staff or self.employer[a] is not None:
            return
        affordable = int(self.money[a] // self.average_wage)
        surplus = len(staff) - affordable
        if surplus <= 0:
            return
        doomed = self.rng.sample(sorted(staff), surplus)
        emptied = surplus == len(staff)
        for worker in doomed:
            self._detach(worker)
        if emptied:
            # Wright: "A firm demise occurs when a firm fires all its
            # employees" -- so a firm that loses its last employee to a
            # rival's H1 poach is not a demise (docs/111 section 2).
            self.month_demises += 1

    def _pay(self, a: int) -> None:
        """W1(a).  "For each actor c in a's employee set" -- so wages are
        paid when the **employer** is the active actor, and the whole
        payroll goes out at once. Paying each employee on its own
        activation instead is ``docs/100``'s error 4.

        Each wage is drawn afresh from the discrete interval
        ``[w_a, w_b]``; if the employer cannot cover it, the wage is drawn
        from ``[0, m_a]`` and partial payment is made rather than none.
        """
        staff = self._staff.get(a)
        if not staff:
            return
        for c in sorted(staff):
            due = float(self.rng.randint(self.wage_min, self.wage_max))
            if self.money[a] < due:
                cap = int(self.money[a])
                due = float(self.rng.randint(0, cap)) if cap >= 0 else 0.0
                if due > self.money[a]:
                    due = self.money[a]
            if due <= 0.0:
                continue
            self.money[a] -= due
            self.money[c] += due
            self.wages_paid[c] += due
            self.revenue[a] -= due
            self.year_wages_out[a] += due
            self.year_wages_in[c] += due

    def step(self) -> None:
        """SR1, in the paper's order: select, hire, spend, sample, fire,
        pay."""
        a = self._select()
        self._hire(a)
        self._spend(a)
        self._sample(a)
        self._fire(a)
        self._pay(a)
        self.steps += 1

    def month(self) -> None:
        """Rule 1M: N applications of SR1, "so that on average wages are
        paid once per month"."""
        self.wages_paid = [0.0] * self.actors
        self.revenue = [0.0] * self.actors
        self.month_demises = 0
        for _ in range(self.actors):
            self.step()
        self.months_elapsed += 1
        if self.history is not None:
            self._observe_month()

    def start_recording(self) -> None:
        """Begin a fresh history at a year boundary (docs/111).

        Wright pools firm sizes over "15 simulated years", which is a
        window on a model already in its stationary state -- so the
        harness runs a burn-in with recording off and calls this before
        the measured window.  The year accumulators are cleared so the
        first recorded year is a whole one.
        """
        self.record = True
        self.history = History()
        self.months_elapsed = 0
        self.month_demises = 0
        self._traded_this_year = set()
        self._previous_year_sizes = {}
        self.year_gross = [0.0] * self.actors
        self.year_wages_out = [0.0] * self.actors
        self.year_wages_in = [0.0] * self.actors

    def _observe_month(self) -> None:
        """Record the month, and close the year every twelfth (docs/111)."""
        history = self.history
        sizes = {owner: len(staff) for owner, staff in self._staff.items() if staff}
        history.firm_sizes.extend(sizes.values())
        history.demises_per_month.append(self.month_demises)
        self._traded_this_year.update(sizes)
        if self.months_elapsed % 12:
            return

        # Fact 3: GDP is the year's total M1 receipts, gross.
        gross = sum(self.year_gross)
        history.gdp.append(gross)

        # Fact 7: the profit rate of each firm trading at the close.
        for owner in sorted(sizes):
            wages = self.year_wages_out[owner]
            if wages > 0.0:
                history.profit_rates.append(
                    100.0 * (self.year_gross[owner] / wages - 1.0)
                )

        # Fact 2: growth for every firm that traded at some point, with
        # Wright's convention that a firm entering or leaving counts one.
        for owner in sorted(self._traded_this_year):
            now = sizes.get(owner, 1)
            before = self._previous_year_sizes.get(owner, 1)
            if before > 0 and now > 0:
                history.firm_growth.append(math.log(now / before))

        # Fact 6: each actor's income for the year, wages plus profit.
        for actor in range(self.actors):
            income = self.year_wages_in[actor] + (
                self.year_gross[actor] - self.year_wages_out[actor]
            )
            history.incomes.append(income)

        # The shares, on the same yearly basis as Wright's figure 7.
        wage_total = sum(self.year_wages_in)
        if gross > 0.0:
            history.wage_shares.append(wage_total / gross)

        self._previous_year_sizes = dict(sizes)
        self._traded_this_year = set()
        self.year_gross = [0.0] * self.actors
        self.year_wages_out = [0.0] * self.actors
        self.year_wages_in = [0.0] * self.actors

    def year(self) -> None:
        """Rule 1Y: twelve months, the accounting period."""
        for _ in range(12):
            self.month()

    def run(self, months: int) -> None:
        for _ in range(months):
            self.month()

    # -------------------------------------------------------- readings

    def incomes(self) -> List[float]:
        """The month's income per actor: wages for workers, revenue net of
        the wage bill for capitalists.  §3: "wage income (from rule W1)
        and capitalist income (from rule M1) are counted as income"."""
        return [
            self.wages_paid[i] + self.revenue[i] for i in range(self.actors)
        ]

    def wage_share(self) -> Optional[float]:
        """Wages over national income for the month -- the reading
        ``docs/99`` shows our own model cannot move for quantity
        reasons."""
        total = sum(self.incomes())
        if total <= 0.0:
            return None
        return sum(self.wages_paid) / total


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
    """Hill estimator of the Pareto tail index over the top ``tail``."""
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
