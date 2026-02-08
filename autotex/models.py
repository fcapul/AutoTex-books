"""Data models for book planning."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChapterSpec:
    """Specification for a single chapter."""

    number: int
    title: str
    sections: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class BookPlan:
    """Complete book outline."""

    title: str
    chapters: list[ChapterSpec] = field(default_factory=list)

    def display(self) -> str:
        """Format the plan for display to the user."""
        lines = [f"Book: {self.title}", "=" * 60]
        for ch in self.chapters:
            lines.append(f"\nChapter {ch.number}: {ch.title}")
            if ch.description:
                lines.append(f"  {ch.description}")
            for i, sec in enumerate(ch.sections, 1):
                lines.append(f"  {ch.number}.{i} {sec}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to a dict for saving to config.yaml."""
        return {
            "title": self.title,
            "chapters": [
                {
                    "number": ch.number,
                    "title": ch.title,
                    "sections": ch.sections,
                    "description": ch.description,
                }
                for ch in self.chapters
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> BookPlan:
        """Reconstruct from a config.yaml dict."""
        chapters = [
            ChapterSpec(
                number=ch["number"],
                title=ch["title"],
                sections=ch.get("sections", []),
                description=ch.get("description", ""),
            )
            for ch in data.get("chapters", [])
        ]
        return cls(title=data.get("title", "Untitled"), chapters=chapters)
