# heading2diagram

**heading2diagram** is a command-line tool that converts a Markdown-like heading format into Mermaid or PlantUML diagram source.

- Japanese: [README_jp.md](README_jp.md)
- Heading-format grammar (Japanese): [docs/見出し形式文法.md](docs/見出し形式文法.md)
- Examples: [examples/README.md](examples/README.md)

## Version

`1.0.0`

## Requirements

- Python 3.10 or later
- No third-party Python packages; the program uses only the standard library

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
# 会議の準備
## 議題の確定
## 資料作成
### 前回議事録
### 実績データ
### 提案書
## 会場手配
### 日程調整
### 備品確認
```

Example:

```sh
python heading2diagram.py examples/example1.md -t hier-flow
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

When an input containing edge labels is requested as `hier-mind`, the program automatically generates `hier-mindlabel`.

## Per-element attributes

For hierarchy diagrams and `struct-flow`, the basic element syntax is:

```text
[|label|][lineType;][shape;]text[:#color]
```

Square brackets indicate optional parts and are not entered literally.

Example:

```text
|先方待ち|実線矢印;サブ;備品確認
```

See [docs/見出し形式文法.md](docs/見出し形式文法.md) for line types, shapes, colors, diagram-specific input conditions, and error-handling rules.

## Global options

- `--direction`: `TB`, `TD`, `BT`, `LR`, `RL`
- `--layout`: `tight`, `normal`, `spacyX`, `spacyY`, `spacyXY`, `spacyPadding`
- `--line`: `dotted`, `solid`, `thick`, `dottedArrow`, `solidArrow`, `thickArrow`
- `--arrowDirection`: `default`, `reverse`
- `--curve`: `default`, `linear`, `bumpX`, `bumpY`, `cardinal`, `catmullRom`, `monotoneX`, `monotoneY`, `natural`, `step`

Applicability depends on the selected diagram type; see the grammar document for details.

## Examples

The `examples/` directory contains seven input files and fourteen reference outputs. See [examples/README.md](examples/README.md) for exact reproduction commands.

## Tests

Run the regression tests with the standard library's `unittest` module:

```sh
python -m unittest discover -s tests -v
```

The current release has been checked so that all fourteen reference outputs in `examples/` exactly match the output of `heading2diagram.py`.

## License

This repository is prepared for release under the [MIT License](LICENSE).

## Citation

Citation metadata are provided in [`CITATION.cff`](CITATION.cff). 

After Zenodo issues a DOI, add the DOI to the README files and to `CITATION.cff` for the next release.
