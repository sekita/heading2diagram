# Examples

This directory contains input examples and reference outputs for `heading2diagram`.

[Back to the main README](../README.md)

The following commands assume that the current directory is `examples/`.

## Example 1 — Basic hierarchy

```sh
python ../heading2diagram.py example1.md -t hier-block -o out1_hier-block.md
python ../heading2diagram.py example1.md -t hier-flow -o out1_hier-flow.md
python ../heading2diagram.py example1.md -t hier-mind -o out1_hier-mind.md
python ../heading2diagram.py example1.md -t struct-flow --layout tight -o out1_struct-flow_tight.md
```

## Example 2 — Shapes, colors, and edge labels

```sh
python ../heading2diagram.py example2.md -t hier-block --direction LR --layout tight -o out2_hier-block_LR_tight.md
python ../heading2diagram.py example2.md -t hier-flow --direction LR -o out2_hier-flow_LR.md
python ../heading2diagram.py example2.md -t hier-mindlabel --direction LR -o out2_hier-mindlabel_LR.md
python ../heading2diagram.py example2.md -t struct-flow --layout tight -o out2_struct-flow_tight.md
```

## Example 3 — Fishbone and reversed hierarchy

```sh
python ../heading2diagram.py example3.md -t fishBone -o out3_fishBone.md
python ../heading2diagram.py example3.md -t hier-flow --direction RL --line thickArrow --arrowDirection reverse -o out3_hier-flow_RL_thickArrow_arrowReverse.md
```

## Example 4 — Venn diagram

```sh
python ../heading2diagram.py example4.md -t venn -o out4_venn.md
```

## Example 5 — Table

```sh
python ../heading2diagram.py example5.md -t table1c -o out5_table1c.md
```

## Example 6 — Quadrant chart

```sh
python ../heading2diagram.py example6.md -t quadrant -o out6_quadrant.md
```

## Example 7 — Pie chart

```sh
python ../heading2diagram.py example7.md -t pie -o out7_pie.md
```

## Regression check

From the repository root, run:

```sh
python -m unittest discover -s tests -v
```

The tests regenerate all fourteen reference outputs and compare them exactly with the `out*.md` files in this directory.
