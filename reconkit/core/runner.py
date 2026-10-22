"""Thin subprocess helper so modules don't repeat boilerplate."""

from __future__ import annotations

import subprocess
import time


class ToolError(RuntimeError):
    pass


def run_cmd(args: list[str], timeout: int = 300) -> tuple[str, str, int]:
    """Run an external tool. Returns (stdout, stderr, returncode).

    Never uses shell=True — args are passed as a list so a target string
    can't inject shell metacharacters.
    """
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as e:
        raise ToolError(f"binary not found: {args[0]}") from e
    except subprocess.TimeoutExpired as e:
        raise ToolError(f"timed out after {timeout}s: {' '.join(args)}") from e
    return proc.stdout, proc.stderr, proc.returncode


def timed():
    """Return a start timestamp; pair with elapsed()."""
    return time.time()


def elapsed(start: float) -> float:
    return round(time.time() - start, 2)
