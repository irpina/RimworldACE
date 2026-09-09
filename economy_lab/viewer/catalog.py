"""The scenario registry the viewer serves (docs/48 section 2).

Everything the page needs to offer a scenario before running it: what it
is, which options its function exposes, which day its shock lands on, how
long it takes, and which documents introduced it.  Options are read off
each function's own signature so the catalog cannot drift from the
scenarios; only the prose and the document numbers are written here.
"""

from __future__ import annotations

import inspect
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .. import scenarios


DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"

#: Runs longer than this many seconds are marked slow, and the page says
#: so on the button before it is pressed.
SLOW_SECONDS = 2.0


@dataclass(frozen=True)
class Option:
    name: str
    type: str  # "float", "int", "bool", "str"; "?" suffix when None is allowed
    default: object
    doc: str = ""


@dataclass(frozen=True)
class Scenario:
    name: str
    function: Callable
    kind: str  # "run" returns an Economy; "sweep" returns rows
    description: str
    options: Tuple[Option, ...]
    #: An int, the name of a ``ScenarioParameters`` field holding the day,
    #: a callable reading the day off the finished economy, or None.
    shock: object
    docs: Tuple[int, ...]
    seconds: float

    @property
    def cost(self) -> str:
        return "slow" if self.seconds >= SLOW_SECONDS else "fast"


def _first_paragraph(text: Optional[str]) -> str:
    if not text:
        return ""
    paragraphs = re.split(r"\n\s*\n", inspect.cleandoc(text))
    return " ".join(paragraphs[0].split())


def _option_type(parameter: inspect.Parameter) -> Optional[str]:
    """The option's type from its annotation, or None to leave it out."""
    annotation = str(parameter.annotation)
    if "List" in annotation or "Tuple" in annotation:
        return None
    default = parameter.default
    optional = "None" in annotation or default is None
    if isinstance(default, bool) or annotation.startswith("bool"):
        base = "bool"
    elif isinstance(default, int) and not isinstance(default, bool):
        base = "int"
    elif isinstance(default, str) or annotation.startswith("str"):
        base = "str"
    else:
        base = "float"
    return base + ("?" if optional else "")


def _options(function: Callable) -> Tuple[Option, ...]:
    options: List[Option] = []
    for name, parameter in inspect.signature(function).parameters.items():
        if name == "parameters":
            continue
        kind = _option_type(parameter)
        if kind is None:
            continue
        options.append(Option(name, kind, parameter.default))
    return tuple(options)


def _reserve_exhaustion_day(economy) -> Optional[int]:
    """The first day Dust Basin's chemfuel marginal cost leaves its start."""
    snapshots = [h for h in economy.history if "regions" in h]
    if not snapshots:
        return None
    first = snapshots[0]["regions"]["Dust Basin"]["reserves"]
    if scenarios.CHEMFUEL not in first:
        return None
    start = first[scenarios.CHEMFUEL]["marginal_cost"]
    for snapshot in snapshots:
        reserve = snapshot["regions"]["Dust Basin"]["reserves"][scenarios.CHEMFUEL]
        if reserve["marginal_cost"] != start:
            return int(snapshot["day"])
    return None


_PROSE = {
    "equilibrium": (
        "The seeded two-region circuit left alone. Nothing is shocked; the "
        "price range should be exactly zero and every ledger should close. "
        "The reference every other scenario is a departure from."
    ),
    "regional_glut": (
        "A shipment equal to a quarter of Dust Basin's annual yayo demand "
        "arrives on day 60. The local price falls, the distant one barely "
        "moves, and the glut travels upstream as a layoff (docs/10, docs/18)."
    ),
    "producer_loss": (
        "Sixty percent of Dust Basin's yayo capacity is destroyed on day 60, "
        "with the expensive route. Price rises once stocks fall below ten "
        "days and delayed entry restores supply."
    ),
    "arbitrage": (
        "The glut, injected on day 30 with the cheap route: the spread "
        "covers freight, exports leave, and the two regional prices "
        "converge on the route's capacity."
    ),
}

_DOCS: Dict[str, Tuple[int, ...]] = {
    "equilibrium": (6, 17, 25),
    "regional_glut": (6, 10, 12),
    "producer_loss": (6, 9, 14),
    "arbitrage": (6, 9),
    "input_shortage": (8, 9),
    "reserve_depletion": (15, 16),
    "subsistence_shock": (17, 18),
    "technique_change": (19, 20),
    "cost_competition": (21, 22),
    "generous_basket": (28, 29),
    "perishable_meals": (30, 31),
    "capital_goods": (36, 37),
    "capacity_exit": (38, 39),
    "recreation_basket": (40, 41),
    "recreation_sweep": (40, 41),
    "demand_boom": (46, 47),
    "wage_slump": (46, 47),
    "reserve_army_sweep": (46, 47),
    "boom_reversal": (51, 52),
    "cash_circuit": (55, 56),
    "gravitation": (61, 62, 63),
    "overshoot": (64, 65, 66, 67),
}

