#!/usr/bin/env python3
"""Task Manager - Natural language task management powered by Claude."""
import sys
from pathlib import Path

# Allow running from project root without installing
sys.path.insert(0, str(Path(__file__).parent))

# Load .env file if present (ANTHROPIC_API_KEY etc.)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import storage
import agent
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.rule import Rule


console = Console()

BANNER = """
 ████████╗ █████╗ ███████╗██╗  ██╗    ███╗   ███╗ ██████╗ ██████╗
    ██╔══╝██╔══██╗██╔════╝██║ ██╔╝    ████╗ ████║██╔════╝ ██╔══██╗
    ██║   ███████║███████╗█████╔╝     ██╔████╔██║██║  ███╗██████╔╝
    ██║   ██╔══██║╚════██║██╔═██╗     ██║╚██╔╝██║██║   ██║██╔══██╗
    ██║   ██║  ██║███████║██║  ██╗    ██║ ╚═╝ ██║╚██████╔╝██║  ██║
    ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝
"""

HELP_TEXT = """\
[bold cyan]使い方 (自然言語で話しかけてください):[/bold cyan]

  タスクを追加する    → [yellow]「レポートを書く」を高優先度で追加して[/yellow]
  一覧を見る         → [yellow]タスクを全部見せて[/yellow]
  完了にする         → [yellow]タスク1を完了にして[/yellow]
  検索する           → [yellow]「Python」に関するタスクを探して[/yellow]
  削除する           → [yellow]タスク3を削除して[/yellow]
  統計を見る         → [yellow]タスクの統計を教えて[/yellow]

  [dim]quit / exit / q[/dim] → 終了
  [dim]help / h[/dim]        → このヘルプを表示
"""


def print_banner() -> None:
    console.print(BANNER, style="bold blue", highlight=False)
    console.print(
        Panel(
            "[bold white]Claude のツールユースで動くタスク管理CLI[/bold white]\n"
            "[dim]Powered by Anthropic claude-sonnet-4-6[/dim]",
            border_style="blue",
        )
    )


def print_help() -> None:
    console.print(Panel(HELP_TEXT, title="ヘルプ", border_style="cyan"))


def main() -> None:
    print_banner()
    storage.init_db()

    console.print()
    print_help()
    console.print(Rule(style="dim"))

    history: list[dict] = []

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]あなた[/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Bye![/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit", "q", "終了"}:
            console.print("[dim]Bye![/dim]")
            break

        if user_input.lower() in {"help", "h", "ヘルプ"}:
            print_help()
            continue

        # Show a spinner while Claude thinks
        with console.status("[dim]Claude が考えています...[/dim]", spinner="dots"):
            try:
                reply, history = agent.chat(user_input, history)
            except RuntimeError as exc:
                console.print(f"[bold red]エラー:[/bold red] {exc}")
                break
            except Exception as exc:
                console.print(f"[bold red]予期しないエラー:[/bold red] {exc}")
                continue

        console.print()
        console.print(
            Panel(
                Text(reply),
                title="[bold magenta]Claude[/bold magenta]",
                border_style="magenta",
            )
        )


if __name__ == "__main__":
    main()
