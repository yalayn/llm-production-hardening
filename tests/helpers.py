"""Shared helpers for the test suite."""

import ast
import pathlib


def imported_modules(module) -> set:
    """The modules a file actually imports, read from its AST.

    Grepping the source conflates a mention with an import, and these files
    explain in their docstrings why they duplicate each other -- which is worth
    keeping and is not a dependency.
    """
    tree = ast.parse(pathlib.Path(module.__file__).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names
