"""Export the most recent Claude Code session for this repo to Markdown.

Usage (from the repo root):

    python scripts/export_chat.py

Writes ``chat-transcript.md`` next to itself (one level up).

Claude Code stores each session as one JSON-Lines file under
``%USERPROFILE%\\.claude\\projects\\<slug>\\<session-id>.jsonl`` where the
slug is the absolute path of the project with ``\\`` and ``:`` replaced by
``-``. Each line is a single event: user prompts, assistant turns (text /
thinking / tool_use), and various tool results / metadata.

We render only the parts that make the conversation readable:

  * user prompts (the string ones the human typed)
  * assistant text blocks (what was shown to the user)
  * a one-line marker for each tool the assistant invoked, so the reader can
    see "the assistant ran Bash here" without having to wade through the
    tool's output

Everything else (file-history-snapshot, attachment, ai-title,
permission-mode, last-prompt, raw tool_result payloads, internal thinking)
is skipped.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def find_session_file() -> Path:
    """Return the newest .jsonl session file for this repo, or raise."""
    home = Path(os.path.expanduser("~"))
    projects = home / ".claude" / "projects"
    if not projects.exists():
        raise SystemExit(f"No Claude Code projects directory at {projects}")

    # The repo root is one level above this script.
    repo_root = Path(__file__).resolve().parent.parent
    # Claude Code's slug for the project directory is the absolute path with
    # every non-alphanumeric character (drive colons, path separators,
    # underscores) replaced with "-". Empirically observed on Windows:
    #   C:\Users\s34859\s34859_kafka -> C--Users-s34859-s34859-kafka
    raw = str(repo_root)
    slug_chars = [c if c.isalnum() else "-" for c in raw]
    slug = "".join(slug_chars)
    candidates = [projects / slug, projects / slug.lstrip("-")]
    project_dir = next((p for p in candidates if p.exists()), None)
    if project_dir is None:
        # Fall back to whichever subdir mentions this repo's name.
        repo_name = repo_root.name.replace("_", "-")
        for sub in projects.iterdir():
            if sub.is_dir() and repo_name in sub.name:
                project_dir = sub
                break
    if project_dir is None:
        raise SystemExit(
            f"Could not find a Claude Code project dir for {repo_root} under {projects}"
        )

    sessions = sorted(
        project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not sessions:
        raise SystemExit(f"No .jsonl sessions in {project_dir}")
    return sessions[0]


def render_user_message(content) -> str | None:
    """Plain user prompts are strings. Tool-result payloads (a list of
    dicts) are noise and are skipped."""
    if isinstance(content, str):
        return content.strip()
    return None


def render_assistant_message(content) -> str | None:
    """Render the visible parts of an assistant turn.

    ``content`` is a list of blocks. We keep ``text`` blocks verbatim and
    summarise ``tool_use`` blocks as a single italic marker line. Thinking
    blocks are skipped.
    """
    if not isinstance(content, list):
        return None

    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        kind = block.get("type")
        if kind == "text":
            text = (block.get("text") or "").strip()
            if text:
                parts.append(text)
        elif kind == "tool_use":
            name = block.get("name", "?")
            tool_input = block.get("input") or {}
            hint = ""
            # Surface a short, useful hint per tool.
            if name == "Bash":
                hint = tool_input.get("description") or tool_input.get("command", "")
            elif name in ("Read", "Write"):
                hint = tool_input.get("file_path", "")
            elif name == "Edit":
                hint = tool_input.get("file_path", "")
            elif name == "Grep":
                hint = tool_input.get("pattern", "")
            elif name == "Glob":
                hint = tool_input.get("pattern", "")
            elif name == "AskUserQuestion":
                qs = tool_input.get("questions") or []
                if qs:
                    hint = qs[0].get("question", "")
            elif name in ("TaskCreate", "TaskUpdate"):
                hint = (
                    tool_input.get("subject")
                    or tool_input.get("status")
                    or ""
                )
            hint = (hint[:120] + "...") if len(hint) > 120 else hint
            parts.append(f"_[tool: **{name}**{(' — ' + hint) if hint else ''}]_")
    return "\n\n".join(parts).strip() or None


def main() -> int:
    session = find_session_file()
    print(f"Reading session: {session}", file=sys.stderr)

    out_path = Path(__file__).resolve().parent.parent / "chat-transcript.md"
    out_lines: list[str] = []
    out_lines.append(f"# Claude Code session — `{session.name}`\n")
    out_lines.append(
        "_Auto-generated transcript of the conversation that built this repo. "
        "Tool calls are summarised; their raw output and internal reasoning "
        "are omitted._\n"
    )

    last_role: str | None = None
    with session.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") not in ("user", "assistant"):
                continue
            msg = ev.get("message") or {}
            role = msg.get("role")
            content = msg.get("content")

            if role == "user":
                rendered = render_user_message(content)
                if rendered is None:
                    continue
                if last_role != "user":
                    out_lines.append("\n## User\n")
                out_lines.append(rendered + "\n")
                last_role = "user"
            elif role == "assistant":
                rendered = render_assistant_message(content)
                if rendered is None:
                    continue
                if last_role != "assistant":
                    out_lines.append("\n## Assistant\n")
                out_lines.append(rendered + "\n")
                last_role = "assistant"

    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote {out_path} ({out_path.stat().st_size:,} bytes)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
