"""LaTeX compilation wrapper using pdflatex."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autotex.config import ProjectConfig


@dataclass
class CompilationResult:
    success: bool
    errors: list[str]
    warnings: list[str]
    log_output: str


class LatexCompiler:
    """Wraps pdflatex to compile the book."""

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config
        self.root_file = config.project_root / config.latex.root_file
        self.build_dir = config.project_root / config.latex.output_dir
        self.output_path = self.build_dir / "main.pdf"

    def check_available(self) -> bool:
        """Check whether the LaTeX compiler is installed."""
        return shutil.which(self.config.latex.compiler) is not None

    def _find_sty_dir(self) -> str | None:
        """Walk up from project_root to find the directory containing autotex-book.sty.

        Returns the directory as a string, or None if the .sty is already
        in project_root or not found.
        """
        # If .sty is in project_root, no extra TEXINPUTS needed
        if (self.config.project_root / "autotex-book.sty").exists():
            return None
        # Walk up parent directories
        for parent in self.config.project_root.parents:
            if (parent / "autotex-book.sty").exists():
                return str(parent)
        return None

    def compile(self, runs: int = 2) -> CompilationResult:
        """Compile the LaTeX document.

        Runs the compiler multiple times to resolve cross-references
        and table of contents. Returns a CompilationResult with errors
        and warnings parsed from the log.
        """
        if not self.check_available():
            return CompilationResult(
                success=False,
                errors=[
                    f"LaTeX compiler '{self.config.latex.compiler}' not found. "
                    "Install MiKTeX (https://miktex.org) or TeX Live."
                ],
                warnings=[],
                log_output="",
            )

        self.build_dir.mkdir(exist_ok=True)

        cmd = [
            self.config.latex.compiler,
            f"-output-directory={self.build_dir}",
            *self.config.latex.compiler_args,
            str(self.root_file),
        ]

        # Add parent .sty directory to TEXINPUTS so pdflatex can find
        # autotex-book.sty when compiling from a book subfolder.
        env = os.environ.copy()
        sty_dir = self._find_sty_dir()
        if sty_dir:
            sep = ";" if os.name == "nt" else ":"
            env["TEXINPUTS"] = f".{sep}{sty_dir}{sep}" + env.get("TEXINPUTS", "")

        full_log = ""
        for i in range(runs):
            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(self.config.project_root),
                    capture_output=True,
                    text=True,
                    timeout=120,
                    env=env,
                )
                full_log += result.stdout + result.stderr

                if result.returncode != 0 and i == runs - 1:
                    errors, warnings = self._parse_log(full_log)
                    return CompilationResult(
                        success=False,
                        errors=errors,
                        warnings=warnings,
                        log_output=full_log,
                    )
            except subprocess.TimeoutExpired:
                return CompilationResult(
                    success=False,
                    errors=["Compilation timed out after 120 seconds."],
                    warnings=[],
                    log_output=full_log,
                )

        errors, warnings = self._parse_log(full_log)
        return CompilationResult(
            success=True,
            errors=errors,
            warnings=warnings,
            log_output=full_log,
        )

    def _parse_log(self, log: str) -> tuple[list[str], list[str]]:
        """Extract errors and warnings from LaTeX log output."""
        errors = []
        warnings = []
        for line in log.split("\n"):
            stripped = line.strip()
            if stripped.startswith("!"):
                errors.append(stripped)
            elif "LaTeX Warning" in stripped or re.search(r"Package \S+ Warning", stripped):
                warnings.append(stripped)
        return errors, warnings
