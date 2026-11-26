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


def parse_flowchart(code: str) -> Diagram:
    """Parse .flow text into positioned nodes and connector lines.

    Unindented lines start new rows. Nodes separated by ``->`` are laid out
    left-to-right. Indented lines continue a branch from the most recent node.
    A trailing ``!`` marks a warning node. Lines beginning with ``#`` are comments.
    """
    nodes: list[Node] = []
    arrows: list[tuple[int, int, int, int]] = []
    last_main_idx: int | None = None
    last_node_idx: int | None = None
    main_row = -1

    for line_number, raw_line in enumerate(code.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indented = raw_line[0].isspace()
        parts = _parse_parts(raw_line.strip(), line_number)

        if indented:
            if last_node_idx is None:
                raise FlowSyntaxError(
                    f"Line {line_number}: an indented branch needs a preceding node."
                )
            for label, warning in parts:
                parent = nodes[last_node_idx]
                x = parent.x + BOX_W + GAP_X
                y = parent.y
                nodes.append(Node(x, y, label, warning))
                arrows.append((parent.x + BOX_W, parent.y + BOX_H // 2,
                               x, y + BOX_H // 2))
                last_node_idx = len(nodes) - 1
            continue

        main_row += 1
        row_first_idx: int | None = None
        previous_idx: int | None = None
        for column, (label, warning) in enumerate(parts):
            x = START_X + column * (BOX_W + GAP_X)
            y = START_Y + main_row * (BOX_H + GAP_Y)
            nodes.append(Node(x, y, label, warning))
            current_idx = len(nodes) - 1

            if column == 0:
                row_first_idx = current_idx
                if last_main_idx is not None:
                    parent = nodes[last_main_idx]
                    arrows.append((parent.x + BOX_W // 2, parent.y + BOX_H,
                                   x + BOX_W // 2, y))
                last_main_idx = current_idx
            elif previous_idx is not None:
                parent = nodes[previous_idx]
                child = nodes[current_idx]
                arrows.append((parent.x + BOX_W, parent.y + BOX_H // 2,
                               child.x, child.y + BOX_H // 2))

            previous_idx = current_idx

        last_node_idx = previous_idx if previous_idx is not None else row_first_idx

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
        else:
            fill, stroke, text_color = "#ffffff", "#334155", "#0f172a"
        label = html.escape(node.label, quote=True)
        elements.append(
            f'<g transform="translate({node.x}, {node.y})">'
            f'<rect width="{BOX_W}" height="{BOX_H}" rx="10" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2" />'
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
