"""Render simple, indentation-based .flow files as standalone HTML flowcharts."""

from __future__ import annotations

import argparse
import html
import os
import tempfile
import webbrowser
from dataclasses import dataclass
from pathlib import Path


BOX_W = 200
BOX_H = 64
GAP_X = 64
GAP_Y = 64
START_X = 48
START_Y = 48
SVG_NS = "http://www.w3.org/2000/svg"


class FlowSyntaxError(ValueError):
    """Raised when a .flow document contains invalid syntax."""


@dataclass(frozen=True)
class Node:
    x: int
    y: int
    label: str
    warning: bool = False
    kind: str = "process"
    branch: str | None = None


@dataclass(frozen=True)
class Diagram:
    nodes: tuple[Node, ...]
    arrows: tuple[tuple[int, int, int, int], ...]
    width: int
    height: int


def _parse_parts(line: str, line_number: int) -> list[tuple[str, bool]]:
    raw_parts = line.split("->")
    if any(not part.strip() for part in raw_parts):
        raise FlowSyntaxError(
            f"Line {line_number}: empty node. Put a label on both sides of every '->'."
        )
    parts: list[tuple[str, bool]] = []
    for raw_part in raw_parts:
        label = raw_part.strip()
        warning = label.endswith("!")
        if warning:
            label = label[:-1].rstrip()
        if not label:
            raise FlowSyntaxError(f"Line {line_number}: warning marker '!' needs a label.")
        parts.append((label, warning))
    return parts


_NODE_TYPES = {"start", "process", "decision", "input", "output", "warning", "end"}


def _typed_label(value: str, line_number: int) -> tuple[str, str, bool]:
    """Read an optional 'type: label' declaration."""
    kind = "process"
    label = value.strip()
    if ":" in label:
        possible_kind, remainder = label.split(":", 1)
        if possible_kind.strip().lower() in _NODE_TYPES:
            kind = possible_kind.strip().lower()
            label = remainder.strip()
    if not label:
        raise FlowSyntaxError(f"Line {line_number}: a node type needs a label.")
    warning = kind == "warning" or label.endswith("!")
    if label.endswith("!"):
        label = label[:-1].rstrip()
    if not label:
        raise FlowSyntaxError(f"Line {line_number}: warning marker '!' needs a label.")
    return label, kind, warning


