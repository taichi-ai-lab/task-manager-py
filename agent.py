"""Claude agent with tool use for natural language task management."""
import os
import json
import traceback
from pathlib import Path
from typing import Any, Optional
import anthropic
from tools import TOOL_SCHEMAS, run_tool

_LOG = Path(__file__).parent / "error.log"


def _log_exc() -> None:
    """Write the current exception traceback to error.log."""
    with open(_LOG, "a", encoding="utf-8") as f:
        traceback.print_exc(file=f)

_client: Optional[anthropic.Anthropic] = None

SYSTEM_PROMPT = """\
You are a helpful task management assistant. You help users manage their tasks \
using the available tools.

Guidelines:
- When a user asks to add, create, or set a task, use add_task.
- When a user asks to see, show, or list tasks, use list_tasks.
- When a user asks to complete, finish, update, or edit a task, use update_task.
- When a user asks to remove or delete a task, use delete_task.
- When a user asks to search or find tasks, use search_tasks.
- When a user asks for stats, summary, or overview, use get_stats.
- Always confirm actions with a brief, friendly message in the same language the user used.
- When listing tasks, format them clearly (ID, title, status, priority).
- Dates should be in YYYY-MM-DD format.
"""


def _block_to_dict(block: Any) -> dict:
    """Convert a response content block (Pydantic model) to a plain ASCII-safe dict.

    Why: Pydantic v2's model_dump_json() uses a Rust serializer with ensure_ascii=False,
    embedding raw Unicode bytes. Re-encoding through json.loads(json.dumps(...)) forces
    Python's standard json module (ensure_ascii=True by default) so all non-ASCII chars
    become escaped sequences safe for any downstream codec.
    """
    if block.type == "text":
        raw = {"type": "text", "text": block.text}
    elif block.type == "tool_use":
        raw = {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }
    else:
        raw = block.model_dump() if hasattr(block, "model_dump") else {"type": block.type}

    # Round-trip through JSON with ensure_ascii=True to guarantee ASCII-safe strings.
    return json.loads(json.dumps(raw, ensure_ascii=True))


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY environment variable is not set.\n"
                "Export it: export ANTHROPIC_API_KEY=sk-ant-..."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _chat(user_message: str, history: list[dict]) -> tuple[str, list[dict]]:
    """
    Send a user message, execute any tool calls, and return the assistant reply.

    Args:
        user_message: The user's natural language input.
        history: Conversation history (list of {role, content} dicts).

    Returns:
        (reply_text, updated_history)
    """
    client = _get_client()
    history = history + [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=history,
        )

        # Convert Pydantic content blocks to plain dicts.
        # Passing raw Pydantic objects causes the SDK's Rust-based JSON serializer
        # (ensure_ascii=False) to embed raw Unicode, which then fails when the
        # underlying HTTP layer tries to encode with ASCII on Windows cp932.
        history.append({
            "role": "assistant",
            "content": [_block_to_dict(b) for b in response.content],
        })

        if response.stop_reason == "end_turn":
            # Extract text reply
            reply = next(
                (block.text for block in response.content if hasattr(block, "text")),
                "",
            )
            return reply, history

        if response.stop_reason == "tool_use":
            # Execute each tool call and collect results
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                result = run_tool(block.name, dict(block.input))
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            # Feed tool results back to Claude
            history.append({"role": "user", "content": tool_results})
            # Loop again to get Claude's response after tools
            continue

        # Unexpected stop reason
        break

    return "(No response)", history


def chat(user_message: str, history: list[dict]) -> tuple[str, list[dict]]:
    # Thin wrapper that logs unexpected exceptions to error.log before re-raising.
    try:
        return _chat(user_message, history)
    except Exception:
        _log_exc()
        raise
