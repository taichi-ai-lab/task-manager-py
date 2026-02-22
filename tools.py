"""Claude tool definitions and their implementations."""
import json
from typing import Any
import storage


# ── Tool schemas (passed to Claude API) ───────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "name": "add_task",
        "description": "Add a new task to the task manager.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short title of the task.",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description (optional).",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Task priority. Defaults to 'medium'.",
                },
                "due_date": {
                    "type": "string",
                    "description": "Due date in YYYY-MM-DD format (optional).",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tag strings (optional).",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "list_tasks",
        "description": "List tasks. Can filter by status, priority, or tag.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "done"],
                    "description": "Filter by status (optional).",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Filter by priority (optional).",
                },
                "tag": {
                    "type": "string",
                    "description": "Filter by tag (optional).",
                },
            },
        },
    },
    {
        "name": "update_task",
        "description": "Update fields of an existing task. Can also change status to complete it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "ID of the task to update.",
                },
                "title": {"type": "string"},
                "description": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "done"],
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
                "due_date": {
                    "type": "string",
                    "description": "Due date in YYYY-MM-DD format.",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "delete_task",
        "description": "Delete a task by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "ID of the task to delete.",
                }
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "search_tasks",
        "description": "Search tasks by keyword in title, description, or tags.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keyword to search for.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_stats",
        "description": "Get statistics about tasks (total, by status, by priority, overdue count).",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]


# ── Tool dispatcher ────────────────────────────────────────────────────────────

def run_tool(name: str, inputs: dict[str, Any]) -> str:
    """Execute a tool by name and return a JSON string result."""
    try:
        if name == "add_task":
            task = storage.add_task(**inputs)
            return json.dumps({"success": True, "task": task.to_dict()}, ensure_ascii=False)

        elif name == "list_tasks":
            tasks = storage.list_tasks(**inputs)
            return json.dumps(
                {"tasks": [t.to_dict() for t in tasks], "count": len(tasks)},
                ensure_ascii=False,
            )

        elif name == "update_task":
            task_id = inputs.pop("task_id")
            task = storage.update_task(task_id, **inputs)
            if task is None:
                return json.dumps({"success": False, "error": f"Task {task_id} not found."})
            return json.dumps({"success": True, "task": task.to_dict()}, ensure_ascii=False)

        elif name == "delete_task":
            ok = storage.delete_task(inputs["task_id"])
            return json.dumps({"success": ok})

        elif name == "search_tasks":
            tasks = storage.search_tasks(inputs["query"])
            return json.dumps(
                {"tasks": [t.to_dict() for t in tasks], "count": len(tasks)},
                ensure_ascii=False,
            )

        elif name == "get_stats":
            stats = storage.get_stats()
            return json.dumps(stats, ensure_ascii=False)

        else:
            return json.dumps({"error": f"Unknown tool: {name}"})

    except Exception as exc:
        return json.dumps({"error": str(exc)})
