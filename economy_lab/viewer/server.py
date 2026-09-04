"""The HTTP server: JSON endpoints and the static page (docs/48 section 2.1).

`http.server` from the standard library, bound to the loopback interface.
Every endpoint reads; the only work it does on request is running a
scenario the page asked for, and that run is cached under its key.
"""

from __future__ import annotations

import csv
import json
import mimetypes
import re
import threading
from dataclasses import fields
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import parse_qs, unquote, urlparse

from .. import sensitivity
from ..baseline import DEFAULT_REFERENCE
from ..scenarios import ScenarioParameters
from . import catalog, markdown
from .runs import OverrideError, RunCache


STATIC_DIR = Path(__file__).resolve().parent / "static"
DOCS_DIR = catalog.DOCS_DIR


def _number(text: object) -> Optional[float]:
    """A CSV cell as a float, or None where the sweep left it blank or non-finite."""
    try:
        value = float(str(text))
    except (TypeError, ValueError):
        return None
    return value if value == value and abs(value) != float("inf") else None


def _parameter_groups() -> Dict[str, str]:
    """Each field's group, read from the ``# --- name ---`` comments in the source."""
    import inspect

    source = inspect.getsource(ScenarioParameters)
    groups: Dict[str, str] = {}
    current = "market and calibration"
    for line in source.splitlines():
        header = re.match(r"\s*# --- (.*?) -+\s*$", line)
        if header:
            current = header.group(1)
            continue
        field = re.match(r"\s*([a-z_][a-z0-9_]*)\s*:\s*(?:float|int|bool)\b", line)
        if field:
            groups[field.group(1)] = current
    return groups


def parameter_listing() -> List[Dict[str, object]]:
    groups = _parameter_groups()
    defaults = ScenarioParameters()
    rows = []
    for field in fields(ScenarioParameters):
        value = getattr(defaults, field.name)
        rows.append(
            {
                "name": field.name,
                "type": str(field.type),
                "default": None if isinstance(value, float) and value != value else value,
                "group": groups.get(field.name, "market and calibration"),
            }
        )
    return rows


