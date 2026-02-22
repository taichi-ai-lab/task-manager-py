# Task Manager

Claude の **Tool Use（ツールユース）** を活用した、自然言語で操作できる Python 製タスク管理 CLI です。

## 特徴

- **自然言語で操作** — コマンドを覚えなくていい。日本語・英語でそのまま話しかけるだけ
- **Claude Tool Use** — Anthropic の claude-sonnet-4-6 が意図を解釈し、適切なツールを自動で呼び出す
- **SQLite 永続化** — タスクはローカル (`~/.task_manager/tasks.db`) に保存
- **リッチな CLI** — `rich` ライブラリによるカラフルな表示

## アーキテクチャ

```
main.py       ← CLIのエントリーポイント (rich による表示)
agent.py      ← Claude との会話ループ・Tool Use の処理
tools.py      ← ツール定義 (JSON Schema) とディスパッチャー
storage.py    ← SQLite による CRUD 操作
models.py     ← Task データクラス
```

```
ユーザー入力
    ↓
agent.py  →  Claude API (claude-sonnet-4-6)
                ↓  tool_use
tools.py  →  storage.py  →  SQLite
                ↓  tool_result
             Claude API
                ↓  end_turn
          テキスト返答
    ↓
main.py   →  rich で表示
```

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/taichi-ai-lab/task-manager-py.git
cd task-manager-py
```

### 2. 仮想環境を作成して依存パッケージをインストール

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. API キーを設定

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
# Windows (PowerShell): $env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

> `.env` ファイルを使う場合は `python-dotenv` を利用してください。

### 4. 起動

```bash
python main.py
```

## 使い方

起動後、日本語（または英語）で自由に話しかけてください。

| やりたいこと | 例 |
|---|---|
| タスクを追加 | `「議事録を作成する」を高優先度で明日までに追加して` |
| 一覧を表示 | `タスクを全部見せて` |
| 進行中のみ表示 | `進行中のタスクを見せて` |
| 完了にする | `タスク2を完了にして` |
| 編集する | `タスク1の優先度を高にして` |
| 検索する | `「Python」に関するタスクを探して` |
| 削除する | `タスク3を削除して` |
| 統計を確認 | `タスクの統計を教えて` |

### タスクのフィールド

| フィールド | 説明 | 値 |
|---|---|---|
| `title` | タスク名 | テキスト |
| `description` | 詳細説明 | テキスト |
| `status` | 状態 | `pending` / `in_progress` / `done` |
| `priority` | 優先度 | `low` / `medium` / `high` |
| `due_date` | 期日 | `YYYY-MM-DD` |
| `tags` | タグ | 文字列リスト |

### 特殊コマンド

| コマンド | 動作 |
|---|---|
| `help` / `h` | ヘルプを表示 |
| `quit` / `exit` / `q` | 終了 |

## 利用ツール一覧

Claude が自動で呼び出すツール (関数) の一覧です。

| ツール名 | 説明 |
|---|---|
| `add_task` | タスクを追加する |
| `list_tasks` | タスクを一覧表示（フィルター対応）|
| `update_task` | タスクを更新・完了にする |
| `delete_task` | タスクを削除する |
| `search_tasks` | キーワードでタスクを検索する |
| `get_stats` | タスクの統計を取得する |

## 動作要件

- Python 3.11 以上
- Anthropic API キー ([取得はこちら](https://console.anthropic.com/))
