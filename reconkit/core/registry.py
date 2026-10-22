"""Plugin registry. Modules come in two kinds:
  - subprocess modules wrap an external CLI (declare `binary`)
  - native modules implement a feature with Python libs (declare `pymods`)
Each declares which target types it supports. Adding a tool = one small module."""

from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass, field
from typing import Callable

from .schema import ReconResult, TargetType

# A module function takes (target: str) and returns a ReconResult.
ModuleFn = Callable[[str], ReconResult]


@dataclass
class Module:
    name: str
    target_types: tuple[TargetType, ...]
    run: ModuleFn
    binary: str | None = None            # external CLI, if subprocess module
    pymods: tuple[str, ...] = ()          # required importable modules, if native
    install_hint: str = ""

    @property
    def kind(self) -> str:
        return "subprocess" if self.binary else "native"

    @property
    def installed(self) -> bool:
        if self.binary:
            return shutil.which(self.binary) is not None
        return all(importlib.util.find_spec(p) is not None for p in self.pymods)


_REGISTRY: dict[str, Module] = {}


def register(
    name: str,
    target_types: tuple[TargetType, ...],
    binary: str | None = None,
    pymods: tuple[str, ...] = (),
    install_hint: str = "",
):
    def deco(fn: ModuleFn) -> ModuleFn:
        _REGISTRY[name] = Module(
            name=name, target_types=target_types, run=fn,
            binary=binary, pymods=pymods, install_hint=install_hint,
        )
        return fn
    return deco


def all_modules() -> list[Module]:
    return list(_REGISTRY.values())


def modules_for(target_type: TargetType) -> list[Module]:
    return [m for m in _REGISTRY.values() if target_type in m.target_types]


def get(name: str) -> Module | None:
    return _REGISTRY.get(name)
