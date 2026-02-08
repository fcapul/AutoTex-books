"""Image generation agent using Google Gemini."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autotex.config import ProjectConfig


@dataclass
class ImageRequest:
    """A request for an AI-generated image extracted from LaTeX source."""

    description: str
    filename: str
    aspect_ratio: str = "16:9"

    @classmethod
    def from_marker(cls, marker_content: str) -> ImageRequest:
        """Parse key=value pairs from an %%IMAGE_REQUEST{...}%% marker."""
        pairs: dict[str, str] = {}
        for match in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', marker_content):
            pairs[match.group(1)] = match.group(2)

        return cls(
            description=pairs.get("description", ""),
            filename=pairs.get("filename", "generated-image"),
            aspect_ratio=pairs.get("aspect_ratio", "16:9"),
        )


# Regex to find image request markers in LaTeX source
IMAGE_MARKER_PATTERN = re.compile(r"%%IMAGE_REQUEST\{(.+?)\}%%")


def extract_image_requests(latex_content: str) -> list[ImageRequest]:
    """Extract all %%IMAGE_REQUEST{...}%% markers from LaTeX content."""
    return [
        ImageRequest.from_marker(m) for m in IMAGE_MARKER_PATTERN.findall(latex_content)
    ]


def replace_markers_with_includes(latex_content: str) -> str:
    """Replace %%IMAGE_REQUEST{...}%% markers with \\includegraphics commands."""

    def _replace(match: re.Match) -> str:
        req = ImageRequest.from_marker(match.group(1))
        return (
            f"\\begin{{figure}}[htbp]\n"
            f"  \\centering\n"
            f"  \\includegraphics[width=0.8\\textwidth]{{{req.filename}}}\n"
            f"  \\caption{{{req.description}}}\n"
            f"  \\label{{fig:{req.filename}}}\n"
            f"\\end{{figure}}"
        )

    return IMAGE_MARKER_PATTERN.sub(_replace, latex_content)


class ImageGenAgent:
    """Generates scientific illustrations using Gemini."""

    def __init__(self, config: ProjectConfig) -> None:
        from google import genai

        self.client = genai.Client(api_key=config.api.gemini_api_key)
        self.model = config.api.gemini_model
        self.assets_dir = config.project_root / "assets"

    def generate(self, request: ImageRequest) -> Path:
        """Generate an image and save it to the assets/ directory.

        Returns the path to the saved image file.
        """
        prompt = self._build_prompt(request)

        from google.genai import types

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
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
        """Build a prompt optimized for scientific illustration."""
        return (
            f"Create a clean, professional scientific illustration: "
            f"{request.description}. "
            f"Use a white background. The image should be suitable for "
            f"a printed textbook. Use clear labels, clean lines, and "
            f"professional scientific style. No decorative elements — "
            f"purely informational."
        )
