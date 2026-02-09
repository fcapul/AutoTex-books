"""Configuration management for AutoTex."""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass
class BookConfig:
    title: str = "Untitled Book"
    author: str = "Unknown Author"
    language: str = "english"
    chapters: list[dict] = field(default_factory=list)


@dataclass
class APIConfig:
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-pro-image-preview"


@dataclass
class LatexConfig:
    compiler: str = "pdflatex"
    compiler_args: list[str] = field(
        default_factory=lambda: ["-interaction=nonstopmode", "-halt-on-error"]
    )
    root_file: str = "main.tex"
    output_dir: str = "build"
    docclass_options: str = "12pt,oneside,openany"


@dataclass
class KDPConfig:
    enabled: bool = True
    trim_size: str = "novel"
    bleed: bool = False
    gutter: str = ""
    paper: str = "white"

    def to_package_options(self) -> str:
        """Build the \\usepackage options string for autotex-book.sty."""
        if not self.enabled:
            return ""
        parts = [f"kdp={self.trim_size}"]
        if self.bleed:
            parts.append("bleed")
        if self.gutter:
            parts.append(f"gutter={self.gutter}")
        if self.paper != "white":
            parts.append(f"paper={self.paper}")
        return ",".join(parts)


@dataclass
class ReviewConfig:
    max_revision_iterations: int = 3
    review_dpi: int = 200
    pages_per_review: int = 2
    final_review_interval: int = 5


@dataclass
class ProjectConfig:
    book: BookConfig
    api: APIConfig
    kdp: KDPConfig
    latex: LatexConfig
    review: ReviewConfig
    project_root: Path


def load_config(config_path: Path | None = None) -> ProjectConfig:
    """Load configuration from YAML file and environment variables.

    API keys are always read from environment variables, never from the
    config file. All other settings come from config.yaml with sensible
    defaults.
    """
    if config_path is None:
        config_path = Path("config.yaml")

    # Load .env from project root (walks up from config_path)
    env_path = config_path.resolve().parent / ".env"
    if not env_path.exists():
        # Try the repo root (two levels up from books/<name>/config.yaml)
        env_path = config_path.resolve().parent.parent.parent / ".env"
    load_dotenv(env_path, override=False)

    raw = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

    book_raw = raw.get("book", {})
    book = BookConfig(
        title=book_raw.get("title", "Untitled Book"),
        author=book_raw.get("author", "Unknown Author"),
        language=book_raw.get("language", "english"),
        chapters=book_raw.get("chapters", []),
    )

    api_raw = raw.get("api", {})
    api = APIConfig(
        gemini_api_key=os.environ.get("GOOGLE_API_KEY", ""),
        gemini_model=api_raw.get("gemini_model", "gemini-3-pro-image-preview"),
    )

    kdp_raw = raw.get("kdp", {})
    kdp = KDPConfig(
        enabled=kdp_raw.get("enabled", True),
        trim_size=kdp_raw.get("trim_size", "novel"),
        bleed=kdp_raw.get("bleed", False),
        gutter=kdp_raw.get("gutter", ""),
        paper=kdp_raw.get("paper", "white"),
    )

    latex_raw = raw.get("latex", {})
    latex = LatexConfig(
        compiler=latex_raw.get("compiler", "pdflatex"),
        compiler_args=latex_raw.get(
            "compiler_args", ["-interaction=nonstopmode", "-halt-on-error"]
        ),
        root_file=latex_raw.get("root_file", "main.tex"),
        output_dir=latex_raw.get("output_dir", "build"),
        docclass_options=latex_raw.get("docclass_options", "12pt,oneside,openany"),
    )

    review_raw = raw.get("review", {})
    review = ReviewConfig(
        max_revision_iterations=review_raw.get("max_revision_iterations", 3),
        review_dpi=review_raw.get("review_dpi", 200),
        pages_per_review=review_raw.get("pages_per_review", 2),
        final_review_interval=review_raw.get("final_review_interval", 5),
    )

    project_root = config_path.resolve().parent

    return ProjectConfig(
        book=book,
        api=api,
        kdp=kdp,
        latex=latex,
        review=review,
        project_root=project_root,
    )


def save_config(config: ProjectConfig, config_path: Path | None = None) -> None:
    """Save the current configuration back to YAML (excluding API keys)."""
    if config_path is None:
        config_path = config.project_root / "config.yaml"

    data = {
        "book": {
            "title": config.book.title,
            "author": config.book.author,
            "language": config.book.language,
            "chapters": config.book.chapters,
        },
        "api": {
            "gemini_model": config.api.gemini_model,
        },
        "kdp": {
            "enabled": config.kdp.enabled,
            "trim_size": config.kdp.trim_size,
            "bleed": config.kdp.bleed,
            "gutter": config.kdp.gutter,
            "paper": config.kdp.paper,
        },
        "latex": {
            "compiler": config.latex.compiler,
            "compiler_args": config.latex.compiler_args,
            "root_file": config.latex.root_file,
            "output_dir": config.latex.output_dir,
            "docclass_options": config.latex.docclass_options,
        },
        "review": {
            "max_revision_iterations": config.review.max_revision_iterations,
            "review_dpi": config.review.review_dpi,
            "pages_per_review": config.review.pages_per_review,
            "final_review_interval": config.review.final_review_interval,
        },
    }

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
