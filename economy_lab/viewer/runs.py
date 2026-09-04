"""Run a scenario and serialize it to one JSON document (docs/48 section 2.2).

The document is built by walking sorted dictionaries, so the same key
produces the same bytes every time.  Nothing here calls into the model
except through the public readings the terminal runner already uses.
"""

from __future__ import annotations

import hashlib
import json
import math
import threading
import time
from dataclasses import fields
from typing import Dict, List, Optional

from ..model import Economy
from ..scenarios import MEALS, ScenarioParameters, summary
from .catalog import CATALOG, Scenario, shock_day


FIELD_TYPES: Dict[str, str] = {
    field.name: str(field.type) for field in fields(ScenarioParameters)
}


class OverrideError(ValueError):
    """An override names a field that does not exist or cannot be coerced."""


def coerce_overrides(overrides: Optional[Dict[str, object]]) -> Dict[str, object]:
    """Validate override names and coerce values to the field's type.

    The rule docs/45 section 1 learned: an ``int`` field perturbed to a
    float is a refusal dressed as a finding.  Here it is a 400 instead.
    """
    clean: Dict[str, object] = {}
    for name, raw in sorted((overrides or {}).items()):
        if name not in FIELD_TYPES:
            raise OverrideError(f"unknown parameter: {name}")
        kind = FIELD_TYPES[name]
        try:
            if kind == "bool":
                if isinstance(raw, str):
                    lowered = raw.strip().lower()
                    if lowered not in ("true", "false"):
                        raise ValueError(raw)
                    value: object = lowered == "true"
                else:
                    value = bool(raw)
            elif kind == "int":
                number = float(raw)
                if not number.is_integer():
                    raise ValueError(raw)
                value = int(number)
            else:
                value = float(raw)
                if not math.isfinite(value) and name != "labor_pool_worker_days":
                    raise ValueError(raw)
        except (TypeError, ValueError):
            raise OverrideError(f"{name}: cannot read {raw!r} as {kind}") from None
        clean[name] = value
    return clean


def coerce_options(scenario: Scenario, options: Optional[Dict[str, object]]) -> Dict[str, object]:
    known = {option.name: option for option in scenario.options}
    clean: Dict[str, object] = {}
    for name, raw in sorted((options or {}).items()):
        if name not in known:
            raise OverrideError(f"{scenario.name} has no option {name}")
        kind = known[name].type
        optional = kind.endswith("?")
        base = kind.rstrip("?")
        if raw is None or (isinstance(raw, str) and raw.strip() == ""):
            if optional:
                continue
            raise OverrideError(f"{name} needs a value")
        try:
            if base == "bool":
                value: object = (
                    raw.strip().lower() == "true" if isinstance(raw, str) else bool(raw)
                )
            elif base == "int":
                number = float(raw)
                if not number.is_integer():
                    raise ValueError(raw)
                value = int(number)
            elif base == "str":
                value = str(raw)
            else:
                value = float("inf") if raw in ("inf", "Infinity") else float(raw)
        except (TypeError, ValueError):
            raise OverrideError(f"{name}: cannot read {raw!r} as {base}") from None
        clean[name] = value
    return clean


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=True)


