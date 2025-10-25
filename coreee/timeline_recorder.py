from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json, html
from typing import Any, Dict, Optional

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class Event:
    ts: str
    turn: int
    role: str
    etype: str
    summary: str
    data: Dict[str, Any]

class Recorder:
    """Registra eventos y genera salidas (JSONL/Markdown/HTML)."""

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.jsonl = self.root / "events.jsonl"
        self.events: list[Event] = []

    # --- API principal ---
    def emit(self, *, turn: int, role: str, etype: str, summary: str = "", data: Optional[Dict[str, Any]] = None) -> Event:
        ev = Event(ts=_now_iso(), turn=turn, role=role, etype=etype, summary=summary, data=data or {})
        self.events.append(ev)
        with open(self.jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(ev), ensure_ascii=False) + "\n")
        return ev

    def write_blob(self, rel_path: str, content: str) -> str:
        p = self.root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return str(p)

    # --- Salidas legibles ---
    def _fmt_json(self, obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False, indent=2)

    def save_markdown(self, path: str) -> str:
        lines = ["# Timeline de ejecución", "", f"_Total eventos: {len(self.events)}_", ""]
        for i, ev in enumerate(self.events, 1):
            lines.append(f"## {i:02d}. [{ev.ts}] {ev.role} · {ev.etype}")
            if ev.summary:
                lines.append("")
                lines.append(ev.summary)
            if ev.data:
                lines.append("")
                lines.append("```json")
                lines.append(self._fmt_json(ev.data))
                lines.append("```")
            lines.append("")
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        return path

    def save_html(self, path: str) -> str:
        parts = []
        parts.append("<!doctype html><meta charset='utf-8'><title>Timeline</title>")
        parts.append(
            "<style>body{font-family:system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:24px}"
            " details{margin:8px 0;padding:8px 12px;border:1px solid #ddd;border-radius:10px}"
            " summary{font-weight:600;cursor:pointer}"
            " code,pre{font-family:ui-monospace,Consolas,Monaco,monospace}"
            " .ts{color:#555;margin-left:6px} .meta{color:#777}</style>"
        )
        parts.append(f"<h1>Timeline de ejecución</h1><div class='meta'>Total eventos: {len(self.events)}</div>")
        for i, ev in enumerate(self.events, 1):
            header = html.escape(f"{i:02d}. {ev.role} · {ev.etype}")
            parts.append("<details open>")
            parts.append(f"<summary>{header} <span class='ts'>[{html.escape(ev.ts)}]</span></summary>")
            if ev.summary:
                parts.append(f"<p>{html.escape(ev.summary)}</p>")
            if ev.data:
                parts.append("<pre>")
                parts.append(html.escape(self._fmt_json(ev.data)))
                parts.append("</pre>")
            parts.append("</details>")
        Path(path).write_text("\n".join(parts), encoding="utf-8")
        return path
