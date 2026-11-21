# heading2diagram

**heading2diagram** is a command-line tool that converts a Markdown-like heading format into Mermaid or PlantUML diagram source.

- Japanese: [README_jp.md](README_jp.md)
- Heading-format grammar: [docs/headingBasedFormatSyntax.md](docs/headingBasedFormatSyntax.md)
- Examples: [examples/README.md](examples/README.md)

## Version

`1.1.0`

## Requirements

- Python 3.10 or later
- No third-party Python packages; the program uses only the standard library

To view the diagrams themselves, display the generated code with a Mermaid or PlantUML renderer.

## Usage

```sh
python heading2diagram.py INPUT.md
```

Select one or more diagram types with `-t` / `--type`:

```sh
python heading2diagram.py INPUT.md -t hier-flow
python heading2diagram.py INPUT.md -t hier-mind hier-block hier-flow
```

Write the result to a file with `-o` / `--output`:

```sh
python heading2diagram.py INPUT.md -t hier-flow -o output.md
```

Show all command-line options:

```sh
python heading2diagram.py -h
```

If `-t` is omitted, the program checks the input conditions for supported diagram types and generates the compatible ones. If a type is explicitly requested with `-t` and its input conditions are not met, the program exits with an error.

## Heading format

Hierarchy is represented by the number of `#` characters at the beginning of a line. An additional `#` denotes a child element, while headings with the same number of `#` characters are siblings.

```text
# Meeting preparation
## Finalize agenda
## Prepare materials
### Previous minutes
### Performance data
### Proposal
## Arrange venue
### Schedule
### Check equipment
```

Example:

```sh
python heading2diagram.py examples/example1_en.md -t hier-flow
```

## Diagram types

| Purpose | Type ID |
|---|---|
| Hierarchy/classification mind map | `hier-mind` |
| Mind map with edge labels | `hier-mindlabel` |
| Grid/block hierarchy | `hier-block` |
| Hierarchy/classification flowchart | `hier-flow` |
| Fishbone / cause-and-effect diagram | `fishBone` |
| Pie chart | `pie` |
| Venn diagram | `venn` |
| Table | `table`, `tablec`, `table1`, `table1c`, `table2`, `table2c`, `table3`, `table3c` |
| Procedure / structural flow | `struct-flow` |
| Quadrant chart | `quadrant` |
| Radial (star) diagram: a central element and its surrounding elements | `star` |

When an input containing edge labels is requested as `hier-mind`, the program automatically generates `hier-mindlabel`.

### Star diagram (`star`)

`star` is new in version 1.1.0. Write the central element at the first level and the surrounding elements at the second level. The surrounding elements are placed clockwise around the center, starting directly above it, in the order in which they are written.

```text
# circle;Meeting preparation:#ffd
## Finalize agenda
## |Previous minutes|solidArrow;Prepare materials
## |Attendees confirmed|solidArrow;fr-rect;Arrange venue:#0FF
## |Venue confirmed|dottedArrow;Schedule
## rounded;Check equipment
```

```sh
python heading2diagram.py examples/example8_en.md -t star
python heading2diagram.py examples/example8_en.md -t star --degree 30 --line dotted
```

## Per-element attributes

For hierarchy diagrams, `struct-flow`, and `star`, the basic element syntax is:

```text
[|label|][lineType;][shape;]text[:#color]
```

Square brackets indicate optional parts and are not entered literally.

Example:

```text
|Waiting for response|solidArrow;fr-rect;Check equipment
```

This assigns the label `Waiting for response` to the line leading to `Check equipment`, draws that line as a solid arrow, and uses the `fr-rect` frame shape.

### Line types

`solid`, `dotted`, `thick`, `solidArrow`, `dottedArrow`, `thickArrow`

### Frame shapes

| Identifier | Shape |
|---|---|
| `rect` | Rectangle |
| `rounded` | Rounded rectangle |
| `stadium` | Stadium |
| `fr-rect` | Subroutine rectangle |
| `cyl` | Cylinder |
| `circle` | Circle |
| `odd` | Asymmetric shape |
| `diam` | Diamond |
| `hex` | Hexagon |
| `lean-r` | Right-leaning parallelogram |
| `lean-l` | Left-leaning parallelogram |
| `trap-b` | Trapezoid |
| `trap-t` | Inverted trapezoid |
| `dbl-circ` | Double circle |
| `borderless` | Borderless |

In `hier-mind`, only `rounded` and `borderless` can be expressed as alternative frame shapes.

### Color

Colors are three- or six-digit hexadecimal RGB values prefixed with `#`, such as `:#f88` or `:#ff8888`.

See [docs/headingBasedFormatSyntax.md](docs/headingBasedFormatSyntax.md) for diagram-specific input conditions and error-handling rules.

## Global options

| Option | Main diagram types | Values |
|---|---|---|
| `--direction` | `hier-*` | `TB`, `TD`, `BT`, `LR`, `RL` |
| `--layout` | `hier-*`, `struct-flow`, `star` | `tight`, `normal`, `spacyX`, `spacyY`, `spacyXY`, `spacyPadding` |
| `--line` | `hier-*`, `struct-flow`, `star` | `dotted`, `solid`, `thick`, `dottedArrow`, `solidArrow`, `thickArrow` |
| `--arrowDirection` | `hier-flow`, `hier-block`, `star` | `default`, `reverse` |
| `--curve` | `hier-flow` | `default`, `linear`, `bumpX`, `bumpY`, `cardinal`, `catmullRom`, `monotoneX`, `monotoneY`, `natural`, `step` |
| `--degree` | `star` | Angle of the first surrounding element in degrees (default `0` = directly above, clockwise) |
| `--span` | `star` | Number of grid columns per block, an integer of 1 or more (default `4`) |
| `--radius` | `star` | Distance from the center in estimated pixels (default: chosen automatically) |
| `--blockWidth` | `star` | Block width for the layout calculation in estimated pixels (default: widest block) |

Here `hier-*` is a collective term for `hier-mind`, `hier-mindlabel`, `hier-block`, and `hier-flow`, not an actual type ID. See the grammar document for details.

## Examples

The `examples/` directory contains eight English input files (`example1_en.md` to `example8_en.md`) and sixteen reference outputs (`out*_en_*.md`).

```text
examples/
├── example1_en.md  # Basic hierarchy
├── example2_en.md  # Shapes, colors, and edge labels
├── example3_en.md  # Fishbone / reversed hierarchy
├── example4_en.md  # Venn diagram
├── example5_en.md  # Table
├── example6_en.md  # Quadrant chart
├── example7_en.md  # Pie chart
└── example8_en.md  # Star diagram
```

See [examples/README.md](examples/README.md) for exact reproduction commands.

## Tests

Run the regression tests with the standard library's `unittest` module:

```sh
python -m unittest discover -s tests -v
```

The current release has been checked so that all reference outputs in `examples/` exactly match the output of `heading2diagram.py`.

## License

This repository is prepared for release under the [MIT License](LICENSE).

## Citation

Citation metadata are provided in [`CITATION.cff`](CITATION.cff).
