"""Interactive menu — the X-osint-style front end, rebuilt on reconkit's
registry (clean-room; no X-osint code). Banner + numbered target types;
pick one, enter a target, and every matching module runs."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .core import registry
from .core.schema import TargetType, ReconResult

console = Console()

BANNER = r"""
  ___ ___  ___ ___  _  _ _  _____ _____
 | _ \ __|/ __/ _ \| \| | |/ /_ _|_   _|
 |   / _|| (_| (_) | .` | ' < | |  | |
 |_|_\___|\___\___/|_|\_|_|\_\___| |_|
        unified osint orchestrator
"""

# Each menu row maps a label to a target type.
MENU: list[tuple[str, TargetType]] = [
    ("Username  — social-account hunt", TargetType.USERNAME),
    ("Email     — breach / site registration", TargetType.EMAIL),
    ("Domain    — subdomains, DNS, emails", TargetType.DOMAIN),
    ("IP        — geolocation + reverse DNS", TargetType.IP),
    ("Phone     — carrier / region / timezone", TargetType.PHONE),
    ("Image     — EXIF + GPS metadata", TargetType.IMAGE),
]


def _run_for(tt: TargetType, target: str) -> list[ReconResult]:
    mods = registry.modules_for(tt)
    results: list[ReconResult] = []
    for m in mods:
        if not m.installed:
            console.print(f"[yellow]skip {m.name}: not installed[/yellow] ({m.install_hint})")
            continue
        console.print(f"[cyan]→ {m.name}…[/cyan]")
        results.append(m.run(target))
    return results


def _show(results: list[ReconResult]) -> None:
    if not results:
        console.print("[yellow]no modules ran.[/yellow]")
        return
    for r in results:
        t = Table(title=f"{r.module}  ({len(r.findings)} findings, {r.duration_s}s)",
                  show_header=False)
        if r.error:
            t.add_row("[red]error[/red]", r.error)
        for f in r.findings:
            t.add_row(f.label, f.value)
        console.print(t)


def menu() -> None:
    console.print(Panel.fit(BANNER, border_style="magenta"))
    console.print("[dim]Authorized targets only — your own accounts, CTF scope, "
                  "or written permission.[/dim]\n")
    while True:
        tbl = Table(show_header=False, box=None)
        for i, (label, _) in enumerate(MENU, 1):
            tbl.add_row(f"[bold cyan]{i}[/bold cyan]", label)
        tbl.add_row("[bold cyan]d[/bold cyan]", "Doctor — show installed tools")
        tbl.add_row("[bold cyan]q[/bold cyan]", "Quit")
        console.print(tbl)

        choice = console.input("\n[bold]reconkit>[/bold] ").strip().lower()
        if choice in ("q", "quit", "exit"):
            console.print("bye.")
            return
        if choice == "d":
            _doctor()
            continue
        if not choice.isdigit() or not (1 <= int(choice) <= len(MENU)):
            console.print("[red]invalid choice[/red]\n")
            continue

        label, tt = MENU[int(choice) - 1]
        prompt = "path to image" if tt is TargetType.IMAGE else tt.value
        target = console.input(f"enter {prompt}: ").strip()
        if not target:
            continue
        results = _run_for(tt, target)
        _show(results)
        console.print()


def _doctor() -> None:
    t = Table(title="installed tools")
    t.add_column("module"); t.add_column("kind"); t.add_column("ok"); t.add_column("hint")
    for m in registry.all_modules():
        ok = "[green]yes[/green]" if m.installed else "[red]no[/red]"
        t.add_row(m.name, m.kind, ok, "" if m.installed else m.install_hint)
    console.print(t)
