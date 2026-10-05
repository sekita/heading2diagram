# Heading Format Syntax

## 1. Heading Format

The heading format is a text notation that represents a hierarchical structure by the number of `#` characters written at the beginning of a line [2]. Increasing the number of `#` characters by one represents a child element of the parent element, while elements with the same number of `#` characters represent sibling elements at the same hierarchy level.

The types of diagrams that can be generated from the heading format are shown in **Table 1**, organized by the type of information to be represented. The diagram type ID is specified using the `-t` command-line option.

**Table 1. Quick Reference for the Heading Format**

| **What You Want to Represent** | **Diagram Type ID** | **Input Overview** |
|---|---|---|
| Represent a hierarchy or classification as a mind map | hier-mind | Use a single first-level element, and describe lower levels by increasing the number of `#` characters. See Table 2 for attribute specifications. |
| Represent a hierarchy or classification as a flowchart | hier-flow | Use a single first-level element, and describe lower levels by increasing the number of `#` characters. See Table 2 for attribute specifications. |
| Represent a hierarchy or classification in a grid layout | hier-block | Use a single first-level element, and describe lower levels by increasing the number of `#` characters. See Table 2 for attribute specifications. |
| Represent a mind map with labels on connecting lines | hier-mindlabel | Use the same format as `hier-mind` and specify labels for the connecting lines. This type is automatically selected for a mind map containing labels. |
| Represent a procedure or flow | struct-flow | Multiple first-level elements may be specified. Increasing the number of `#` characters creates a lower level, and elements at the same level are connected in the order in which they are written. See Table 2 for attribute specifications. |
| Represent causal relationships as a fishbone diagram | fishBone | Describe the result at the first level, major categories of causes at the second level, and individual causes at the third and subsequent levels. |
| Represent proportions or breakdowns as a pie chart | pie | Use the first level as the title and describe second-level elements in the form `element name:value`. To specify a color, append `:#color` to the end. |
| Represent sets and their intersections as a Venn diagram | venn | Describe sets at the first level, intersections of two sets at the second level, and intersections of three sets at the third level. The corresponding sets are determined by their order of appearance. |
| Represent information consisting of rows and columns. Make the header row and column N bold. `c` centers the elements. | table, tableN, tablec, tableNc | Each first-level element becomes the first column of a row, and the following second-level elements become the second and subsequent columns. Specify `1`, `2`, or `3` for N. |
| Represent four quadrants based on two perspectives | quadrant | Specify two first-level elements representing the left and right sides of the horizontal axis. Under each, specify two second-level elements representing the lower and upper parts of the vertical axis. Each quadrant may contain up to nine third-level elements: the first is the quadrant heading, and up to eight subsequent elements are items within the quadrant. |

## 2. Attribute Specifications for Individual Elements

In `hier-mind`, `hier-flow`, `hier-block`, and `struct-flow`, attributes can be added to individual elements to specify the frame shape, labels on connecting lines, connecting-line type, and fill color (**Table 2**). These element-level specifications take precedence over the diagram-wide specifications in Table 3. In the following sections, the first three diagram types are collectively referred to as `hier-*`. This is only a collective term used for explanation and does not mean that `hier-*` can be specified as a diagram type ID.

Excluding the leading `#` characters used to indicate the hierarchy level, the basic format is as follows:

```text
[|label|][lineType;][shape;]text[:#color]
```

Here, square brackets `[]` are explanatory notation indicating that the enclosed item is optional; they are not written in the actual input. All four attributes may be omitted. If omitted, the default appearance is used: no label, a solid line, a rectangular frame, and the color defined by the execution environment.

`text` is the element name and must not be omitted. For example:

```text
|Waiting for response|solidArrow;fr-rect;Check equipment
```

This assigns the label `Waiting for response` to the line connecting to `Check equipment`, uses a solid arrow, and sets the frame shape to `fr-rect`.

### Connecting-Line Types

The following specifications can be used for connecting lines. The terms in parentheses are the English identifiers.

- Solid line (`solid`)
- Dotted line (`dotted`)
- Thick line (`thick`)
- Solid arrow (`solidArrow`)
- Dotted arrow (`dottedArrow`)
- Thick arrow (`thickArrow`)

For `hier-mind`, line types containing arrows must not be used.

### Frame Shapes

The following specifications can be used for frame shapes. The terms in parentheses are the English identifiers.

