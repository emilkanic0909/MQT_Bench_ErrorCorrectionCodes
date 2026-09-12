# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Initialization of the error correction module."""

# ruff: file-ignore[non-empty-init-module]

from __future__ import annotations

import importlib
import importlib.resources as ir
import inspect

from .ec_transpiler import ECTranspiler, LogicalQubit
from .shor_transpiler import ShorTranspiler
from .steane_transpiler import SteaneTranspiler

__all__ = [
    "ECTranspiler",
    "LogicalQubit",
    "ShorTranspiler",
    "SteaneTranspiler",
    "get_available_encoding_names",
    "get_transpiler",
]

_DISCOVERED_MODULES: list[str] = sorted(
    entry.name.removesuffix(".py")
    for entry in ir.files(__name__).iterdir()
    if entry.is_file() and entry.name.endswith(".py") and not entry.name.startswith("_")
)


def _discover_transpilers() -> dict[str, type[ECTranspiler]]:
    """Collect every concrete :class:`ECTranspiler` subclass defined in a module of this package.

    Abstract classes, classes that are not transpilers and classes merely imported into a module are ignored.

    Raises:
        TypeError: If a concrete transpiler does not define ``CODE_NAME`` or two transpilers share the same one.
    """
    transpilers: dict[str, type[ECTranspiler]] = {}
    for module_name in _DISCOVERED_MODULES:
        module = importlib.import_module(f"{__name__}.{module_name}")
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if not issubclass(cls, ECTranspiler) or inspect.isabstract(cls) or cls.__module__ != module.__name__:
                continue
            code_name = getattr(cls, "CODE_NAME", None)
            if code_name is None:
                msg = f"Transpiler '{cls.__qualname__}' must define a 'CODE_NAME'."
                raise TypeError(msg)
            if code_name in transpilers:
                msg = f"Transpilers '{transpilers[code_name].__qualname__}' and '{cls.__qualname__}' share the CODE_NAME '{code_name}'."
                raise TypeError(msg)
            transpilers[code_name] = cls
    return transpilers


_TRANSPILERS: dict[str, type[ECTranspiler]] = _discover_transpilers()


def get_available_encoding_names() -> list[str]:
    """Return the names of all supported error-correcting codes, i.e. the valid ``encoding`` values."""
    return sorted(_TRANSPILERS)


def get_transpiler(encoding: str) -> type[ECTranspiler]:
    """Return the transpiler class for the given error-correcting code.

    Arguments:
        encoding: Name of the error-correcting code (see :func:`get_available_encoding_names`).

    Raises:
        ValueError: If ``encoding`` is not a supported error-correcting code.
    """
    if encoding not in _TRANSPILERS:
        msg = (
            f"'{encoding}' is not a supported error-correcting code. Available codes: {get_available_encoding_names()}"
        )
        raise ValueError(msg)
    return _TRANSPILERS[encoding]
