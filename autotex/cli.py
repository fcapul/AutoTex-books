"""Command-line interface for AutoTex utilities.

Claude Code is the primary agent. This CLI provides utility commands
that Claude Code invokes via Bash for compilation, rendering, image
generation, and other atomic operations.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from autotex.config import load_config


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="autotex",
        description="AutoTex: utility commands for LaTeX book generation",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to config.yaml (default: ./config.yaml)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- compile ---
    subparsers.add_parser("compile", help="Compile the LaTeX document to PDF")

    # --- render ---
    render_parser = subparsers.add_parser(
        "render", help="Render specific PDF pages to PNG images"
    )
    render_parser.add_argument(
        "pages", nargs="+", type=int, help="Page numbers to render (0-based)"
    )
    render_parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Directory to save PNGs (default: build/)",
    )
    render_parser.add_argument(
        "--dpi", type=int, default=None,
        help="Resolution in DPI (default: from config, usually 200)",
    )

    # --- render-chapter ---
    rch_parser = subparsers.add_parser(
        "render-chapter", help="Render the last N pages of a specific chapter"
    )
    rch_parser.add_argument("number", type=int, help="Chapter number")
    rch_parser.add_argument("title", type=str, help="Chapter title")
    rch_parser.add_argument(
        "--count", type=int, default=2, help="Number of pages to render (default: 2)"
    )
    rch_parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Directory to save PNGs (default: build/)",
    )

    # --- images ---
    img_parser = subparsers.add_parser(
        "images",
        help="Extract image markers from a .tex file, generate via Gemini, replace markers",
    )
    img_parser.add_argument(
        "file", type=Path, help="Path to the .tex file (e.g. text/chapter03.tex)"
    )

    # --- search ---
    search_parser = subparsers.add_parser(
        "search", help="Find pages containing text in the compiled PDF"
    )
    search_parser.add_argument("text", type=str, help="Text to search for")

    # --- update-main ---
    subparsers.add_parser(
        "update-main",
        help="Regenerate main.tex from config.yaml chapters and KDP settings",
    )

    # --- init ---
    init_parser = subparsers.add_parser(
        "init", help="Create a new book project in books/<name>/"
    )
    init_parser.add_argument(
        "name", type=str, help="Book project name (used as folder name)"
    )

    # --- info ---
    subparsers.add_parser("info", help="Print current project configuration")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # init runs before loading config (the book doesn't exist yet)
    if args.command == "init":
        _cmd_init(args)
        return

    config = load_config(args.config)

    if args.command == "compile":
        _cmd_compile(config)
    elif args.command == "render":
        _cmd_render(config, args)
    elif args.command == "render-chapter":
        _cmd_render_chapter(config, args)
    elif args.command == "images":
        _cmd_images(config, args)
    elif args.command == "search":
        _cmd_search(config, args)
    elif args.command == "update-main":
        _cmd_update_main(config)
    elif args.command == "info":
        _cmd_info(config)


# ------------------------------------------------------------------
# Command implementations
# ------------------------------------------------------------------


def _cmd_init(args) -> None:
    """Create a new book project in books/<name>/."""
    name: str = args.name
    # Find the repo root (where autotex-book.sty lives)
    repo_root = Path.cwd()
    for parent in [Path.cwd()] + list(Path.cwd().parents):
        if (parent / "autotex-book.sty").exists():
            repo_root = parent
            break

    book_dir = repo_root / "books" / name
    if book_dir.exists():
        print(f"ERROR: {book_dir} already exists.")
        sys.exit(1)

    # Create directory structure
    for sub in ["text", "assets", "build"]:
        (book_dir / sub).mkdir(parents=True, exist_ok=True)
        (book_dir / sub / ".gitkeep").touch()

    # Copy root config.yaml as template (reset book-specific fields)
    root_config = repo_root / "config.yaml"
    if root_config.exists():
        shutil.copy2(root_config, book_dir / "config.yaml")
    else:
        # Write a minimal config
        (book_dir / "config.yaml").write_text(
            "book:\n"
            '  title: ""\n'
            '  author: "AutoTex"\n'
            "  chapters: []\n"
            "\n"
            "api:\n"
            '  gemini_model: "gemini-3-pro-image-preview"\n'
            "\n"
            "kdp:\n"
            "  enabled: false\n"
            '  trim_size: "novel"\n'
            "  bleed: false\n"
            '  gutter: ""\n'
            '  paper: "white"\n'
            "\n"
            "latex:\n"
            '  compiler: "pdflatex"\n'
            "  compiler_args:\n"
            '    - "-interaction=nonstopmode"\n'
            '    - "-halt-on-error"\n'
            '  root_file: "main.tex"\n'
            '  output_dir: "build"\n'
            "\n"
            "review:\n"
            "  max_revision_iterations: 3\n"
            "  review_dpi: 200\n"
            "  pages_per_review: 2\n"
            "  final_review_interval: 5\n",
            encoding="utf-8",
        )

    # Create book-specific CLAUDE.md
    (book_dir / "CLAUDE.md").write_text(
        f"# Book: {name}\n"
        f"\n"
        f"## Topic & Scope\n"
        f"<!-- Describe what this book is about -->\n"
        f"\n"
        f"## Target Audience\n"
        f"<!-- Who is this book for? -->\n"
        f"\n"
        f"## Writing Style\n"
        f"<!-- Formal/conversational, level of math, notation conventions -->\n"
        f"\n"
        f"## Special Instructions\n"
        f"<!-- Any book-specific guidelines for Claude Code -->\n",
        encoding="utf-8",
    )

    print(f"Created book project: {book_dir}")
    print(f"  config.yaml  — edit book title, author, chapters")
    print(f"  CLAUDE.md    — edit book-specific instructions")
    print(f"  text/        — chapter .tex files go here")
    print(f"  assets/      — generated images go here")
    print(f"  build/       — compilation output")
    print()
    print(f"Usage: python -m autotex --config books/{name}/config.yaml <command>")


def _cmd_compile(config) -> None:
    """Compile main.tex to PDF."""
    from autotex.latex.compiler import LatexCompiler

    compiler = LatexCompiler(config)
    if not compiler.check_available():
        print("ERROR: pdflatex not found. Install MiKTeX or TeX Live.")
        sys.exit(1)

    result = compiler.compile()
    if result.success:
        print(f"Compiled successfully: {compiler.output_path}")
        if result.warnings:
            print(f"Warnings ({len(result.warnings)}):")
            for w in result.warnings[:10]:
                print(f"  {w}")
    else:
        print("Compilation failed:")
        for err in result.errors:
            print(f"  {err}")
        sys.exit(1)


def _cmd_render(config, args) -> None:
    """Render specific PDF pages to PNG files."""
    from autotex.pdf.renderer import PDFRenderer

    renderer = PDFRenderer(config)
    pdf_path = config.project_root / config.latex.output_dir / "main.pdf"

    if not pdf_path.exists():
        print(f"PDF not found at {pdf_path}. Run 'autotex compile' first.")
        sys.exit(1)

    output_dir = args.output_dir or (config.project_root / config.latex.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    images = renderer.render_pages(pdf_path, args.pages)
    for page_num, img_bytes in zip(args.pages, images):
        out_file = output_dir / f"page_{page_num:04d}.png"
        out_file.write_bytes(img_bytes)
        print(f"Saved: {out_file}")


def _cmd_render_chapter(config, args) -> None:
    """Render the last N pages of a specific chapter."""
    from autotex.pdf.renderer import PDFRenderer

    renderer = PDFRenderer(config)
    pdf_path = config.project_root / config.latex.output_dir / "main.pdf"

    if not pdf_path.exists():
        print(f"PDF not found at {pdf_path}. Run 'autotex compile' first.")
        sys.exit(1)

    pages = renderer.get_chapter_last_pages(
        pdf_path, args.number, args.title, args.count
    )

    if not pages:
        print(f"Could not find Chapter {args.number}: {args.title} in the PDF.")
        sys.exit(1)

    output_dir = args.output_dir or (config.project_root / config.latex.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    images = renderer.render_pages(pdf_path, pages)
    for page_num, img_bytes in zip(pages, images):
        out_file = output_dir / f"page_{page_num:04d}.png"
        out_file.write_bytes(img_bytes)
        print(f"Saved: {out_file}")


def _cmd_images(config, args) -> None:
    """Extract image markers, generate images via Gemini, replace markers."""
    from autotex.agents.image_gen import (
        ImageGenAgent,
        extract_image_requests,
        replace_markers_with_includes,
    )

    tex_path: Path = args.file
    if not tex_path.is_absolute():
        tex_path = config.project_root / tex_path

    if not tex_path.exists():
        print(f"File not found: {tex_path}")
        sys.exit(1)

    content = tex_path.read_text(encoding="utf-8")
    requests = extract_image_requests(content)

    if not requests:
        print("No %%IMAGE_REQUEST{...}%% markers found.")
        return

    print(f"Found {len(requests)} image request(s). Generating...")
    agent = ImageGenAgent(config)
    agent.generate_all(requests)

    content = replace_markers_with_includes(content)
    tex_path.write_text(content, encoding="utf-8")
    print(f"Updated {tex_path} with \\includegraphics commands.")


def _cmd_search(config, args) -> None:
    """Find pages containing specific text in the compiled PDF."""
    from autotex.pdf.search import PDFSearch

    pdf_path = config.project_root / config.latex.output_dir / "main.pdf"
    if not pdf_path.exists():
        print(f"PDF not found at {pdf_path}. Run 'autotex compile' first.")
        sys.exit(1)

    searcher = PDFSearch()
    pages = searcher.find_pages_with_text(pdf_path, args.text)

    if pages:
        print(f"Found on page(s): {', '.join(str(p) for p in pages)}")
    else:
        print(f"Text '{args.text}' not found in PDF.")


def _cmd_update_main(config) -> None:
    """Regenerate main.tex from config.yaml chapters and KDP settings."""
    from autotex.models import BookPlan

    if not config.book.chapters:
        print("No chapters in config.yaml. Plan the book first.")
        sys.exit(1)

    plan = BookPlan.from_dict({
        "title": config.book.title,
        "chapters": config.book.chapters,
    })

    includes = "\n".join(
        f"\\include{{text/chapter{ch.number:02d}}}"
        for ch in plan.chapters
    )

    # Document class: for KDP use twoside, otherwise default to a4paper
    if config.kdp.enabled:
        docclass = "\\documentclass[12pt,twoside,openright]{book}"
    else:
        docclass = "\\documentclass[12pt,a4paper,openright]{book}"

    # Build \usepackage line with optional KDP options
    kdp_opts = config.kdp.to_package_options()
    if kdp_opts:
        usepackage = f"\\usepackage[{kdp_opts}]{{autotex-book}}"
    else:
        usepackage = "\\usepackage{autotex-book}"

    template = (
        f"{docclass}\n"
        f"{usepackage}\n"
        f"\n"
        f"\\title{{{plan.title}}}\n"
        f"\\author{{{config.book.author}}}\n"
        f"\\date{{\\today}}\n"
        f"\n"
        f"\\begin{{document}}\n"
        f"\n"
        f"\\frontmatter\n"
        f"\\maketitle\n"
        f"\\tableofcontents\n"
        f"\n"
        f"\\mainmatter\n"
        f"{includes}\n"
        f"\n"
        f"\\backmatter\n"
        f"\\bibliographystyle{{plainnat}}\n"
        f"% \\bibliography{{references}}\n"
        f"\n"
        f"\\end{{document}}\n"
    )

    main_tex = config.project_root / config.latex.root_file
    main_tex.write_text(template, encoding="utf-8")
    print(f"Updated {main_tex} with {len(plan.chapters)} chapter(s).")


def _cmd_info(config) -> None:
    """Print current project configuration."""
    print(f"Title:    {config.book.title}")
    print(f"Author:   {config.book.author}")
    print(f"Chapters: {len(config.book.chapters)}")
    if config.book.chapters:
        for ch in config.book.chapters:
            print(f"  {ch['number']}. {ch['title']}")
    print(f"\nKDP:      {'enabled' if config.kdp.enabled else 'disabled'}")
    if config.kdp.enabled:
        print(f"  Trim:   {config.kdp.trim_size}")
        print(f"  Bleed:  {config.kdp.bleed}")
        print(f"  Paper:  {config.kdp.paper}")
    print(f"\nCompiler: {config.latex.compiler}")
    print(f"Root:     {config.latex.root_file}")
    print(f"Output:   {config.latex.output_dir}/")
    print(f"Gemini:   {config.api.gemini_model}")


if __name__ == "__main__":
    main()
