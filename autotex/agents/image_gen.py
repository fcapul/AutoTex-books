"""Image generation agent using Google Gemini."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autotex.config import ProjectConfig


# Aspect ratios supported by Gemini image generation.
SUPPORTED_ASPECT_RATIOS = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"]

# Map aspect ratios to recommended \includegraphics width for LaTeX.
_ASPECT_WIDTH: dict[str, str] = {
    "16:9": "0.85\\textwidth",
    "3:2": "0.8\\textwidth",
    "4:3": "0.75\\textwidth",
    "1:1": "0.6\\textwidth",
    "3:4": "0.5\\textwidth",
    "2:3": "0.45\\textwidth",
    "9:16": "0.4\\textwidth",
}


@dataclass
class ImageRequest:
    """A request for an AI-generated image extracted from LaTeX source."""

    description: str
    filename: str
    aspect_ratio: str = "16:9"
    reference: str = ""  # optional path to a reference image

    @classmethod
    def from_marker(cls, marker_content: str) -> ImageRequest:
        """Parse key=value pairs from an %%IMAGE_REQUEST{...}%% marker."""
        pairs: dict[str, str] = {}
        for match in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', marker_content):
            pairs[match.group(1)] = match.group(2)

        aspect = pairs.get("aspect_ratio", "16:9")
        if aspect not in SUPPORTED_ASPECT_RATIOS:
            aspect = "16:9"

        return cls(
            description=pairs.get("description", ""),
            filename=pairs.get("filename", "generated-image"),
            aspect_ratio=aspect,
            reference=pairs.get("reference", ""),
        )


# Regex to find image request markers in LaTeX source
IMAGE_MARKER_PATTERN = re.compile(r"%%IMAGE_REQUEST\{(.+?)\}%%")


def extract_image_requests(latex_content: str) -> list[ImageRequest]:
    """Extract all %%IMAGE_REQUEST{...}%% markers from LaTeX content."""
    return [
        ImageRequest.from_marker(m) for m in IMAGE_MARKER_PATTERN.findall(latex_content)
    ]


def _sanitize_latex(text: str) -> str:
    """Escape LaTeX special characters in plain text for safe insertion."""
    replacements = [
        ("\\", "\\textbackslash{}"),
        ("{", "\\{"),
        ("}", "\\}"),
        ("&", "\\&"),
        ("%", "\\%"),
        ("$", "\\$"),
        ("#", "\\#"),
        ("_", "\\_"),
        ("~", "\\textasciitilde{}"),
        ("^", "\\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _marker_to_include(match: re.Match) -> str:
    """Convert a single %%IMAGE_REQUEST%% match to a \\begin{figure} block."""
    req = ImageRequest.from_marker(match.group(1))
    width = _ASPECT_WIDTH.get(req.aspect_ratio, "0.8\\textwidth")
    caption = _sanitize_latex(req.description)
    return (
        f"\\begin{{figure}}[htbp]\n"
        f"  \\centering\n"
        f"  \\includegraphics[width={width}]{{{req.filename}}}\n"
        f"  \\caption{{{caption}}}\n"
        f"  \\label{{fig:{req.filename}}}\n"
        f"\\end{{figure}}"
    )


def replace_markers_with_includes(latex_content: str) -> str:
    """Replace all %%IMAGE_REQUEST{...}%% markers with \\includegraphics commands."""
    return IMAGE_MARKER_PATTERN.sub(_marker_to_include, latex_content)


def replace_first_marker(latex_content: str) -> str:
    """Replace only the first %%IMAGE_REQUEST{...}%% marker."""
    return IMAGE_MARKER_PATTERN.sub(_marker_to_include, latex_content, count=1)


class ImageGenAgent:
    """Generates scientific illustrations using Gemini.

    Best practices for prompting:
    - Text in images: enclose desired text in quotes within the prompt
      (e.g. '...with the text "Figure 1" in bold...').
    - Spatial reasoning: the model uses a thinking process, so complex
      spatial prompts ("Place Y to the left of X, behind Z") work well.
    - Character/style consistency: upload a reference image as primary
      input to maintain visual style across multiple generations.
    """

    def __init__(self, config: ProjectConfig) -> None:
        from google import genai

        self.client = genai.Client(api_key=config.api.gemini_api_key)
        self.model = config.api.gemini_model
        self.assets_dir = config.project_root / "assets"
        self.assets_dir.mkdir(exist_ok=True)
        self.project_root = config.project_root

    def generate(self, request: ImageRequest) -> Path:
        """Generate an image and save it to the assets/ directory.

        If the request includes a reference image path, it is uploaded
        alongside the prompt so Gemini can maintain style consistency
        or edit the reference.

        Returns the path to the saved image file.
        """
        from google.genai import types

        prompt = self._build_prompt(request)
        contents: list = []

        # Include reference image if provided
        if request.reference:
            ref_path = Path(request.reference)
            if not ref_path.is_absolute():
                ref_path = self.project_root / ref_path
            if ref_path.exists():
                mime = "image/png" if ref_path.suffix == ".png" else "image/jpeg"
                contents.append(
                    types.Part.from_bytes(data=ref_path.read_bytes(), mime_type=mime)
                )

        contents.append(prompt)

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        # Extract the image from the response parts
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                output_path = self.assets_dir / f"{request.filename}.png"
                output_path.write_bytes(part.inline_data.data)
                return output_path

        raise RuntimeError(
            f"Gemini did not return an image for: {request.description}"
        )

    def generate_all(self, requests: list[ImageRequest]) -> dict[str, Path]:
        """Generate images for all requests. Returns {filename: path} map."""
        results = {}
        for req in requests:
            path = self.generate(req)
            results[req.filename] = path
        return results

    def _build_prompt(self, request: ImageRequest) -> str:
        """Build a prompt optimized for scientific illustration.

        Includes aspect ratio guidance so the model produces images
        with the requested proportions.
        """
        ratio_hint = ""
        if request.aspect_ratio != "16:9":
            ratio_hint = f" The image aspect ratio should be {request.aspect_ratio}."

        ref_hint = ""
        if request.reference:
            ref_hint = (
                " Use the uploaded reference image to maintain visual style "
                "consistency. Match its color palette, line weight, and overall "
                "aesthetic while creating the new content described."
            )

        return (
            f"Create a clean, professional scientific illustration: "
            f"{request.description}. "
            f"Use a white background. The image should be suitable for "
            f"a printed textbook. Use clear labels, clean lines, and "
            f"professional scientific style. No decorative elements — "
            f"purely informational.{ratio_hint}{ref_hint}"
        )
