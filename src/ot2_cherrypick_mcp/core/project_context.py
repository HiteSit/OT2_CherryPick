"""Runtime project directory context for the MCP server."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


_MAX_RECENT = 10


@dataclass
class ProjectContext:
    """Holds the active project directory and recent-project history.

    Attributes:
        project_dir: The active project directory.
        auto_created: Whether the directory was auto-created as a temp dir.
        recent_projects: History of recent project directories (max 10).
    """

    project_dir: Path
    auto_created: bool = False
    recent_projects: list[str] = field(default_factory=list)

    def switch_to(self, new_dir: Path, auto_created: bool = False) -> None:
        """Save the current project to history and switch to *new_dir*."""
        current = str(self.project_dir)
        # Add current to history (avoid duplicates)
        if current in self.recent_projects:
            self.recent_projects.remove(current)
        self.recent_projects.insert(0, current)
        # Trim to max length
        self.recent_projects = self.recent_projects[:_MAX_RECENT]

        self.project_dir = new_dir
        self.auto_created = auto_created

    def resolve_path(self, relative: str | Path) -> Path:
        """Resolve *relative* against the active project directory."""
        candidate = Path(relative)
        return candidate if candidate.is_absolute() else self.project_dir / candidate

    def info(self) -> dict[str, object]:
        """Return a serialisable summary of the current state."""
        return {
            "project_dir": str(self.project_dir),
            "auto_created": self.auto_created,
            "recent_projects": list(self.recent_projects),
        }
