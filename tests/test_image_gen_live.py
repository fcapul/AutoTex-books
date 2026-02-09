"""Live integration test for image generation with real Gemini API.

Requires GOOGLE_API_KEY in environment. Skipped automatically if missing.

Run:
    python -m pytest tests/test_image_gen_live.py -v -s
"""

from __future__ import annotations

import os
import struct
from pathlib import Path

import pytest
import yaml

from autotex.agents.image_gen import (
    ImageGenAgent,
    ImageRequest,
    extract_image_requests,
    replace_markers_with_includes,
)
from autotex.config import load_config

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
pytestmark = pytest.mark.skipif(not GOOGLE_API_KEY, reason="GOOGLE_API_KEY not set")


def _write_config(tmp_path: Path) -> Path:
    """Write a minimal config.yaml and return its path."""
    cfg = {
        "book": {"title": "Test Book", "author": "Test"},
        "api": {"gemini_model": "gemini-3-pro-image-preview"},
        "kdp": {"enabled": True, "trim_size": "novel", "bleed": False, "gutter": "", "paper": "white"},
        "latex": {
            "compiler": "pdflatex",
            "compiler_args": ["-interaction=nonstopmode", "-halt-on-error"],
            "root_file": "main.tex",
            "output_dir": "build",
        },
        "review": {"max_revision_iterations": 3, "review_dpi": 200},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump(cfg, sort_keys=False), encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "text").mkdir()
    (tmp_path / "build").mkdir()
    return config_path


def _is_valid_png(data: bytes) -> bool:
    """Check PNG magic bytes and IHDR chunk."""
    if len(data) < 24:
        return False
    # PNG signature: 8 bytes
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return False
    # First chunk must be IHDR (bytes 12-15)
    if data[12:16] != b"IHDR":
        return False
    return True


def _png_dimensions(data: bytes) -> tuple[int, int]:
    """Extract (width, height) from PNG IHDR chunk."""
    width = struct.unpack(">I", data[16:20])[0]
    height = struct.unpack(">I", data[20:24])[0]
    return width, height


class TestLiveImageGeneration:
    """End-to-end test: config -> marker extraction -> Gemini API -> file on disk -> marker replacement."""

    def test_full_pipeline(self, tmp_path):
        # -- 1. Set up project directory with config --
        config_path = _write_config(tmp_path)
        config = load_config(config_path)

        # -- 2. Write a .tex file with an image marker --
        tex_content = (
            "\\chapter{Test Chapter}\n"
            "\\label{ch:test}\n"
            "\n"
            "Some introductory text about neural networks.\n"
            "\n"
            '%%IMAGE_REQUEST{description="A simple diagram of a feedforward neural network '
            'with three layers: input (3 nodes), hidden (4 nodes), output (2 nodes). '
            'Each layer is labeled. Arrows connect all nodes between adjacent layers.", '
            'filename="ch01-neural-net", aspect_ratio="16:9"}%%\n'
            "\n"
            "The network shown above illustrates a basic architecture.\n"
        )
        tex_path = tmp_path / "text" / "chapter01.tex"
        tex_path.write_text(tex_content, encoding="utf-8")

        # -- 3. Extract markers and verify parsing --
        requests = extract_image_requests(tex_content)
        assert len(requests) == 1, "Expected exactly 1 image marker"

        req = requests[0]
        assert req.filename == "ch01-neural-net"
        assert req.aspect_ratio == "16:9"
        assert "neural network" in req.description

        # -- 4. Generate image via real Gemini API --
        agent = ImageGenAgent(config)
        image_path = agent.generate(req)

        # -- 5. Verify image file exists and is valid PNG --
        assert image_path.exists(), f"Image file not found: {image_path}"
        assert image_path.name == "ch01-neural-net.png"
        assert image_path.parent == tmp_path / "assets"

        image_data = image_path.read_bytes()
        assert len(image_data) > 1000, f"Image suspiciously small: {len(image_data)} bytes"
        assert _is_valid_png(image_data), "Generated file is not a valid PNG"

        width, height = _png_dimensions(image_data)
        assert width > 0 and height > 0, f"Invalid dimensions: {width}x{height}"
        print(f"\n  Generated image: {image_path.name} ({width}x{height}, {len(image_data):,} bytes)")

        # -- 6. Replace markers and verify LaTeX output --
        replaced = replace_markers_with_includes(tex_content)

        # Marker should be gone
        assert "%%IMAGE_REQUEST" not in replaced

        # Figure environment should be present with correct values
        assert "\\begin{figure}[htbp]" in replaced
        assert "\\includegraphics[width=0.85\\textwidth]{ch01-neural-net}" in replaced
        assert "\\label{fig:ch01-neural-net}" in replaced
        assert "\\caption{" in replaced
        assert "\\end{figure}" in replaced

        # Surrounding text should be preserved
        assert "\\chapter{Test Chapter}" in replaced
        assert "The network shown above" in replaced

        print("  Marker replacement: OK")
        print("  Full pipeline: PASSED")
