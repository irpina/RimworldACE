"""Which ``sum()`` this interpreter has, and why the port cares (docs/142).

CPython 3.12 changed the builtin ``sum()`` over floats to Neumaier's
compensated summation.  The laboratory calls ``sum()`` throughout, so the
same model run under 3.11 and under 3.12 differs in the last bits, and
the C# port reproduces the 3.12 behaviour (``CompensatedSum``, docs/53
§3).  Every fixture the port is checked against must therefore be written
by an interpreter that compensates.

The test is behavioural rather than a version number, so it stays right
on any implementation: a compensating ``sum`` recovers the 1.0 that a
naive running total loses.
"""
from __future__ import annotations

import sys


def sums_compensated() -> bool:
    return sum([1e16, 1.0, -1e16]) == 1.0


def require_compensated_sum() -> None:
    """Refuse to write port fixtures with the wrong ``sum()``."""
    if not sums_compensated():
        raise SystemExit(
            f"Python {sys.version.split()[0]} does not compensate sum(); the port's "
            "fixtures must be written by CPython 3.12 or later (docs/142). "
            "Run this with python3.12."
        )
