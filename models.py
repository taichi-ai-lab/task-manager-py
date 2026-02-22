"""Task data model."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    id: int
    title: str
    description: str
    status: str          # "pending" | "in_progress" | "done"
    priority: str        # "low" | "medium" | "high"
    created_at: str
    due_date: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: tuple) -> "Task":
        task_id, title, description, status, priority, created_at, due_date, tags_str = row
        tags = tags_str.split(",") if tags_str else []
        return cls(
            id=task_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            created_at=created_at,
            due_date=due_date,
            tags=tags,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "due_date": self.due_date,
            "tags": self.tags,
        }

    @staticmethod
    def now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
