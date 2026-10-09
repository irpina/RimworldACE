"""The whole state of an economy, as data the C# port can read (docs/141 §4).

``encode(economy)`` returns every field of every object the step reads or
writes, in the order the model holds it, as plain JSON types.  Floats are
written by ``json`` with ``repr``, which round-trips exactly; a reader that
parses them with a correctly rounded parser (``System.Text.Json`` is one)
recovers the same bits.

It is exhaustive on purpose: an attribute the codec does not know raises,
so a field added to the model cannot be silently missing from the port's
fixtures.  Two things are left out, each because nothing in the step reads
it: ``history`` (read only by ``Economy.series``) and the frozen
``scale_record`` a generator may attach.

Layout::

    {"schema": 1,
     "economy":      {scalar settings and counters, in attribute order},
     "commodities":  [Commodity, ...],
     "processes":    [Process, ...]        one per name, first-seen order,
     "known_processes": {commodity: process name},
     "regions":      [Region, ...]         producers inside, process by name,
     "routes":       [Route, ...],
     "shipments":    [Shipment, ...],
     "ledger":       Ledger,
     "labor_values": {...}, "regional_labor_values": {...},
     "stale_labor_values": [sorted names],
     "throughput":   {region: {commodity: float}},
     "daily_extraction": [[region, reserve, float], ...],
     "opening_inventory": {...}}
"""
from __future__ import annotations

import dataclasses
import json
from typing import Any, Dict, List

from .model import Economy, Process

SCHEMA = 1

#: Attributes of ``Economy`` that are containers with their own section.
_SECTIONS = {
    "commodities", "regions", "routes", "shipments", "ledger", "labor_values",
    "regional_labor_values", "stale_labor_values", "_throughput",
    "known_processes", "opening_inventory", "_daily_extraction",
}
#: Attributes deliberately not carried; see the module docstring.
_OMITTED = {"history", "scale_record"}


def _plain(value: Any, path: str) -> Any:
    """A value as JSON types, refusing anything not anticipated."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path}: non-string key {key!r}")
            out[key] = _plain(item, f"{path}.{key}")
        return out
    if isinstance(value, (list, tuple)):
        return [_plain(item, f"{path}[{index}]") for index, item in enumerate(value)]
    raise TypeError(f"{path}: cannot encode {type(value).__name__}")


def _record(obj: Any, path: str, processes: Dict[str, Process]) -> Dict[str, Any]:
    """A dataclass's fields in declaration order; a Process becomes its name."""
    extra = set(vars(obj)) - {field.name for field in dataclasses.fields(obj)}
    if extra:
        raise TypeError(f"{path}: attributes outside the dataclass: {sorted(extra)}")
    out: Dict[str, Any] = {}
    for field in dataclasses.fields(obj):
        value = getattr(obj, field.name)
        where = f"{path}.{field.name}"
        if isinstance(value, Process):
            _register(value, processes, where)
            out[field.name] = value.name
        elif dataclasses.is_dataclass(value):
            out[field.name] = _record(value, where, processes)
        elif isinstance(value, list) and value and dataclasses.is_dataclass(value[0]):
            out[field.name] = [
                _record(item, f"{where}[{index}]", processes)
                for index, item in enumerate(value)
            ]
        elif isinstance(value, dict) and value and dataclasses.is_dataclass(next(iter(value.values()))):
            out[field.name] = {
                key: _record(item, f"{where}.{key}", processes)
                for key, item in value.items()
            }
        else:
            out[field.name] = _plain(value, where)
    return out


def _register(process: Process, processes: Dict[str, Process], path: str) -> None:
    known = processes.get(process.name)
    if known is None:
        processes[process.name] = process
    elif known != process:
        raise ValueError(f"{path}: two different processes named {process.name!r}")


