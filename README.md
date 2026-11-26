# .flow

A small, readable language for describing flowcharts. Write a `.flow` file, then render it as a standalone HTML/SVG diagram.

## Quick start

```flow
start: Power on
process: Check the fuse
decision: Is the fuse intact?
  yes: Start controller
  no: Replace fuse!
end: System ready
```

Run it:

```bash
python flow_runner.py example.flow
```

The Windows build is available as `dist/flow_runner.exe`. No third-party Python packages are needed to run the source version. Python 3.10+ is required.

## Language guide

### Node declarations

Every line creates a node. The type is optional; an untyped node is a `process`.

| Syntax | Meaning | Appearance |
|---|---|---|
| `start: Label` | Entry point | Green rounded capsule |
| `process: Label` | Action or operation | Standard rectangle |
| `decision: Question?` | Yes/no decision | Diamond |
| `input: Label` | Input data | Purple parallelogram |
| `output: Label` | Output data | Purple parallelogram |
| `warning: Label` | Warning or fault | Red rectangle |
| `end: Label` | Exit point | Blue rounded capsule |

The type is followed by a colon and a label. Labels can contain spaces and punctuation. A trailing `!` also marks a warning.

### Connections and branches

Unindented lines form the main path, top to bottom:

```flow
start: Boot
process: Load configuration
process: Start service
end: Ready
```

Indent a branch under its parent node. Decision branches can be labelled `yes`, `no`, `true`, or `false`:

```flow
start: Read sensor
decision: Temperature safe?
  yes: Continue operation
  no: warning: Shut down system!
end: Monitoring complete
```

For compact diagrams, connect nodes on one line with `->`:

```flow
start: Battery -> process: Fuse -> output: Motor
```

### Comments

Lines beginning with `#` and blank lines are ignored.

```flow
# Main power path
start: Battery
process: Check voltage

# This is a separate section
end: Complete
```

## Syntax rules

- Node labels cannot be empty.
- A branch must be indented and must follow an existing node.
- `->` separates nodes on the same line and cannot appear inside a label.
- Node types are `start`, `process`, `decision`, `input`, `output`, `warning`, and `end`.
- Untyped labels remain supported as ordinary process nodes, so older files continue to work.

## Command line

```bash
python flow_runner.py path/to/example.flow
python flow_runner.py path/to/example.flow --output build/example.html --no-open
```

## Development and executable build

Run tests:

```bash
python -m unittest discover -s tests -v
```

Build the Windows executable:

```bash
python -m pip install pyinstaller
pyinstaller --clean flow_runner.spec
```

The executable is written to `dist/flow_runner.exe`.

## Licence

GNU General Public License v3.0. See [LICENSE](LICENSE).


## Examples

Runnable examples are in [examples/](examples/):

- [Startup demo](examples/startup-demo.flow)
- [Helpdesk demo](examples/helpdesk-demo.flow)

Run one with:

```powershell
.\\flow_runner.exe .\\examples\\startup-demo.flow
```

## Installing and verifying releases

Download prebuilt Windows packages from the [GitHub Releases](https://github.com/The-Graphite-Team/.flow/releases) page.

- [Windows installation guide](INSTALL.md)
- [Release verification guide](VERIFYING.md)

The release workflow publishes the executable, example files, SHA-256 checksums, and GitHub build provenance attestation. Releases are not Authenticode-signed yet, so Windows may still show an unknown-publisher warning.