- Rectangle (`rect`)
- Rounded rectangle (`rounded`)
- Stadium (`stadium`)
- Subroutine rectangle (`fr-rect`)
- Cylinder (`cyl`)
- Circle (`circle`)
- Asymmetric shape (`odd`)
- Diamond (`diam`)
- Hexagon (`hex`)
- Right-leaning parallelogram (`lean-r`)
- Left-leaning parallelogram (`lean-l`)
- Trapezoid (`trap-b`)
- Inverted trapezoid (`trap-t`)
- Double circle (`dbl-circ`)
- Borderless (`borderless`)

`Right-leaning parallelogram` and `Left-leaning parallelogram` indicate shapes whose vertical sides are inclined to the right and left, respectively.

For `hier-mind`, the default frame shape is a rectangle, and only `rounded` and `borderless` may be specified as alternative frame shapes.

### Color

Colors are specified as three- or six-digit hexadecimal RGB values prefixed with `#`.

Examples:

```text
:#f88
:#ff8888
```

If a label is specified on a connecting line in `hier-mind`, `hier-mindlabel` is automatically used.

**Table 2. Attribute Values for hier-mind, hier-flow, hier-block, and struct-flow**

| **Attribute** | **Position / Format** | **Description** |
|---|---|---|
| Label on connecting line | `|label|` | A string displayed on the connecting line from the parent element to the current element |
| Connecting-line type | `lineType;` | The type of connecting line leading to the current element. Arrows are not permitted in `hier-mind`. |
| Frame shape | `shape;` | The shape of the frame surrounding the current element. Not applicable to `hier-mind`. |
| Fill color | `:#color` | The color inside the frame of the current element |

## 3. Command-Line Options for the Entire Diagram

For `hier-*` and `struct-flow`, options can be added to the execution command shown in Section 4.1 to change the overall diagram direction, connecting lines, spacing, and other settings. The available options can also be checked using the following command:

```sh
python heading2diagram.py -h
```

The values available for each option are shown in **Table 3**. For each option, the first value listed is the default.

**Table 3. Command-Line Options for the Entire Diagram  
(Options that do not apply to the selected diagram type are ignored. The first value is the default.)**

| **Option** | **Applicable Diagram Types** | **Values** | **Meaning** |
|---|---|---|---|
| `--direction` | hier-* | TB (TD), LR, RL, BT | Specifies the direction in which the hierarchy expands. |
| `--line` | hier-*, struct-flow | solid, dotted, thick, solidArrow, dottedArrow, thickArrow | Specifies the default connecting-line type used throughout the diagram. |
| `--layout` | hier-*, struct-flow | normal, tight, spacyX, spacyY, spacyXY, spacyPadding | Specifies spacing and margins between elements. `spacyPadding` increases the padding between the frame and the element name. |
| `--arrowDirection` | hier-flow, hier-block, struct-flow | default, reverse | Specifies the direction of arrows when arrows are used. `reverse` reverses the default direction. |
| `--curve` | hier-flow | default, linear, bumpX, bumpY, step, cardinal, catmullRom, monotoneX, monotoneY, natural | Specifies the type of curve used for connecting lines. See the Mermaid documentation for details. |

## 4. Design Policy for Input Errors

The heading format is designed to continue processing as far as possible even when part of the input contains errors, so that problematic portions can still be identified and reviewed as text. Therefore, the following policies are adopted for input errors.

### (1) Continue Processing

For lines that cannot be interpreted as headings, empty lines, or specifications that do not conform to the required format, a warning is issued and the relevant portion is ignored. Processing then continues as far as possible.

### (2) Recovery from Local Errors

If a hierarchy level is skipped—for example, if `###` appears immediately after `#`—the relevant line is treated as a child element of the preceding line, and a warning is issued. In this way, a local input error does not immediately cause the entire generation process to fail.

### (3) Identification of Problematic Locations

Warnings and errors are written to standard error as single-line text messages containing the line number. Each message uses a short format beginning with `warning` or `error:`, making sequential review with a screen reader easier.

If `-t` is not specified, the required input conditions for each diagram type (**Table 1**) are evaluated individually. If the input does not satisfy the conditions for a particular diagram type, generation of only that type is skipped, while generation continues for other types whose conditions are satisfied.

On the other hand, if a diagram type is explicitly specified using `-t` and the input does not satisfy the conditions required for that type, the unmet conditions are reported as errors and processing terminates.
