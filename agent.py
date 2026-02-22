"""Claude agent with tool use for natural language task management."""
import os
from typing import Optional
import anthropic
from tools import TOOL_SCHEMAS, run_tool

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


def chat(user_message: str, history: list[dict]) -> tuple[str, list[dict]]:
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

        # Append assistant message to history
        history.append({"role": "assistant", "content": response.content})

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