#: Shock days: an int, a parameter name, a callable, or None.
_SHOCKS: Dict[str, object] = {
    "regional_glut": 60,
    "producer_loss": 60,
    "arbitrage": 30,
    "input_shortage": 60,
    "reserve_depletion": _reserve_exhaustion_day,
    "subsistence_shock": 60,
    "technique_change": "technique_change_day",
    "cost_competition": "cost_competition_day",
    "demand_boom": 60,
    "wage_slump": 60,
    "boom_reversal": 60,
    "overshoot": 60,
}

#: Measured once on the development machine; the page shows the tier, not
#: the number, so a slower machine changes nothing but the wait.
_SECONDS: Dict[str, float] = {
    "capacity_exit": 3.2,
    "recreation_sweep": 0.5,
    "reserve_army_sweep": 0.6,
    "gravitation": 2.0,
    "overshoot": 2.0,
}

_SWEEPS = ("recreation_sweep", "reserve_army_sweep")

_ORDER = (
    "equilibrium",
    "regional_glut",
    "producer_loss",
    "arbitrage",
    "input_shortage",
    "reserve_depletion",
    "subsistence_shock",
    "technique_change",
    "cost_competition",
    "generous_basket",
    "perishable_meals",
    "capital_goods",
    "capacity_exit",
    "recreation_basket",
    "recreation_sweep",
    "demand_boom",
    "wage_slump",
    "reserve_army_sweep",
    "boom_reversal",
    "cash_circuit",
    "gravitation",
    "overshoot",
)


def _build() -> Dict[str, Scenario]:
    catalog: Dict[str, Scenario] = {}
    for name in _ORDER:
        function = getattr(scenarios, name)
        catalog[name] = Scenario(
            name=name,
            function=function,
            kind="sweep" if name in _SWEEPS else "run",
            description=_PROSE.get(name) or _first_paragraph(function.__doc__),
            options=_options(function),
            shock=_SHOCKS.get(name),
            docs=_DOCS[name],
            seconds=_SECONDS.get(name, 0.2),
        )
    return catalog


CATALOG: Dict[str, Scenario] = _build()


def shock_day(scenario: Scenario, parameters, economy) -> Optional[int]:
    """Resolve the scenario's shock day for one finished run."""
    shock = scenario.shock
    if shock is None:
        return None
    if isinstance(shock, int):
        return shock
    if isinstance(shock, str):
        return int(getattr(parameters, shock))
    return shock(economy)


def _json_default(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def document_mentions() -> Dict[str, List[int]]:
    """Which documents mention each scenario by name, beyond its own pair."""
    texts: Dict[int, str] = {}
    for path in sorted(DOCS_DIR.glob("*.md")):
        match = re.match(r"(\d+)-", path.name)
        if match:
            texts[int(match.group(1))] = path.read_text(encoding="utf-8")
    mentions: Dict[str, List[int]] = {}
    for name in CATALOG:
        pattern = re.compile(r"\b" + re.escape(name) + r"\b")
        mentions[name] = [
            number for number, text in sorted(texts.items()) if pattern.search(text)
        ]
    return mentions


def describe(mentions: Optional[Dict[str, List[int]]] = None) -> List[Dict[str, object]]:
    """The catalog as the JSON the page reads."""
    mentions = mentions or {}
    rows: List[Dict[str, object]] = []
    for scenario in CATALOG.values():
        rows.append(
            {
                "name": scenario.name,
                "kind": scenario.kind,
                "description": scenario.description,
                "options": [
                    {
                        "name": option.name,
                        "type": option.type,
                        "default": _json_default(option.default),
                    }
                    for option in scenario.options
                ],
                "shock": (
                    scenario.shock
                    if isinstance(scenario.shock, (int, str))
                    else ("derived" if scenario.shock else None)
                ),
                "docs": list(scenario.docs),
                "mentioned_in": [
                    number
                    for number in mentions.get(scenario.name, [])
                    if number not in scenario.docs
                ],
                "cost": scenario.cost,
                "seconds": scenario.seconds,
            }
        )
    return rows
