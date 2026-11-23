import sys
import os
import tempfile
import webbrowser

def build_svg_flowchart(code, title="Flowchart"):
    BOX_W, BOX_H = 180, 50
    GAP_X, GAP_Y = 60, 50
    START_X, START_Y = 50, 50

    nodes = []
    arrows = []
    last_main_idx = None
    last_row_idx = None
    current_row = -1

    for raw_line in code.strip().splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue

        is_indented = raw_line.startswith((" ", "\t"))
        parts = [p.strip() for p in raw_line.strip().split("->") if p.strip()]

        if not is_indented:
            current_row += 1
            col = 0
            for i, text in enumerate(parts):
                is_warn = text.endswith("!")
                clean_text = text.rstrip("!")
                x = START_X + col * (BOX_W + GAP_X)
                y = START_Y + current_row * (BOX_H + GAP_Y)
                idx = len(nodes)
                nodes.append((x, y, clean_text, is_warn))

                if i == 0:
                    if last_main_idx is not None:
                        px, py, _, _ = nodes[last_main_idx]
                        arrows.append((px + BOX_W/2, py + BOX_H, x + BOX_W/2, y))
                    last_main_idx = idx
                else:
                    px, py, _, _ = nodes[last_row_idx]
                    arrows.append((px + BOX_W, py + BOX_H/2, x, y + BOX_H/2))

                last_row_idx = idx
                col += 1
        else:
            for text in parts:
                is_warn = text.endswith("!")
                clean_text = text.rstrip("!")
                px, py, _, _ = nodes[last_row_idx]
                x = px + BOX_W + GAP_X
                y = py
                idx = len(nodes)
                nodes.append((x, y, clean_text, is_warn))
                arrows.append((px + BOX_W, py + BOX_H/2, x, y + BOX_H/2))
                last_row_idx = idx

    if not nodes:
        return

    max_x = max(n[0] for n in nodes) + BOX_W + START_X
    max_y = max(n[1] for n in nodes) + BOX_H + START_Y

    svg_elements = []
    for x1, y1, x2, y2 in arrows:
        svg_elements.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="#64748b" stroke-width="2" marker-end="url(#arrowhead)" />'
        )

    for x, y, text, is_warn in nodes:
        fill = "#fef2f2" if is_warn else "#ffffff"
        stroke = "#ef4444" if is_warn else "#334155"
        text_color = "#991b1b" if is_warn else "#0f172a"
        svg_elements.append(f'''
        <g transform="translate({x}, {y})">
            <rect width="{BOX_W}" height="{BOX_H}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2" filter="url(#shadow)" />
            <text x="{BOX_W/2}" y="{BOX_H/2 + 5}" font-family="system-ui, sans-serif" font-size="14" 
                  font-weight="600" fill="{text_color}" text-anchor="middle">{text}</text>
        </g>''')

    html = f"""<!DOCTYPE html>
<html>
<head>
  <title>{title}</title>
  <style>
    body {{ margin: 0; background: #f1f5f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
    svg {{ background: white; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); }}
  </style>
</head>
<body>
  <svg width="{max_x}" height="{max_y}" xmlns="http://w3.org">
    <defs>
      <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />
      </marker>
      <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
        <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.08"/>
      </filter>
    </defs>
    {"".join(svg_elements)}
  </svg>
</body>
</html>"""

    # Save to system temp folder so it doesn't clutter your desktop
    fd, out_file = tempfile.mkstemp(suffix=".html", prefix="flow_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(html)
    webbrowser.open(f"file://{out_file}")

if __name__ == "__main__":
    # sys.argv[1] holds the path of the file you double-clicked
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        build_svg_flowchart(code, title=os.path.basename(file_path))
