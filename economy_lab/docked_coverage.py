"""docs/141 prediction 7: how much of the day's code a docked day runs.

Denominator: every executable line of every function in ``model.py``
reachable from ``Economy.step`` through a call by name (``self.f(``,
``region.f(``, ``x.f(``), resolved against every function ``model.py``
defines with that name.  Static, so it over-counts reach rather than
under-counts it.

Numerator: those lines a docked economy executes over its first sixty
days, at a small size (40 commodities, 2 regions), traced.

    python -m economy_lab.docked_coverage
"""
from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

from . import model
from .wright_battery import DOCKED, build_ours

SOURCE = Path(model.__file__)


def _functions():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    found = defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    found[item.name].append((node.name, item))
    for item in tree.body:
        if isinstance(item, ast.FunctionDef):
            found[item.name].append((None, item))
    return found


def reachable():
    """(class, function) pairs reachable from Economy.step, and their nodes."""
    functions = _functions()
    seen = {}
    stack = [("Economy", next(f for c, f in functions["step"] if c == "Economy"))]
    while stack:
        owner, node = stack.pop()
        key = (owner, node.name)
        if key in seen:
            continue
        seen[key] = node
        for call in ast.walk(node):
            if isinstance(call, ast.Call):
                target = call.func
                name = target.attr if isinstance(target, ast.Attribute) else (
                    target.id if isinstance(target, ast.Name) else None)
                for candidate in functions.get(name, ()):
                    stack.append(candidate)
    return seen


def body_lines(node):
    """Line numbers holding a statement in the function's body, nested
    functions included, the docstring and the ``def`` line excluded."""
    lines = set()
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
        body = body[1:]
    for statement in body:
        for sub in ast.walk(statement):
            if isinstance(sub, ast.stmt):
                lines.add(sub.lineno)
    return lines


def main():
    nodes = reachable()
    wanted = set()
    for node in nodes.values():
        wanted |= body_lines(node)
    economy = build_ours(0, commodities=40, regions=2, **DOCKED)
    hit = set()
    path = str(SOURCE)

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != path:
            return None
        if event == "line":
            hit.add(frame.f_lineno)
        return tracer

    sys.settrace(tracer)
    try:
        economy.step(60)
    finally:
        sys.settrace(None)
    executed = wanted & hit
    print(f"functions reachable from step: {len(nodes)}")
    print(f"statement lines in them:       {len(wanted)}")
    print(f"executed by sixty docked days: {len(executed)}")
    print(f"share:                         {len(executed) / len(wanted):.3f}")
    per = []
    for (owner, name), node in sorted(nodes.items(), key=lambda kv: kv[1].lineno):
        lines = body_lines(node)
        per.append((len(lines & hit), len(lines), f"{owner}.{name}"))
    untouched = [label for done, total, label in per if done == 0]
    print(f"functions never entered ({len(untouched)}):", ", ".join(untouched))


if __name__ == "__main__":
    main()