def encode(economy: Economy) -> Dict[str, Any]:
    attributes = vars(economy)
    unknown = set(attributes) - _SECTIONS - _OMITTED
    scalars = {}
    for name, value in attributes.items():
        if name in _SECTIONS or name in _OMITTED:
            continue
        if not (value is None or isinstance(value, (bool, int, float, str))):
            raise TypeError(f"economy.{name}: an unanticipated {type(value).__name__}")
        scalars[name] = value
        unknown.discard(name)

    processes: Dict[str, Process] = {}
    regions = [
        _record(region, f"regions.{region.name}", processes)
        for region in economy.regions.values()
    ]
    for name, process in economy.known_processes.items():
        _register(process, processes, f"known_processes.{name}")
    process_records = [_record(process, f"processes.{name}", {})
                       for name, process in processes.items()]

    extraction = [
        [region, reserve, value]
        for (region, reserve), value in getattr(economy, "_daily_extraction", {}).items()
    ]
    return {
        "schema": SCHEMA,
        "economy": scalars,
        "commodities": [_record(good, f"commodities.{good.name}", {})
                        for good in economy.commodities.values()],
        "processes": process_records,
        "known_processes": {name: process.name
                            for name, process in economy.known_processes.items()},
        "regions": regions,
        "routes": [_record(route, "routes", {}) for route in economy.routes],
        "shipments": [_record(item, "shipments", {}) for item in economy.shipments],
        "ledger": _record(economy.ledger, "ledger", {}),
        "labor_values": _plain(economy.labor_values, "labor_values"),
        "regional_labor_values": _plain(economy.regional_labor_values,
                                        "regional_labor_values"),
        "stale_labor_values": sorted(economy.stale_labor_values),
        "throughput": _plain(economy._throughput, "throughput"),
        "has_daily_extraction": hasattr(economy, "_daily_extraction"),
        "daily_extraction": extraction,
        "opening_inventory": _plain(economy.opening_inventory, "opening_inventory"),
    }


def dumps(economy: Economy) -> str:
    """Compact, deterministic text: the fixture format."""
    return json.dumps(encode(economy), indent=None, separators=(",", ":"),
                      allow_nan=False)


def decode(data: Dict[str, Any]) -> Economy:
    """An economy rebuilt from :func:`encode`'s output, without running
    ``Economy.__init__`` (which seeds).  Its only use is the completeness
    test: a decoded economy must step identically to the original, which
    shows the encoding carries every piece of state the step depends on."""
    from .model import (CapacityProject, Commodity, Ledger, Producer,
                        Region, ResourceGrade, ResourceReserve, Route, Shipment)

    if data["schema"] != SCHEMA:
        raise ValueError(f"schema {data['schema']}, expected {SCHEMA}")

    def build(cls, record, **override):
        values = dict(record)
        values.update(override)
        return cls(**values)

    processes = {record["name"]: build(Process, record) for record in data["processes"]}

    def producer(record):
        process = record["process"]
        return build(Producer, record,
                     process=None if process is None else processes[process])

    def project(record):
        process = record["process"]
        return build(CapacityProject, record,
                     process=None if process is None else processes[process])

    def reserve(record):
        return build(ResourceReserve, record,
                     grades=[build(ResourceGrade, grade) for grade in record["grades"]])

    economy = object.__new__(Economy)
    for name, value in data["economy"].items():
        setattr(economy, name, value)
    economy.commodities = {record["name"]: build(Commodity, record)
                           for record in data["commodities"]}
    economy.regions = {}
    for record in data["regions"]:
        region = build(
            Region, record,
            producers=[producer(item) for item in record["producers"]],
            projects=[project(item) for item in record["projects"]],
            reserves={key: reserve(item) for key, item in record["reserves"].items()},
        )
        economy.regions[region.name] = region
    economy.routes = [build(Route, record) for record in data["routes"]]
    economy.shipments = [build(Shipment, record) for record in data["shipments"]]
    ledger = data["ledger"]
    economy.ledger = build(
        Ledger, ledger,
        bankruptcies=[tuple(item) for item in ledger["bankruptcies"]],
        exits=[tuple(item) for item in ledger["exits"]],
    )
    economy.labor_values = dict(data["labor_values"])
    economy.regional_labor_values = {
        name: dict(values) for name, values in data["regional_labor_values"].items()
    }
    economy.stale_labor_values = set(data["stale_labor_values"])
    economy._throughput = {
        name: dict(values) for name, values in data["throughput"].items()
    }
    economy.known_processes = {
        name: processes[process] for name, process in data["known_processes"].items()
    }
    economy.opening_inventory = dict(data["opening_inventory"])
    if data["has_daily_extraction"]:
        economy._daily_extraction = {
            (region, reserve_name): value
            for region, reserve_name, value in data["daily_extraction"]
        }
    economy.history = []
    return economy


def loads(text: str) -> Economy:
    return decode(json.loads(text))
