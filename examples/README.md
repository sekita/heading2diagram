# Examples

This directory contains English input examples and reference outputs for `heading2diagram`. All of them use English text, English line-type identifiers, and English frame-shape identifiers.

[Back to the main README](../README.md)

The following commands assume that the current directory is `examples/`.

## Example 1 — Basic hierarchy

Input: `example1_en.md`

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

```sh
python ../heading2diagram.py example1_en.md -t hier-block -o out1_en_hier-block.md
python ../heading2diagram.py example1_en.md -t hier-flow -o out1_en_hier-flow.md
python ../heading2diagram.py example1_en.md -t hier-mind -o out1_en_hier-mind.md
python ../heading2diagram.py example1_en.md -t struct-flow --layout tight -o out1_en_struct-flow_tight.md
```

| Output | Type | Main settings |
|---|---|---|
| `out1_en_hier-block.md` | `hier-block` | Default |
| `out1_en_hier-flow.md` | `hier-flow` | Default |
| `out1_en_hier-mind.md` | `hier-mind` | Default |
| `out1_en_struct-flow_tight.md` | `struct-flow` | `--layout tight` |

## Example 2 — Shapes, colors, and edge labels

Input: `example2_en.md`

```text
# fr-rect;Meeting preparation
## Finalize agenda
## stadium;Prepare materials:#FAF
### Previous minutes
### Performance data
### Proposal
## hex;Arrange venue:#0FF
### |Attendees confirmed|solidArrow;lean-r;Schedule
### |Venue confirmed|solidArrow;Check equipment
```

```sh
python ../heading2diagram.py example2_en.md -t hier-block --direction LR --layout tight -o out2_en_hier-block_LR_tight.md
python ../heading2diagram.py example2_en.md -t hier-flow --direction LR -o out2_en_hier-flow_LR.md
python ../heading2diagram.py example2_en.md -t hier-mindlabel --direction LR -o out2_en_hier-mindlabel_LR.md
python ../heading2diagram.py example2_en.md -t struct-flow --layout tight -o out2_en_struct-flow_tight.md
```

| Output | Type | Main settings |
|---|---|---|
| `out2_en_hier-block_LR_tight.md` | `hier-block` | `--direction LR --layout tight` |
| `out2_en_hier-flow_LR.md` | `hier-flow` | `--direction LR` |
| `out2_en_hier-mindlabel_LR.md` | `hier-mindlabel` | `--direction LR` |
| `out2_en_struct-flow_tight.md` | `struct-flow` | `--layout tight` |

`hier-mindlabel` cannot express frame shapes or per-element line types, so a warning is written to standard error for this output. The other attributes are reflected as usual.

## Example 3 — Fishbone and reversed hierarchy

Input: `example3_en.md`

```sh
python ../heading2diagram.py example3_en.md -t fishBone -o out3_en_fishBone.md
python ../heading2diagram.py example3_en.md -t hier-flow --direction RL --line thickArrow --arrowDirection reverse -o out3_en_hier-flow_RL_thickArrow_arrowReverse.md
```

## Example 4 — Venn diagram

Input: `example4_en.md`

```sh
python ../heading2diagram.py example4_en.md -t venn -o out4_en_venn.md
```

## Example 5 — Table

Input: `example5_en.md`

```sh
python ../heading2diagram.py example5_en.md -t table1c -o out5_en_table1c.md
```

## Example 6 — Quadrant chart

Input: `example6_en.md`

```sh
python ../heading2diagram.py example6_en.md -t quadrant -o out6_en_quadrant.md
```

## Example 7 — Pie chart

Input: `example7_en.md`

Each item can be written in the form `item name:value:#color`.

```text
# Breakdown of working time
## Prepare materials:60:#aff
## Arrange venue:40:#afa
## Schedule:30:#ffa
## Finalize agenda:15:#faa
```

```sh
python ../heading2diagram.py example7_en.md -t pie -o out7_en_pie.md
```

## Example 8 — Star diagram

Input: `example8_en.md`

The first-level element is the center. The second-level elements are placed clockwise around it, starting directly above, in the order in which they are written.

```text
# circle;Meeting preparation:#ffd
## Finalize agenda
## |Previous minutes|solidArrow;Prepare materials
## |Attendees confirmed|solidArrow;fr-rect;Arrange venue:#0FF
## |Venue confirmed|dottedArrow;Schedule
## rounded;Check equipment
```

```sh
python ../heading2diagram.py example8_en.md -t star -o out8_en_star.md
python ../heading2diagram.py example8_en.md -t star --degree 30 --line dotted -o out8_en_star_degree30_dotted.md
```

| Output | Type | Main settings |
|---|---|---|
| `out8_en_star.md` | `star` | Default |
| `out8_en_star_degree30_dotted.md` | `star` | `--degree 30 --line dotted` |

`--degree 30` rotates the whole arrangement 30 degrees clockwise. `--line dotted` changes the default line type; the line types written on individual elements take precedence.

## Regression check

From the repository root, run:

```sh
python -m unittest discover -s tests -v
```

The tests regenerate all reference outputs and compare them exactly with the `out*.md` files in this directory.
