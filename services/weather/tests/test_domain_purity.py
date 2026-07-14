"""Keep the hexagon clean: the domain must have no I/O, no clock, no provider deps.

Uses the AST (not a substring grep) so that merely *mentioning* a forbidden name in a
docstring or comment is fine — only real imports and clock calls fail. Rule evaluation for
high-consequence farming advice must stay reproducible and side-effect free.
"""

from __future__ import annotations

import ast
import pathlib

DOMAIN = pathlib.Path(__file__).resolve().parents[1] / "src" / "rythu_weather" / "domain"

FORBIDDEN_IMPORTS = {"httpx", "requests", "boto3", "boto", "os", "socket", "urllib", "zoneinfo", "random"}
# Attribute-call names that read a wall clock (e.g. datetime.now(), date.today()).
FORBIDDEN_CLOCK_CALLS = {"now", "today", "monotonic"}


def _violations(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out += [f"import {a.name}" for a in node.names if a.name.split(".")[0] in FORBIDDEN_IMPORTS]
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in FORBIDDEN_IMPORTS:
                out.append(f"from {node.module}")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in FORBIDDEN_CLOCK_CALLS
        ):
            out.append(f"call .{node.func.attr}()")
    return out


def test_domain_package_is_pure():
    offenders: dict[str, list[str]] = {}
    for py in DOMAIN.rglob("*.py"):
        found = _violations(py)
        if found:
            offenders[py.name] = found
    assert not offenders, f"domain must stay pure, found: {offenders}"
