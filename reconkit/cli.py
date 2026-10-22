"""reconkit CLI — unified OSINT orchestrator.

    reconkit doctor                     # show which tools are installed
    reconkit list                       # list modules and the targets they take
    reconkit run <target> --type email  # run every module that fits the target
    reconkit run acme.com --type domain --only subfinder,theharvester --md report.md
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from . import modules  # noqa: F401 — side effect: registers all modules
from .core import registry
from .core.schema import TargetType, ReconResult, dump_json, dump_markdown

app = typer.Typer(add_completion=False, help="Unified OSINT orchestrator.",
                  invoke_without_command=True)
console = Console()


@app.callback()
def _default(ctx: typer.Context):
    """With no subcommand, launch the interactive menu."""
    if ctx.invoked_subcommand is None:
        from .tui import menu
        menu()


@app.command()
def menu():
    """Launch the interactive X-osint-style menu."""
    from .tui import menu as run_menu
    run_menu()


@app.command()
def doctor():
    """Check which underlying tools are installed on this machine."""
    table = Table(title="reconkit module status")
    table.add_column("module"); table.add_column("kind")
    table.add_column("installed"); table.add_column("install hint")
    for m in registry.all_modules():
        mark = "[green]yes[/green]" if m.installed else "[red]no[/red]"
        table.add_row(m.name, m.kind, mark, "" if m.installed else m.install_hint)
    console.print(table)


@app.command("list")
def list_modules():
    """List registered modules and the target types they accept."""
    table = Table(title="reconkit modules")
    table.add_column("module"); table.add_column("accepts")
    for m in registry.all_modules():
        table.add_row(m.name, ", ".join(t.value for t in m.target_types))
    console.print(table)


@app.command()
def run(
    target: str = typer.Argument(..., help="username / email / domain / phone / ip"),
    type_: str = typer.Option(..., "--type", "-t", help="target type"),
    only: str = typer.Option("", "--only", help="comma-separated module names to limit to"),
    json_out: str = typer.Option("", "--json", help="write JSON report to this path"),
    md_out: str = typer.Option("", "--md", help="write Markdown report to this path"),
):
    """Run every module that matches the target type and merge the results."""
    try:
        tt = TargetType(type_.lower())
    except ValueError:
        console.print(f"[red]unknown target type:[/red] {type_}")
        console.print(f"valid: {', '.join(t.value for t in TargetType)}")
        raise typer.Exit(2)

    mods = registry.modules_for(tt)
    if only:
        wanted = {s.strip() for s in only.split(",")}
        mods = [m for m in mods if m.name in wanted]
    if not mods:
        console.print(f"[yellow]no modules for target type {tt.value}[/yellow]")
        raise typer.Exit(1)

    results: list[ReconResult] = []
    for m in mods:
        if not m.installed:
            console.print(f"[yellow]skip {m.name}: not installed[/yellow] ({m.install_hint})")
            continue
        console.print(f"[cyan]→ running {m.name}…[/cyan]")
        results.append(m.run(target))

    # Console summary
    total = sum(len(r.findings) for r in results)
    console.print(f"\n[bold]{total} findings across {len(results)} modules[/bold]")
    for r in results:
        if r.ok:
            console.print(f"  {r.module}: {len(r.findings)} ({r.duration_s}s)")
        else:
            # escape: errors like "[Errno -2] ..." would otherwise parse as markup
            console.print(f"  [red]{r.module}: failed[/red] — {escape(r.error or '')}")

    if json_out:
        Path(json_out).write_text(dump_json(results), encoding="utf-8")
        console.print(f"[green]wrote {json_out}[/green]")
    if md_out:
        Path(md_out).write_text(dump_markdown(results, target), encoding="utf-8")
        console.print(f"[green]wrote {md_out}[/green]")


if __name__ == "__main__":
    app()