def run_key(scenario: str, options: Dict[str, object], overrides: Dict[str, object]) -> str:
    payload = _canonical({"scenario": scenario, "options": options, "overrides": overrides})
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _finite(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _series_document(economy: Economy) -> Dict[str, object]:
    """Every recorded snapshot as arrays, one entry per recorded day."""
    snapshots = [h for h in economy.history if "regions" in h]
    days = [int(h["day"]) for h in snapshots]
    commodities = sorted(economy.commodities)
    region_names = sorted(economy.regions)
    per_commodity = ("price", "inventory", "unmet", "capacity", "cost_ratio")
    scalars = (
        "cash", "worker_cash", "employment", "wage_rate", "wage_premium",
        "habitual_scale", "premium_over_value",
    )
    regions: Dict[str, object] = {}
    for name in region_names:
        states = [h["regions"][name] for h in snapshots]
        entry: Dict[str, object] = {}
        for field in per_commodity:
            entry[field] = {
                commodity: [_finite(state[field].get(commodity)) for state in states]
                for commodity in commodities
            }
        for field in scalars:
            entry[field] = [_finite(state[field]) for state in states]
        reserved = sorted({c for state in states for c in state["reserves"]})
        entry["reserves"] = {
            commodity: {
                "remaining": [
                    _finite(state["reserves"].get(commodity, {}).get("remaining"))
                    for state in states
                ],
                "marginal_cost": [
                    _finite(state["reserves"].get(commodity, {}).get("marginal_cost"))
                    for state in states
                ],
            }
            for commodity in reserved
        }
        regions[name] = entry
    return {
        "days": days,
        "commodities": commodities,
        "region_names": region_names,
        "regions": regions,
        "labor_values": {
            commodity: [_finite(h["labor_values"].get(commodity)) for h in snapshots]
            for commodity in commodities
        },
    }


def _value_ledger(economy: Economy) -> Dict[str, object]:
    """The summary's value ledger, for a run whose summary refused."""
    ledger = economy.ledger
    names = list(economy.regions)
    return {
        "constant_capital": sum(ledger.constant_capital(r) for r in names),
        "circulating_capital": sum(ledger.circulating_capital.get(r, 0.0) for r in names),
        "fixed_capital_consumed": sum(ledger.fixed_capital_consumed.get(r, 0.0) for r in names),
        "variable_capital": sum(ledger.necessary_labor.get(r, 0.0) for r in names),
        "surplus_labor": sum(ledger.surplus_labor(r) for r in names),
        "organic_composition": economy.organic_composition(),
        "value_rate_of_profit": economy.value_rate_of_profit(),
    }


def _production_prices(economy: Economy) -> Optional[Dict[str, object]]:
    from ..scenarios import _production_price_report

    return _production_price_report(economy)


def _ledgers(economy: Economy, report: Dict[str, object]) -> Dict[str, object]:
    """The five panels of docs/48 section 1, each under its own unit."""
    ledger = economy.ledger
    region_names = sorted(economy.regions)
    commodities = sorted(economy.commodities)

    labor_value = {
        "unit": "work-ticks",
        "silver_per_tick": economy.labor_value_per_tick,
        "social": {c: economy.labor_values.get(c) for c in commodities},
        "individual": {
            r: {c: v for c, v in sorted(economy.regional_labor_values.get(r, {}).items())}
            for r in region_names
        },
        "authored_silver": {c: economy.commodities[c].labor_value for c in commodities},
        "stale": sorted(economy.stale_labor_values),
    }

    market_price = {
        "unit": "silver",
        "regions": {
            r: {
                "prices": {c: economy.regions[r].prices[c] for c in commodities},
                "decomposition": {
                    c: {
                        k: _finite(v)
                        for k, v in sorted(economy.price_decomposition(r, c).items())
                    }
                    for c in commodities
                },
                "wages_paid": ledger.wages_paid.get(r, 0.0),
                "wage_premium_paid": ledger.wage_premium_paid.get(r, 0.0),
                "worker_spending": ledger.worker_spending.get(r, 0.0),
                "unattributed_margin": ledger.unattributed_margin.get(r, 0.0),
                "fixed_capital_money": ledger.fixed_capital_money.get(r, 0.0),
            }
            for r in region_names
        },
        "investment_spending": ledger.investment_spending,
        "transport_cash": ledger.transport_cash,
    }

    production = report.get("prices_of_production")
    system = economy.prices_of_production()
    price_of_production = {
        "unit": "ratio to meals",
        "report": production,
        "labor_value_numeraire": (
            None
            if system is None
            else {
                "unit": "work-ticks",
                "prices": {c: v for c, v in sorted(system["prices"].items())},
                "gross_markup": system["gross_markup"],
                "fixed_capital_share": system["fixed_capital_share"],
                "turnover_days": {
                    c: v for c, v in sorted(system["turnover_days"].items())
                },
            }
        ),
    }

    def rate(reading):
        return None if reading is None else reading

    surplus_value = {
        "unit": "work-ticks",
        "total": report["value_ledger"],
        "regions": {
            r: {
                "living_labor": ledger.living_labor.get(r, 0.0),
                "necessary_labor": ledger.necessary_labor.get(r, 0.0),
                "surplus_labor": ledger.surplus_labor(r),
                "wage_deviation_labor": ledger.wage_deviation_labor.get(r, 0.0),
                "constant_capital": ledger.constant_capital(r),
                "circulating_capital": ledger.circulating_capital.get(r, 0.0),
                "fixed_capital_consumed": ledger.fixed_capital_consumed.get(r, 0.0),
                "value_of_labor_power": economy.value_of_labor_power(economy.regions[r]),
                "habitual_scale": economy.regions[r].habitual_scale,
                "premium_over_value": economy.regions[r].premium_over_value(),
                "rate_of_surplus_value": rate(economy.rate_of_surplus_value(r)),
                "realized_rate_of_surplus_value": rate(
                    economy.realized_rate_of_surplus_value(r)
                ),
                "organic_composition": rate(economy.organic_composition(r)),
                "value_rate_of_profit": rate(economy.value_rate_of_profit(r)),
            }
            for r in region_names
        },
        "sector_organic_composition": {
            c: v for c, v in sorted(economy.sector_organic_composition().items())
        },
        "price_value_deviation": (
            None
            if economy.price_value_deviation() is None
            else {c: v for c, v in sorted(economy.price_value_deviation().items())}
        ),
        "capital_advanced": {
            k: v for k, v in sorted(economy.capital_advanced().items())
        },
        "rate_of_profit_on_advances": rate(economy.value_rate_of_profit_on_advances()),
        "realized_turnover_days": rate(economy.realized_turnover_days()),
    }

    bound = economy.absolute_rent_bound()
    rent = {
        "differential_rent": {
            "unit": "silver",
            "by_commodity": {
                c: v for c, v in sorted(ledger.differential_rent.items())
            },
        },
        "absolute_rent_bound": {
            "unit": "work-ticks per day",
            "by_commodity": None if bound is None else {c: v for c, v in sorted(bound.items())},
        },
        "reserves": {
            r: {
                c: {
                    "remaining": _finite(reserve.remaining),
                    "marginal_cost": _finite(reserve.marginal_cost()),
                    "grades": [
                        {
                            "quantity": _finite(g.quantity),
                            "extraction_cost": _finite(g.extraction_cost),
                        }
                        for g in reserve.grades
                    ],
                }
                for c, reserve in sorted(economy.regions[r].reserves.items())
            }
            for r in region_names
        },
    }

    return {
        "labor_value": labor_value,
        "market_price": market_price,
        "price_of_production": price_of_production,
        "surplus_value": surplus_value,
        "rent": rent,
    }


def _sweep_document(scenario: Scenario, options, parameters) -> Dict[str, object]:
    result = scenario.function(**options, parameters=parameters)
    if scenario.name == "recreation_sweep":
        rows = [{k: _finite(v) for k, v in row.items()} for row in result]
        return {"columns": list(rows[0]) if rows else [], "rows": rows}
    rows = []
    for pool, economy in result.items():
        region = economy.regions["Dust Basin"]
        premiums = [
            h["regions"]["Dust Basin"]["wage_premium"]
            for h in economy.history
            if "regions" in h
        ]
        peak = max(premiums)
        rows.append(
            {
                "labor_pool": "inf" if math.isinf(pool) else pool,
                "premium_peak": peak,
                "premium_peak_day": premiums.index(peak),
                "premium_end": region.wage_premium,
                "employment_end": region.worker_days_earned,
                "meal_price_end": region.prices[MEALS],
                "rate_of_surplus_value": economy.rate_of_surplus_value(),
                "realized_rate_of_surplus_value": economy.realized_rate_of_surplus_value(),
            }
        )
    return {"columns": list(rows[0]) if rows else [], "rows": rows}


def run_document(
    scenario_name: str,
    options: Optional[Dict[str, object]] = None,
    overrides: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    if scenario_name not in CATALOG:
        raise OverrideError(f"unknown scenario: {scenario_name}")
    scenario = CATALOG[scenario_name]
    options = coerce_options(scenario, options)
    overrides = coerce_overrides(overrides)
    parameters = ScenarioParameters(**overrides)
    key = run_key(scenario_name, options, overrides)
    started = time.perf_counter()
    document: Dict[str, object] = {
        "key": key,
        "scenario": scenario_name,
        "kind": scenario.kind,
        # An infinite option (the unbounded reserve army) is shown as the
        # word, since JSON has no infinity.
        "options": {
            k: ("inf" if isinstance(v, float) and math.isinf(v) else v)
            for k, v in options.items()
        },
        "overrides": overrides,
    }
    if scenario.kind == "sweep":
        document["sweep"] = _sweep_document(scenario, options, parameters)
    else:
        economy = scenario.function(**options, parameters=parameters)
        document.update(_series_document(economy))
        document["shock_day"] = shock_day(scenario, parameters, economy)
        try:
            report = summary(economy)
        except RuntimeError as refusal:
            # A sampled history has no positional series, so the terminal
            # runner's summary refuses (docs/34 section 3.2).  The series
            # above carry their own days; the summary is simply absent.
            document["summary"] = None
            document["summary_unavailable"] = str(refusal)
            report = {
                "value_ledger": _value_ledger(economy),
                "prices_of_production": _production_prices(economy),
            }
        else:
            document["summary"] = report
        document["ledgers"] = _ledgers(economy, report)
    document["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    return document


def document_bytes(document: Dict[str, object]) -> bytes:
    """The document as JSON, with timing left out so the bytes are stable."""
    body = {k: v for k, v in document.items() if k != "elapsed_seconds"}
    return _canonical(body).encode("utf-8")


class RunCache:
    """Runs made this session, by key; one run at a time."""

    def __init__(self) -> None:
        self._documents: Dict[str, Dict[str, object]] = {}
        self._order: List[str] = []
        self._lock = threading.Lock()

    def get(self, scenario: str, options, overrides) -> Dict[str, object]:
        scenario_entry = CATALOG.get(scenario)
        if scenario_entry is None:
            raise OverrideError(f"unknown scenario: {scenario}")
        key = run_key(
            scenario,
            coerce_options(scenario_entry, options),
            coerce_overrides(overrides),
        )
        with self._lock:
            if key not in self._documents:
                document = run_document(scenario, options, overrides)
                self._documents[key] = document
                self._order.append(key)
            return self._documents[key]

    def lookup(self, key: str) -> Optional[Dict[str, object]]:
        with self._lock:
            return self._documents.get(key)

    def listing(self) -> List[Dict[str, object]]:
        with self._lock:
            return [
                {
                    "key": key,
                    "scenario": self._documents[key]["scenario"],
                    "kind": self._documents[key]["kind"],
                    "options": self._documents[key]["options"],
                    "overrides": self._documents[key]["overrides"],
                    "days": (
                        self._documents[key]["days"][-1]
                        if "days" in self._documents[key]
                        else None
                    ),
                }
                for key in self._order
            ]