def parse_flowchart(code: str) -> Diagram:
    """Parse legacy arrows and the typed .flow syntax into a positioned diagram.

    Typed syntax uses 'type: label' declarations. Indented yes/no/true/false
    lines branch from the most recent node. Unindented declarations continue
    the main path vertically. Untyped lines remain ordinary process nodes.
    """
    nodes: list[Node] = []
    arrows: list[tuple[int, int, int, int]] = []
    last_main_idx: int | None = None
    last_node_idx: int | None = None
    main_row = -1
    branch_counts: dict[int, int] = {}
    branch_parent_idx: int | None = None

    for line_number, raw_line in enumerate(code.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indented = raw_line[0].isspace()
        text = raw_line.strip()
        branch: str | None = None
        if indented:
            import re
            match = re.match(r"^(yes|no|true|false)\s*:\s*(.*)$", text, re.IGNORECASE)
            if match:
                branch = match.group(1).upper()
                text = match.group(2).strip()
                if not text:
                    raise FlowSyntaxError(f"Line {line_number}: branch '{branch.lower()}' needs a node.")

        parts = _parse_parts(text, line_number)
        if indented and last_node_idx is None:
            raise FlowSyntaxError(
                f"Line {line_number}: an indented branch needs a preceding node."
            )

        if indented:
            parent_idx = branch_parent_idx if branch_parent_idx is not None else last_node_idx
            branch_parent_idx = parent_idx
            parent = nodes[parent_idx]
            branch_index = branch_counts.get(parent_idx, 0)
            branch_counts[parent_idx] = branch_index + 1
            for part_index, (raw_label, legacy_warning) in enumerate(parts):
                label, kind, warning = _typed_label(raw_label, line_number)
                warning = warning or legacy_warning
                x = parent.x + BOX_W + GAP_X
                y = parent.y + branch_index * (BOX_H + GAP_Y)
                if part_index:
                    previous = nodes[-1]
                    x = previous.x + BOX_W + GAP_X
                    y = previous.y
                nodes.append(Node(x, y, label, warning, kind, branch if part_index == 0 else None))
                arrows.append((parent.x + BOX_W, parent.y + BOX_H // 2,
                               x, y + BOX_H // 2))
                parent = nodes[-1]
                last_node_idx = len(nodes) - 1
            continue

        branch_parent_idx = None
        main_row += 1
        previous_idx: int | None = None
        for column, (raw_label, legacy_warning) in enumerate(parts):
            label, kind, warning = _typed_label(raw_label, line_number)
            warning = warning or legacy_warning
            x = START_X + column * (BOX_W + GAP_X)
            y = START_Y + main_row * (BOX_H + GAP_Y)
            nodes.append(Node(x, y, label, warning, kind))
            current_idx = len(nodes) - 1
            if column == 0:
                if last_main_idx is not None:
                    parent = nodes[last_main_idx]
                    arrows.append((parent.x + BOX_W // 2, parent.y + BOX_H,
                                   x + BOX_W // 2, y))
                last_main_idx = current_idx
            elif previous_idx is not None:
                parent = nodes[previous_idx]
                arrows.append((parent.x + BOX_W, parent.y + BOX_H // 2,
                               x, y + BOX_H // 2))
            previous_idx = current_idx
        last_node_idx = previous_idx

    if not nodes:
        raise FlowSyntaxError("The .flow file is empty. Add at least one node.")

    width = max(node.x for node in nodes) + BOX_W + START_X
    height = max(node.y for node in nodes) + BOX_H + START_Y
    return Diagram(tuple(nodes), tuple(arrows), width, height)


def render_flowchart(code: str, title: str = "Flowchart") -> str:
    """Return a complete, self-contained HTML document containing the SVG."""
    diagram = parse_flowchart(code)
    title_html = html.escape(title, quote=True)
    elements: list[str] = []

    for x1, y1, x2, y2 in diagram.arrows:
        elements.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            'stroke="#64748b" stroke-width="2.5" marker-end="url(#arrowhead)" />'
        )

    for node in diagram.nodes:
        if node.warning:
            fill, stroke, text_color = "#fff1f2", "#e11d48", "#9f1239"
        elif node.kind == "start":
            fill, stroke, text_color = "#dcfce7", "#16a34a", "#166534"
        elif node.kind == "end":
            fill, stroke, text_color = "#dbeafe", "#2563eb", "#1e40af"
        elif node.kind == "decision":
            fill, stroke, text_color = "#fef3c7", "#d97706", "#92400e"
        elif node.kind in {"input", "output"}:
            fill, stroke, text_color = "#ede9fe", "#7c3aed", "#5b21b6"
        else:
            fill, stroke, text_color = "#ffffff", "#334155", "#0f172a"
        label = html.escape(node.label, quote=True)
        if node.kind == "decision":
            shape = f'<polygon points="{BOX_W / 2},0 {BOX_W},{BOX_H / 2} {BOX_W / 2},{BOX_H} 0,{BOX_H / 2}" fill="{fill}" stroke="{stroke}" stroke-width="2" />'
        elif node.kind in {"input", "output"}:
            shape = f'<polygon points="18,0 {BOX_W},0 {BOX_W - 18},{BOX_H} 0,{BOX_H}" fill="{fill}" stroke="{stroke}" stroke-width="2" />'
        else:
            radius = 28 if node.kind in {"start", "end"} else 10
            shape = f'<rect width="{BOX_W}" height="{BOX_H}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2" />'
        branch = (f'<text x="8" y="-7" font-family="system-ui, sans-serif" '
                  f'font-size="11" font-weight="700" fill="#475569">{html.escape(node.branch or "")}</text>'
                  if node.branch else "")
        elements.append(
            f'<g transform="translate({node.x}, {node.y})">{branch}{shape}'
            f'<text x="{BOX_W / 2}" y="{BOX_H / 2 + 5}" '
            'font-family="system-ui, sans-serif" font-size="14" '
            f'font-weight="600" fill="{text_color}" text-anchor="middle">'
            f'{label}</text></g>'
        )

    svg = (
        f'<svg xmlns="{SVG_NS}" width="{diagram.width}" height="{diagram.height}" '
        f'viewBox="0 0 {diagram.width} {diagram.height}" role="img" '
        f'aria-label="{html.escape(title, quote=True)}">'
        '<defs><marker id="arrowhead" markerWidth="10" markerHeight="8" '
        'refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 z" '
        'fill="#64748b" /></marker></defs>'
        + "".join(elements)
        + "</svg>"
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title_html}</title>
  <style>
    :root {{ color-scheme: light; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-width: 100%; min-height: 100vh; padding: 32px;
           display: flex; justify-content: center; align-items: flex-start;
           background: #f1f5f9; font-family: system-ui, sans-serif; }}
    main {{ max-width: 100%; overflow: auto; padding: 20px; background: white;
            border-radius: 14px; box-shadow: 0 10px 30px rgba(15,23,42,.08); }}
    svg {{ display: block; max-width: none; }}
  </style>
</head>
<body><main>{svg}</main></body>
</html>
"""


def build_svg_flowchart(
    code: str,
    title: str = "Flowchart",
    output_path: str | os.PathLike[str] | None = None,
    open_browser: bool = True,
) -> str:
    """Render a chart to HTML and optionally open it in the default browser.

    Returns the path to the generated HTML file. If ``output_path`` is omitted,
    a temporary file is created so the user's working directory stays clean.
    """
    document = render_flowchart(code, title=title)
    if output_path is None:
        fd, destination = tempfile.mkstemp(suffix=".html", prefix="flow_")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(document)
    else:
        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(document, encoding="utf-8")
        destination = str(path)

    if open_browser:
        webbrowser.open(Path(destination).as_uri())
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a .flow file as an HTML flowchart.")
    parser.add_argument("file", help="Path to the .flow file")
    parser.add_argument("-o", "--output", help="Write HTML to this path instead of a temporary file")
    parser.add_argument("--no-open", action="store_true", help="Do not open the result in a browser")
    args = parser.parse_args(argv)

    source = Path(args.file)
    try:
        code = source.read_text(encoding="utf-8")
        destination = build_svg_flowchart(
            code,
            title=source.name,
            output_path=args.output,
            open_browser=not args.no_open,
        )
    except (OSError, UnicodeError, FlowSyntaxError) as exc:
        parser.exit(2, f"flow_runner: error: {exc}\n")

    print(f"Flowchart written to: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