class Library:
    """Everything the server reads once and then serves: the sweep's files,
    the frozen reference, the document list.  Metrics collection is the one
    slow thing, and it happens only on an explicit request."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sensitivity_rows: Optional[List[Dict[str, object]]] = None
        self._current_metrics: Optional[Dict[str, object]] = None
        self._mentions: Optional[Dict[str, List[int]]] = None

    def scenarios(self) -> List[Dict[str, object]]:
        with self._lock:
            if self._mentions is None:
                self._mentions = catalog.document_mentions()
            return catalog.describe(self._mentions)

    def reference_metrics(self) -> Dict[str, object]:
        document = json.loads(DEFAULT_REFERENCE.read_text(encoding="utf-8"))
        return {"description": document.get("description"), "metrics": document["metrics"]}

    def current_metrics(self) -> Dict[str, object]:
        with self._lock:
            if self._current_metrics is None:
                from ..behavior import collect_behavioral_metrics

                self._current_metrics = collect_behavioral_metrics()
            return self._current_metrics

    def _rows(self) -> List[Dict[str, object]]:
        with self._lock:
            if self._sensitivity_rows is None:
                path = sensitivity.DEFAULT_CSV
                if not path.exists():
                    self._sensitivity_rows = []
                else:
                    with path.open(encoding="utf-8", newline="") as handle:
                        self._sensitivity_rows = list(csv.DictReader(handle))
            return self._sensitivity_rows

    def sensitivity_ranking(self) -> Dict[str, object]:
        rows = self._rows()
        if not rows:
            return {"available": False, "ranking": [], "inert": [], "readings": 0}
        ranking = sensitivity.parameter_ranking(rows)
        reach = sensitivity.parameter_reach(rows)
        readings = len({str(r["metric"]) for r in rows if r["metric"] != "REFUSED"}) * 2
        ordered = sorted(
            ranking,
            key=lambda row: (
                -reach.get(str(row["parameter"]), 0),
                -float(row["elasticity"]),
                str(row["parameter"]),
            ),
        )
        return {
            "available": True,
            "readings": readings,
            "ranking": [
                {
                    "rank": index,
                    "parameter": str(row["parameter"]),
                    "reach": reach.get(str(row["parameter"]), 0),
                    "elasticity": float(row["elasticity"]),
                    "strongest_metric": str(row["metric"]),
                    "strongest_delta": float(row["absolute_delta"]),
                    "strongest_unit": str(row["unit"]),
                }
                for index, row in enumerate(ordered, start=1)
            ],
            "refused": [
                {"parameter": r["parameter"], "direction": r["direction"], "note": r["note"]}
                for r in sensitivity.refusals(rows)
            ],
            "excluded": sensitivity.excluded_parameters(ScenarioParameters()),
        }

    def sensitivity_parameter(self, name: str) -> Dict[str, object]:
        rows = [r for r in self._rows() if r["parameter"] == name and r["metric"] != "REFUSED"]
        readings = []
        for row in rows:
            readings.append(
                {
                    "direction": row["direction"],
                    "baseline_parameter": _number(row["baseline_parameter"]),
                    "perturbed_parameter": _number(row["perturbed_parameter"]),
                    "parameter_change_pct": _number(row["actual_parameter_change_pct"]),
                    "metric": row["metric"],
                    "unit": row["unit"],
                    "baseline_output": _number(row["baseline_output"]),
                    "perturbed_output": _number(row["perturbed_output"]),
                    "absolute_delta": _number(row["absolute_delta"]),
                    "relative_delta_pct": _number(row["relative_delta_pct"]),
                    "elasticity": _number(row["elasticity"]),
                    "note": row.get("note") or "",
                }
            )
        readings.sort(
            key=lambda r: (-abs(r["elasticity"] or 0.0), r["metric"], r["direction"])
        )
        return {"parameter": name, "readings": readings}

    def documents(self) -> List[Dict[str, object]]:
        rows = []
        for path in sorted(DOCS_DIR.glob("*.md")):
            match = re.match(r"(\d+)-(.*)\.md$", path.name)
            if not match:
                continue
            text = path.read_text(encoding="utf-8")
            rows.append(
                {
                    "number": int(match.group(1)),
                    "slug": match.group(2),
                    "file": path.name,
                    "title": markdown.title(text) or match.group(2),
                }
            )
        return rows

    def document(self, number: int) -> Optional[Dict[str, object]]:
        for path in sorted(DOCS_DIR.glob(f"{number:02d}-*.md")):
            text = path.read_text(encoding="utf-8")
            return {
                "number": number,
                "file": path.name,
                "title": markdown.title(text),
                "html": markdown.render(text),
            }
        return None


class Handler(BaseHTTPRequestHandler):
    library: Library
    runs: RunCache
    quiet: bool = True

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        if not self.quiet:
            super().log_message(format, *args)

    # ----------------------------------------------------------- responses
    def _json(self, payload: object, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, message: str) -> None:
        self._json({"error": message}, status)

    def _static(self, relative: str) -> None:
        target = (STATIC_DIR / relative).resolve()
        if STATIC_DIR not in target.parents or not target.is_file():
            self._error(HTTPStatus.NOT_FOUND, f"no such file: {relative}")
            return
        body = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in ("application/javascript",):
            content_type += "; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> Dict[str, object]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except ValueError:
            raise OverrideError("request body is not JSON") from None
        if not isinstance(payload, dict):
            raise OverrideError("request body must be an object")
        return payload

    # ---------------------------------------------------------------- routes
    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        path = unquote(url.path)
        try:
            if path in ("/", "/index.html"):
                self._static("index.html")
            elif path.startswith("/static/"):
                self._static(path[len("/static/"):])
            elif path == "/api/scenarios":
                self._json(self.library.scenarios())
            elif path == "/api/parameters":
                self._json(parameter_listing())
            elif path == "/api/runs":
                self._json(self.runs.listing())
            elif path.startswith("/api/runs/"):
                document = self.runs.lookup(path[len("/api/runs/"):])
                if document is None:
                    self._error(HTTPStatus.NOT_FOUND, "no such run")
                else:
                    self._json(document)
            elif path == "/api/run":
                query = parse_qs(url.query)
                scenario = (query.get("scenario") or [""])[0]
                options = json.loads((query.get("options") or ["{}"])[0])
                overrides = json.loads((query.get("overrides") or ["{}"])[0])
                self._json(self.runs.get(scenario, options, overrides))
            elif path == "/api/metrics":
                self._json(self.library.reference_metrics())
            elif path == "/api/sensitivity":
                self._json(self.library.sensitivity_ranking())
            elif path.startswith("/api/sensitivity/"):
                self._json(self.library.sensitivity_parameter(path[len("/api/sensitivity/"):]))
            elif path == "/api/docs":
                self._json(self.library.documents())
            elif re.match(r"^/api/docs/\d+$", path):
                document = self.library.document(int(path.rsplit("/", 1)[1]))
                if document is None:
                    self._error(HTTPStatus.NOT_FOUND, "no such document")
                else:
                    self._json(document)
            else:
                self._error(HTTPStatus.NOT_FOUND, f"no route for {path}")
        except OverrideError as error:
            self._error(HTTPStatus.BAD_REQUEST, str(error))
        except Exception as error:  # noqa: BLE001 - surfaced to the page
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, f"{type(error).__name__}: {error}")

    def do_POST(self) -> None:  # noqa: N802
        path = unquote(urlparse(self.path).path)
        try:
            if path == "/api/run":
                payload = self._body()
                self._json(
                    self.runs.get(
                        str(payload.get("scenario", "")),
                        payload.get("options") or {},
                        payload.get("overrides") or {},
                    )
                )
            elif path == "/api/metrics/collect":
                self._json({"metrics": self.library.current_metrics()})
            else:
                self._error(HTTPStatus.NOT_FOUND, f"no route for {path}")
        except OverrideError as error:
            self._error(HTTPStatus.BAD_REQUEST, str(error))
        except Exception as error:  # noqa: BLE001
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, f"{type(error).__name__}: {error}")


def make_server(host: str = "127.0.0.1", port: int = 8765, *, quiet: bool = True) -> ThreadingHTTPServer:
    handler = type("ViewerHandler", (Handler,), {"library": Library(), "runs": RunCache(), "quiet": quiet})
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    return server
