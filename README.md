# .flow

A lightweight, text-based language for describing flowcharts. Write a `.flow` file in a text editor, then render it as a standalone HTML/SVG diagram with the Python runner.

## Features

- Plain-text flowchart definitions.
- Left-to-right chains using `->`.
- Indented branch continuations.
- Warning nodes marked with a trailing `!`.
- Comments beginning with `#`.
- Standalone HTML output that works in a modern browser.
- No third-party Python packages required.

## Requirements

- Python 3.10 or newer.
- A modern web browser to view the generated chart.

## Run

```bash
python flow_runner.py path/to/example.flow
```

The chart opens in your default browser. To save the HTML to a known location without opening it:

```bash
python flow_runner.py path/to/example.flow --output build/example.html --no-open
```

On Windows, you can also use the packaged `dist/flow_runner.exe` if you prefer not to install Python. The executable is a prebuilt release artifact and may not include the latest source changes; rebuild it after updating the source (see below).

## Syntax

An unindented line starts a new row. Separate nodes on the same row with `->`:

```flow
Power source -> Circuit breaker -> Controller
```

A new unindented line starts the next main row and connects vertically from the previous main row:

```flow
Power source
Circuit breaker
Controller
```

An indented line continues a branch horizontally from the most recently created node. You can chain multiple nodes on a branch:

```flow
Power source
    120V AC input -> Circuit breaker
        Controller
    Backup supply
```

Mark a warning node with `!` at the end of its label:

```flow
Thin wire -> Excess current! -> Overheating!
```

Use `#` for comments and blank lines for spacing:

```flow
# Main power path
Battery -> Fuse -> Load

# This is a separate row
Status indicator
```

### Syntax rules

- Node labels cannot be empty.
- Every `->` must have a node label on both sides.
- A branch must be indented and must follow an existing node.
- `->` is a reserved separator and cannot currently appear inside a label.
- `!` is treated as a warning marker only when it appears at the end of a label.

## Development

Run the test suite with the Python standard library:

```bash
python -m unittest discover -s tests -v
```

Build the Windows executable from the repository root (requires PyInstaller):

```bash
python -m pip install pyinstaller
pyinstaller --clean flow_runner.spec
```

The generated executable is placed in `dist/`.

## Project status

Early prototype. The language and layout rules may evolve. See the tests for the currently supported parsing and rendering behaviour.

## Licence

This project is distributed under the GNU General Public License v3.0. See [LICENSE](LICENSE).
