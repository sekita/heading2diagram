#!/usr/bin/env python3
"""heading2diagram: 見出し形式Markdownからダイアグラム定義（PlantUML / Mermaid）を生成する。

仕様書: heading2diagram_spec261004.md
標準ライブラリのみを使用する（Python 3.10以上）。
"""

import argparse
import re
import sys
import unicodedata

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

ALL_TYPES = [
    "hier-mind", "hier-mindlabel", "hier-block", "hier-flow", "fishBone",
    "pie", "venn",
    "table", "tablec", "table1", "table1c", "table2", "table2c", "table3", "table3c",
    "struct-flow", "quadrant",
]
TABLE_TYPES = {"table", "tablec", "table1", "table1c", "table2", "table2c", "table3", "table3c"}

DIRECTION_CHOICES = ["TB", "TD", "BT", "LR", "RL"]
LAYOUT_CHOICES = ["tight", "normal", "spacyX", "spacyY", "spacyXY", "spacyPadding"]
LINE_CHOICES = ["dotted", "solid", "thick", "dottedArrow", "solidArrow", "thickArrow"]
ARROW_DIRECTION_CHOICES = ["default", "reverse"]
CURVE_CHOICES = ["default", "linear", "bumpX", "bumpY", "cardinal", "catmullRom",
                 "monotoneX", "monotoneY", "natural", "step"]

LINE_TYPE_NAMES = {
    "実線": "solid", "solid": "solid",
    "点線": "dotted", "dotted": "dotted",
    "太線": "thick", "thick": "thick",
    "実線矢印": "solidArrow", "solidArrow": "solidArrow",
    "点線矢印": "dottedArrow", "dottedArrow": "dottedArrow",
    "太線矢印": "thickArrow", "thickArrow": "thickArrow",
}

SHAPE_NAMES = {
    "四角": "rect", "rect": "rect",
    "角丸": "rounded", "rounded": "rounded",
    "スタ": "stadium", "stadium": "stadium",
    "サブ": "fr-rect", "fr-rect": "fr-rect",
    "円柱": "cyl", "cyl": "cyl",
    "円形": "circle", "circle": "circle",
    "非対": "odd", "odd": "odd",
    "ひし": "diam", "diam": "diam",
    "六角": "hex", "hex": "hex",
    "四右": "lean-r", "lean-r": "lean-r",
    "四左": "lean-l", "lean-l": "lean-l",
    "台形": "trap-b", "trap-b": "trap-b",
    "逆台": "trap-t", "trap-t": "trap-t",
    "重円": "dbl-circ", "dbl-circ": "dbl-circ",
    "無枠": "borderless", "borderless": "borderless",
}

# Mermaid のノード書式（前置部, 後置部）。テキストは "..." で囲まれる。
SHAPE_FORMATS = {
    "rect": ('["', '"]'),
    "rounded": ('("', '")'),
    "stadium": ('(["', '"])'),
    "fr-rect": ('[["', '"]]'),
    "cyl": ('[("', '")]'),
    "circle": ('(("', '"))'),
    "odd": ('>"', '"]'),
    "diam": ('{"', '"}'),
    "hex": ('{{"', '"}}'),
    "lean-r": ('[/"', '"/]'),
    "lean-l": ('[\\"', '"\\]'),
    "trap-b": ('[/"', '"\\]'),
    "trap-t": ('[\\"', '"/]'),
    "dbl-circ": ('((("', '")))'),
    "borderless": ('["', '"]'),
}

FLOW_SYMBOLS = {
    "solid": "---", "dotted": "-.-", "thick": "===",
    "solidArrow": "-->", "dottedArrow": "-.->", "thickArrow": "==>",
}
BLOCK_SYMBOLS = {
    "solid": "---", "dotted": "-.-", "thick": "===",
    "solidArrow": "--->", "dottedArrow": "-.->", "thickArrow": "===>",
}
BLOCK_REVERSE_SYMBOLS = {
    "solid": "---", "dotted": "-.-", "thick": "===",
    "solidArrow": "<---", "dottedArrow": "<-.-", "thickArrow": "<===",
}
REVERSE_DIRECTION = {"TB": "BT", "TD": "BT", "BT": "TB", "LR": "RL", "RL": "LR"}

# 見出しに含めるオプション（図種ごと、この順）
HEADING_OPTIONS = {
    "hier-mind": ["direction", "layout", "line"],
    "hier-mindlabel": ["direction", "layout", "line"],
    "hier-block": ["direction", "layout", "line", "arrowDirection"],
    "hier-flow": ["direction", "layout", "line", "arrowDirection", "curve"],
    "struct-flow": ["layout", "line"],
}

HEADING_RE = re.compile(r"^(#+)[ \t]+(.*)$")
HEADING_EMPTY_RE = re.compile(r"^#+[ \t]+$")
HEADING_TYPO_RE = re.compile(r"^#+[^ \t#]")
COLOR_RE = re.compile(r":#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$")
BAD_COLOR_RE = re.compile(r":#\S*$")
MODIFIER_RE = re.compile(r"^([^ \t;]*);")
NUMBER_RE = re.compile(r"[0-9]+(\.[0-9]+)?")
WHITESPACE = " \t"


# ---------------------------------------------------------------------------
# 警告・エラー
# ---------------------------------------------------------------------------

def warn(message, lineNo=None):
    if lineNo is None:
        sys.stderr.write(f"warning: {message}\n")
    else:
        sys.stderr.write(f"warning: line {lineNo}: {message}\n")


def errorExit(message, lineNo=None):
    if lineNo is None:
        sys.stderr.write(f"error: {message}\n")
    else:
        sys.stderr.write(f"error: line {lineNo}: {message}\n")
    sys.exit(1)


# ---------------------------------------------------------------------------
# 入力解析
# ---------------------------------------------------------------------------

class Node:
    """見出し1行に対応する節。"""

    def __init__(self, label, lineType, shape, text, color, level, lineNo):
        self.label = label          # 線上ラベル（無ければ None）
        self.lineType = lineType    # 線種（英語名、無ければ None）
        self.shape = shape          # 形状（英語名、無ければ None）
        self.text = text            # テキスト
        self.color = color          # 色（# を除いた16進文字列、無ければ None）
        self.level = level          # 実効レベル（1始まり）
        self.lineNo = lineNo        # 入力の行番号
        self.children = []
        self.parent = None
        self.nodeId = ""

    @property
    def isBorderless(self):
        return self.shape == "borderless"

    @property
    def isRounded(self):
        return self.shape == "rounded"


def parseContent(content, lineNo):
    """見出し行の内容を解析する。テキストが空なら None を返す。"""
    label = None
    rest = content

    # 1. ラベル
    if rest.startswith("|"):
        closeIndex = rest.find("|", 1)
        if closeIndex < 0:
            warn("ラベルの閉じる '|' が無いため、先頭の '|' を含めて内容全体をテキストとして扱う", lineNo)
        else:
            labelText = rest[1:closeIndex].strip(WHITESPACE)
            rest = rest[closeIndex + 1:]
            if labelText == "":
                warn("ラベルが空（||）のため、ラベル無しとして扱う", lineNo)
            else:
                label = labelText
    rest = rest.strip(WHITESPACE)

    # 2. 色
    color = None
    colorMatch = COLOR_RE.search(rest)
    if colorMatch:
        color = colorMatch.group(1)
        rest = rest[:colorMatch.start()]
    elif BAD_COLOR_RE.search(rest):
        warn("':#' の後が16進3桁または6桁でないため、色の書き間違いの可能性がある"
             "（':#' 以降はテキストの一部として扱う）", lineNo)
    rest = rest.lstrip(WHITESPACE)

    # 3. 修飾（線種名・形状名）
    lineType = None
    shape = None
    for _ in range(2):
        modifierMatch = MODIFIER_RE.match(rest)
        if not modifierMatch:
            break
        name = modifierMatch.group(1)
        if name in LINE_TYPE_NAMES:
            if lineType is not None:
                warn(f"線種名 '{name};' が重複しているため、テキストの一部として扱う", lineNo)
                break
            lineType = LINE_TYPE_NAMES[name]
        elif name in SHAPE_NAMES:
            if shape is not None:
                warn(f"形状名 '{name};' が重複しているため、テキストの一部として扱う", lineNo)
                break
            shape = SHAPE_NAMES[name]
        else:
            warn(f"'{name};' は既知の線種名・形状名ではないため、テキストの一部として扱う"
                 "（書き間違いの可能性がある）", lineNo)
            break
        rest = rest[modifierMatch.end():].lstrip(WHITESPACE)

    # 4. テキスト
    text = rest.strip(WHITESPACE)
    if text == "":
        warn("解析後のテキストが空のため、この行を無視する", lineNo)
        return None
    return {"label": label, "lineType": lineType, "shape": shape, "text": text, "color": color}


def assignNodeIds(roots):
    def assign(node, nodeId):
        node.nodeId = nodeId
        for index, child in enumerate(node.children, start=1):
            assign(child, f"{nodeId}_{index}")

    for index, root in enumerate(roots, start=1):
        assign(root, f"N{index}")


def parseInput(sourceText):
    """入力テキストを木構造へ変換し、ルートのリストを返す。"""
    roots = []
    stack = []
    prevLevel = 0
    for lineNo, rawLine in enumerate(sourceText.split("\n"), start=1):
        line = rawLine.rstrip("\r")
        if line.strip(WHITESPACE) == "":
            continue
        headingMatch = HEADING_RE.match(line)
        if not headingMatch:
            if HEADING_EMPTY_RE.match(line):
                warn("内容が空の見出し行を無視する", lineNo)
            elif HEADING_TYPO_RE.match(line):
                warn("'#' の直後に空白が無いため無視する（見出し行の書き間違いの可能性がある）", lineNo)
            else:
                warn("見出し行でも空行でもない行を無視する", lineNo)
            continue
        content = headingMatch.group(2)
        if content.strip(WHITESPACE) == "":
            warn("内容が空の見出し行を無視する", lineNo)
            continue
        parsed = parseContent(content, lineNo)
        if parsed is None:
            continue
        level = len(headingMatch.group(1))
        if level > prevLevel + 1:
            warn(f"レベル飛び（レベル{prevLevel} の次にレベル{level}）のため、"
                 f"実効レベル{prevLevel + 1} として扱う", lineNo)
            level = prevLevel + 1
        node = Node(parsed["label"], parsed["lineType"], parsed["shape"],
                    parsed["text"], parsed["color"], level, lineNo)
        if level == 1:
            roots.append(node)
        else:
            parent = stack[level - 2]
            node.parent = parent
            parent.children.append(node)
        stack = stack[:level - 1] + [node]
        prevLevel = level
    assignNodeIds(roots)
    return roots


# ---------------------------------------------------------------------------
# 木の走査
# ---------------------------------------------------------------------------

def preorder(roots):
    result = []

    def visit(node):
        result.append(node)
        for child in node.children:
            visit(child)

    for root in roots:
        visit(root)
    return result


def breadthFirst(roots):
    result = list(roots)
    index = 0
    while index < len(result):
        result.extend(result[index].children)
        index += 1
    return result


def maxLevelOf(nodes):
    return max(node.level for node in nodes)


# ---------------------------------------------------------------------------
# 図種ごとの追加文法（pie / venn）
# ---------------------------------------------------------------------------

def parsePieSlice(text):
    """'名称:数値' を (名称, 数値) に分解する。合致しなければ None。"""
    if ":" not in text:
        return None
    name, number = text.rsplit(":", 1)
    name = name.strip(WHITESPACE)
    number = number.strip(WHITESPACE)
    if name == "" or not NUMBER_RE.fullmatch(number):
        return None
    return name, number


def parseVennText(text):
    """'名称[:数値]' を (名称, 数値または None) に分解する。"""
    if ":" in text:
        name, number = text.rsplit(":", 1)
        number = number.strip(WHITESPACE)
        if NUMBER_RE.fullmatch(number):
            return name.strip(WHITESPACE), number
    return text.strip(WHITESPACE), None


VENN_PAIRS = ["N1,N2", "N1,N3", "N2,N3"]


# ---------------------------------------------------------------------------
# 入力条件（4.4）
# ---------------------------------------------------------------------------

def checkConditions(typeId, roots, nodes):
    """入力条件違反があれば理由の文字列を、なければ None を返す。"""
    maxLevel = maxLevelOf(nodes)
    if typeId.startswith("hier-") or typeId == "fishBone":
        if len(roots) != 1:
            return f"ルートがちょうど1個であること（実際は{len(roots)}個）"
        return None
    if typeId == "pie":
        if len(roots) != 1:
            return f"ルートがちょうど1個であること（実際は{len(roots)}個）"
        if not roots[0].children:
            return "レベル2の節が1個以上あること"
        if maxLevel >= 3:
            return "レベル3以上の節が存在しないこと"
        for child in roots[0].children:
            if parsePieSlice(child.text) is None:
                return f"レベル2の節が「名称:数値」形式であること（{child.lineNo}行目: {child.text}）"
        return None
    if typeId == "venn":
        if maxLevel > 3:
            return "レベルが3以下であること"
        counts = {1: 0, 2: 0, 3: 0}
        for node in nodes:
            counts[node.level] += 1
        if not 1 <= counts[1] <= 3:
            return f"レベル1が1個以上3個以下であること（実際は{counts[1]}個）"
        if counts[2] > 3:
            return f"レベル2が高々3個であること（実際は{counts[2]}個）"
        if counts[3] > 1:
            return f"レベル3が高々1個であること（実際は{counts[3]}個）"
        seenLevel1 = 0
        seenLevel2 = 0
        for node in nodes:
            name, _ = parseVennText(node.text)
            if name == "":
                return f"全節の名称が空でないこと（{node.lineNo}行目）"
            if node.level == 1:
                seenLevel1 += 1
            elif node.level == 2:
                seenLevel2 += 1
                required = 2 if seenLevel2 == 1 else 3
                if seenLevel1 < required:
                    return (f"{seenLevel2}番目のレベル2（{node.lineNo}行目）に対応する集合 "
                            f"{VENN_PAIRS[seenLevel2 - 1]} がそれより前に出現していること")
            else:
                if seenLevel1 < 3:
                    return f"レベル3（{node.lineNo}行目）に対応する集合 N1,N2,N3 がそれより前に出現していること"
        return None
    if typeId in TABLE_TYPES:
        if maxLevel >= 3:
            return "レベルが2以下であること（レベル3以上が存在しないこと）"
        return None
    if typeId == "struct-flow":
        return None
    if typeId == "quadrant":
        if len(roots) != 2:
            return f"ルートがちょうど2個であること（実際は{len(roots)}個）"
        if maxLevel >= 4:
            return "レベル4以上の節が存在しないこと"
        for root in roots:
            if len(root.children) != 2:
                return f"各ルートのレベル2の節がちょうど2個であること（{root.lineNo}行目: {root.text}）"
            for child in root.children:
                if not 1 <= len(child.children) <= 9:
                    return (f"各レベル2節のレベル3の節が1個以上9個以下であること"
                            f"（{child.lineNo}行目: {child.text}）")
        return None
    return None


# ---------------------------------------------------------------------------
# 共通の出力部品
# ---------------------------------------------------------------------------

def escapeQuote(text):
    return text.replace('"', "#quot;")


def mermaidNodeDef(node):
    prefix, suffix = SHAPE_FORMATS[node.shape or "rect"]
    return f"{node.nodeId}{prefix}{escapeQuote(node.text)}{suffix}"


def mermaidStyleLines(nodes):
    lines = []
    for node in nodes:
        if node.color and node.isBorderless:
            lines.append(f"style {node.nodeId} fill:#{node.color},stroke:none")
        elif node.color:
            lines.append(f"style {node.nodeId} fill:#{node.color}")
        elif node.isBorderless:
            lines.append(f"style {node.nodeId} fill:none,stroke:none")
    return lines


def flowEdge(leftRef, lineType, label, rightRef):
    symbol = FLOW_SYMBOLS[lineType]
    if label:
        return f'{leftRef} {symbol} |"{escapeQuote(label)}"|{rightRef}'
    return f"{leftRef} {symbol} {rightRef}"


def blockEdge(leftId, lineType, label, rightId, reverse):
    symbol = (BLOCK_REVERSE_SYMBOLS if reverse else BLOCK_SYMBOLS)[lineType]
    if label:
        return f'{leftId} -- "{escapeQuote(label)}" {symbol} {rightId}'
    return f"{leftId} {symbol} {rightId}"


def renderGridRow(cells):
    tokens = []
    index = 0
    width = len(cells)
    while index < width:
        if cells[index] is None:
            end = index
            while end < width and cells[end] is None:
                end += 1
            count = end - index
            tokens.append("space" if count == 1 else f"space:{count}")
            index = end
        else:
            tokens.append(cells[index])
            index += 1
    return " ".join(tokens)


def tightLevelCoords(nodes, maxLevel):
    """10.1 の tight 時のレベル座標 t(L) と T を返す。"""
    gaps = [0] * (maxLevel + 1)  # gaps[L] = g(L)
    for node in nodes:
        if node.level >= 2 and node.label:
            gaps[node.level - 1] = 1
    coords = {1: 1}
    for level in range(1, maxLevel):
        coords[level + 1] = coords[level] + 1 + gaps[level]
    return coords, coords[maxLevel]


BLOCK_PADDING_FRONTMATTER = ["---", "config:", "  block:", "    padding: 30", "---"]


# ---------------------------------------------------------------------------
# 6.1 / 6.2 hier-mind / hier-mindlabel（PlantUML mindmap）
# ---------------------------------------------------------------------------

def generateMindmap(roots, nodes, options, useLabel):
    root = roots[0]

    if any(node.shape and node.shape not in ("borderless", "rounded") for node in nodes):
        warn("PlantUML mindmapでは枠の形状を表現できない（「無枠」「角丸」以外の形状指定を無視する）")
    if any(node.lineType for node in nodes):
        warn("PlantUML mindmapでは節ごとの線種を変更できない（線種名指定を無視する）")

    direction = options.direction
    if direction == "BT":
        warn("PlantUML mindmapでは方向 BT はサポートされていないため、TB として扱う")
        direction = "TB"
    if direction == "TD":
        direction = "TB"

    lineStyle = options.line
    if lineStyle.endswith("Arrow"):
        stripped = lineStyle[:-len("Arrow")]
        warn(f"PlantUML mindmapでは矢印を付けられないため、--line {lineStyle} を {stripped} として扱う")
        lineStyle = stripped

    if options.layout == "tight":
        padding, margin = 3, 2
    elif options.layout == "normal":
        padding, margin = 3, 5
    else:
        padding, margin = 5, 10

    lines = ["@startmindmap", "<style>", "mindmapDiagram {",
             "  node {", "    RoundCorner 0", f"    Padding {padding}", f"    Margin {margin}", "  }"]
    for node in nodes:
        if node.color or node.isRounded:
            lines.append(f"  .{node.nodeId}Node {{")
            if node.isRounded:
                lines.append("    RoundCorner 8")
            if node.color:
                lines.append(f"    BackgroundColor #{node.color}")
            lines.append("  }")
    if lineStyle == "dotted":
        lines += ["  arrow {", "    LineStyle 2-2", "  }"]
    elif lineStyle == "thick":
        lines += ["  arrow {", "    LineThickness 4", "  }"]
    lines += ["}", "</style>"]
    lines.append({"TB": "top to bottom direction",
                  "LR": "left to right direction",
                  "RL": "right to left direction"}[direction])

    if useLabel and root.label:
        warn("hier-mindlabel ではルートのラベルを無視する", root.lineNo)

    if direction == "TB":
        alternativeLabel = ":" if lineStyle == "dotted" else "|"
    else:
        alternativeLabel = "…" if lineStyle == "dotted" else "-"

    def nodeLine(node, depth):
        mark = "*" * depth + ("_" if node.isBorderless else "")
        suffix = f" <<{node.nodeId}Node>>" if (node.color or node.isRounded) else ""
        return f"{mark} {node.text}{suffix}"

    def emit(node, depth):
        lines.append(nodeLine(node, depth))
        hasLabel = useLabel and any(child.label for child in node.children)
        for child in node.children:
            if hasLabel:
                lines.append("*" * (depth + 1) + "_ " + (child.label or alternativeLabel))
                emit(child, depth + 2)
            else:
                emit(child, depth + 1)

    emit(root, 1)
    lines.append("@endmindmap")
    return lines


# ---------------------------------------------------------------------------
# 6.3 hier-flow（Mermaid flowchart）
# ---------------------------------------------------------------------------

def generateHierFlow(roots, nodes, options):
    root = roots[0]
    reverse = options.arrowDirection == "reverse"
    directionText = options.directionRaw
    isVertical = options.direction in ("TB", "TD", "BT")

    padding, nodeSpacing, rankSpacing = 8, 30, 30
    layout = options.layout
    if layout == "tight":
        nodeSpacing = rankSpacing = 15
    elif layout == "spacyXY":
        nodeSpacing = rankSpacing = 50
    elif layout == "spacyX":
        if isVertical:
            nodeSpacing = 50
        else:
            rankSpacing = 50
    elif layout == "spacyY":
        if isVertical:
            rankSpacing = 50
        else:
            nodeSpacing = 50
    elif layout == "spacyPadding":
        padding = 16

    lines = ["---", "config:", "  flowchart:",
             f"    padding: {padding}", f"    nodeSpacing: {nodeSpacing}",
             f"    rankSpacing: {rankSpacing}", "    diagramPadding: 5", "---"]
    if options.curve != "default":
        lines.append(f'%%{{init:{{"flowchart":{{"curve":"{options.curve}"}}}}}}%%')
    if reverse:
        directionText = REVERSE_DIRECTION[directionText]
    lines.append(f"flowchart {directionText}")

    defined = set()

    def ref(node):
        if node.nodeId in defined:
            return node.nodeId
        defined.add(node.nodeId)
        return mermaidNodeDef(node)

    edgeCount = 0
    for parent in breadthFirst(roots):
        for child in parent.children:
            lineType = child.lineType or options.line
            if reverse:
                left = ref(child)
                right = ref(parent)
            else:
                left = ref(parent)
                right = ref(child)
            lines.append(flowEdge(left, lineType, child.label, right))
            edgeCount += 1
    if edgeCount == 0:
        lines.append(mermaidNodeDef(root))

    styleLines = mermaidStyleLines(nodes)
    if styleLines:
        lines.append("")
        lines += styleLines
    return lines


# ---------------------------------------------------------------------------
# 6.4 / 10.2〜10.4 hier-block（Mermaid block）
# ---------------------------------------------------------------------------

def generateHierBlock(roots, nodes, options):
    root = roots[0]
    maxLevel = maxLevelOf(nodes)
    layout = options.layout
    spacyX = layout in ("spacyX", "spacyXY")
    spacyY = layout in ("spacyY", "spacyXY")
    tight = layout == "tight"
    direction = "TB" if options.direction == "TD" else options.direction

    # 10.2 位置決定
    positions = {}
    leafCount = 0
    for node in nodes:
        if not node.children:
            leafCount += 1
            positions[node.nodeId] = leafCount

    def decide(node):
        if node.children:
            for child in node.children:
                decide(child)
            childPositions = [positions[child.nodeId] for child in node.children]
            positions[node.nodeId] = (min(childPositions) + max(childPositions)) // 2

    decide(root)
    tightCoords, tightTotal = tightLevelCoords(nodes, maxLevel)

    # 10.3 グリッドへの展開
    placements = []
    if direction in ("TB", "BT"):
        width = 2 * leafCount - 1 if spacyX else leafCount
        if tight:
            rowCount = tightTotal
        elif spacyY:
            rowCount = 3 * maxLevel - 2
        else:
            rowCount = 2 * maxLevel - 1
        for node in nodes:
            position = positions[node.nodeId]
            column = 2 * position - 1 if spacyX else position
            if tight:
                row = tightCoords[node.level]
            elif spacyY:
                row = 3 * node.level - 2
            else:
                row = 2 * node.level - 1
            if direction == "BT":
                row = rowCount + 1 - row
            placements.append((row, column, node))
    else:
        if tight:
            width = tightTotal
        elif spacyX:
            width = 3 * maxLevel - 2
        else:
            width = 2 * maxLevel - 1
        rowCount = 2 * leafCount - 1 if spacyY else leafCount
        for node in nodes:
            if tight:
                column = tightCoords[node.level]
            elif spacyX:
                column = 3 * node.level - 2
            else:
                column = 2 * node.level - 1
            if direction == "RL":
                column = width + 1 - column
            position = positions[node.nodeId]
            row = 2 * position - 1 if spacyY else position
            placements.append((row, column, node))

    grid = [[None] * width for _ in range(rowCount)]
    for row, column, node in placements:
        grid[row - 1][column - 1] = mermaidNodeDef(node)

    lines = []
    if layout == "spacyPadding":
        lines += BLOCK_PADDING_FRONTMATTER
    lines += ["block", f"columns {width}"]
    lines += [renderGridRow(cells) for cells in grid]

    # 10.4 線の出力順（幅優先）
    reverse = options.arrowDirection == "reverse"
    edgeLines = []
    for parent in breadthFirst(roots):
        for child in parent.children:
            lineType = child.lineType or options.line
            edgeLines.append(blockEdge(parent.nodeId, lineType, child.label, child.nodeId, reverse))
    if edgeLines:
        lines.append("")
        lines += edgeLines

    styleLines = mermaidStyleLines(nodes)
    if styleLines:
        lines.append("")
        lines += styleLines
    return lines


# ---------------------------------------------------------------------------
# 10.5〜10.6 struct-flow（Mermaid block）
# ---------------------------------------------------------------------------

def generateStructFlow(roots, nodes, options):
    maxLevel = maxLevelOf(nodes)
    layout = options.layout
    spacyX = layout in ("spacyX", "spacyXY")
    spacyY = layout in ("spacyY", "spacyXY")
    tight = layout == "tight"
    tightCoords, tightTotal = tightLevelCoords(nodes, maxLevel)

    if tight:
        width = tightTotal
    elif spacyX:
        width = 3 * maxLevel - 2
    else:
        width = 2 * maxLevel - 1

    def columnOf(node):
        if tight:
            return tightCoords[node.level]
        if spacyX:
            return 3 * node.level - 2
        return 2 * node.level - 1

    groups = []
    for root in roots:
        groupRows = []

        def visit(node, isFirstChild):
            if not isFirstChild:
                groupRows.append([None] * width)
            groupRows[-1][columnOf(node) - 1] = mermaidNodeDef(node)
            for index, child in enumerate(node.children):
                visit(child, index == 0)

        visit(root, False)
        groups.append(groupRows)

    blankRow = renderGridRow([None] * width)
    lines = []
    if layout == "spacyPadding":
        lines += BLOCK_PADDING_FRONTMATTER
    lines += ["block", f"columns {width}"]
    for groupIndex, groupRows in enumerate(groups):
        if groupIndex > 0:
            lines.append("")
            if spacyY:
                lines.append(blankRow)
        for rowIndex, cells in enumerate(groupRows):
            if rowIndex > 0 and spacyY:
                lines.append(blankRow)
            lines.append(renderGridRow(cells))

    # 10.6 線
    edgeLines = []

    def subtreeEdges(node):
        for index, child in enumerate(node.children):
            lineType = child.lineType or options.line
            if child.label:
                edgeLines.append(blockEdge(node.nodeId, lineType, child.label, child.nodeId, False))
            elif index == 0:
                edgeLines.append(blockEdge(node.nodeId, lineType, None, child.nodeId, False))
            else:
                previous = node.children[index - 1]
                edgeLines.append(blockEdge(previous.nodeId, lineType, None, child.nodeId, False))
            subtreeEdges(child)

    for rootIndex, root in enumerate(roots):
        if rootIndex > 0:
            previousRoot = roots[rootIndex - 1]
            lineType = root.lineType or options.line
            edgeLines.append("")
            edgeLines.append(blockEdge(previousRoot.nodeId, lineType, None, root.nodeId, False))
        subtreeEdges(root)
    if edgeLines and edgeLines[0] == "":
        edgeLines.pop(0)
    if edgeLines:
        lines.append("")
        lines += edgeLines

    styleLines = mermaidStyleLines(nodes)
    if styleLines:
        lines.append("")
        lines += styleLines
    return lines


# ---------------------------------------------------------------------------
# 7 fishBone（Mermaid ishikawa-beta）
# ---------------------------------------------------------------------------

def generateFishBone(roots, nodes, options):
    lines = ["ishikawa-beta"]
    for node in nodes:
        lines.append(" " * (2 * node.level) + node.text)
    return lines


# ---------------------------------------------------------------------------
# 8.1 pie
# ---------------------------------------------------------------------------

def generatePie(roots, nodes, options):
    root = roots[0]
    slices = root.children
    if len(slices) >= 13:
        warn(f"pie のスライスが{len(slices)}個ある（Mermaidのテーマ変数は pie1〜pie12 までのため、"
             "13個目以降の色指定は無視する）")
    items = []
    for index, sliceNode in enumerate(slices, start=1):
        if sliceNode.color and index <= 12:
            items.append(f'  "pie{index}":"#{sliceNode.color}"')
    items.append('  "pieOpacity":1')
    lines = ['%%{init: {"theme":"base","themeVariables":{']
    lines += [item + "," for item in items[:-1]] + [items[-1]]
    lines.append("}}}%%")
    lines.append("pie showData")
    lines.append(f"title {root.text}")
    for sliceNode in slices:
        name, number = parsePieSlice(sliceNode.text)
        lines.append(f'"{escapeQuote(name)}" : {number}')
    return lines


# ---------------------------------------------------------------------------
# 8.2 venn
# ---------------------------------------------------------------------------

def generateVenn(roots, nodes, options):
    lines = ["venn-beta"]
    styleLines = []
    level1Count = 0
    level2Count = 0
    for node in nodes:
        name, number = parseVennText(node.text)
        if node.level == 1:
            level1Count += 1
            region = f"N{level1Count}"
            line = f'  set {region}["{escapeQuote(name)}"]'
        else:
            if node.level == 2:
                level2Count += 1
                region = VENN_PAIRS[level2Count - 1]
            else:
                region = "N1,N2,N3"
            line = f'  union {region}["{escapeQuote(name)}"]'
        if number is not None:
            line += f":{number}"
        lines.append(line)
        if node.color:
            styleLines.append(f"  style {region} fill:#{node.color}")
    if styleLines:
        lines.append("")
        lines += styleLines
    return lines


# ---------------------------------------------------------------------------
# 8.3 table系（PlantUML salt）
# ---------------------------------------------------------------------------

def displayWidth(text):
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def generateTable(roots, nodes, options, typeId):
    tableMatch = re.fullmatch(r"table([123]?)(c?)", typeId)
    boldColumn = int(tableMatch.group(1)) if tableMatch.group(1) else 0
    centering = tableMatch.group(2) == "c"

    rows = [[root.text] + [child.text for child in root.children] for root in roots]
    columnWidths = []
    for row in rows:
        for columnIndex, text in enumerate(row):
            width = displayWidth(text)
            if columnIndex >= len(columnWidths):
                columnWidths.append(width)
            else:
                columnWidths[columnIndex] = max(columnWidths[columnIndex], width)

    lines = ["@startsalt", "{#"]
    for rowIndex, row in enumerate(rows):
        cells = []
        for columnIndex, text in enumerate(row):
            cell = text
            if boldColumn and (columnIndex + 1 == boldColumn or rowIndex == 0):
                cell = f"<b>{cell}</b>"
            if centering:
                padWidth = columnWidths[columnIndex] - displayWidth(text)
                spaceCount = padWidth // 2
                leftCount = spaceCount // 2
                cell = "　" * leftCount + cell + "　" * (spaceCount - leftCount)
            cells.append(cell)
        line = "| " + " | ".join(cells)
        if centering:
            line = line.rstrip("　")
        lines.append(line)
    lines += ["}", "@endsalt"]
    return lines


# ---------------------------------------------------------------------------
# 9 quadrant（Mermaid quadrantChart）
# ---------------------------------------------------------------------------

def formatHundredths(value):
    """100倍した整数値を 0.4 / 0.25 の形式で表記する。"""
    integerPart, fraction = divmod(value, 100)
    if fraction % 10 == 0:
        return f"{integerPart}.{fraction // 10}"
    return f"{integerPart}.{fraction:02d}"


def generateQuadrant(roots, nodes, options):
    firstRoot, secondRoot = roots
    # レベル2節 → 象限番号
    quadrantOf = [
        (firstRoot.children[0], 3, 25, 40),
        (firstRoot.children[1], 2, 25, 90),
        (secondRoot.children[0], 4, 75, 40),
        (secondRoot.children[1], 1, 75, 90),
    ]
    byQuadrant = {quadrant: node for node, quadrant, _, _ in quadrantOf}

    lines = []
    fillLines = []
    for quadrant in range(1, 5):
        node = byQuadrant[quadrant]
        if node.color:
            fillLines.append(f'    quadrant{quadrant}Fill: "#{node.color}"')
    if fillLines:
        lines += ["---", "config:", "  themeVariables:"] + fillLines + ["---"]
    lines.append("quadrantChart")
    lines.append(f'  x-axis "{escapeQuote(firstRoot.text)}" --> "{escapeQuote(secondRoot.text)}"')
    lines.append(f'  y-axis "{escapeQuote(firstRoot.children[0].text)}" --> '
                 f'"{escapeQuote(firstRoot.children[1].text)}"')
    for quadrant in range(1, 5):
        lines.append(f'  quadrant-{quadrant} "{escapeQuote(byQuadrant[quadrant].children[0].text)}"')
    for node, _, xValue, yTop in quadrantOf:
        for pointIndex, point in enumerate(node.children[1:], start=1):
            yValue = yTop - 5 * (pointIndex - 1)
            lines.append(f'  "{escapeQuote(point.text)}": '
                         f'[{formatHundredths(xValue)}, {formatHundredths(yValue)}] radius:0')
    return lines


# ---------------------------------------------------------------------------
# 図種の振り分け
# ---------------------------------------------------------------------------

def generateDiagram(typeId, roots, nodes, options):
    """(フェンスの言語, 本文の行リスト) を返す。"""
    if typeId == "hier-mind":
        return "plantuml", generateMindmap(roots, nodes, options, useLabel=False)
    if typeId == "hier-mindlabel":
        return "plantuml", generateMindmap(roots, nodes, options, useLabel=True)
    if typeId == "hier-flow":
        return "mermaid", generateHierFlow(roots, nodes, options)
    if typeId == "hier-block":
        return "mermaid", generateHierBlock(roots, nodes, options)
    if typeId == "struct-flow":
        return "mermaid", generateStructFlow(roots, nodes, options)
    if typeId == "fishBone":
        return "mermaid", generateFishBone(roots, nodes, options)
    if typeId == "pie":
        return "mermaid", generatePie(roots, nodes, options)
    if typeId == "venn":
        return "mermaid", generateVenn(roots, nodes, options)
    if typeId in TABLE_TYPES:
        return "plantuml", generateTable(roots, nodes, options, typeId)
    if typeId == "quadrant":
        return "mermaid", generateQuadrant(roots, nodes, options)
    raise ValueError(typeId)


def buildHeading(typeId, args):
    parts = []
    for optionName in HEADING_OPTIONS.get(typeId, []):
        value = getattr(args, optionName)
        if value is not None:
            parts.append(f"--{optionName} {value}")
    if parts:
        return f"## {typeId} ({' '.join(parts)})"
    return f"## {typeId}"


class ResolvedOptions:
    def __init__(self, args):
        self.directionRaw = args.direction or "TB"
        self.direction = self.directionRaw
        self.layout = args.layout or "normal"
        self.line = args.line or "solid"
        self.arrowDirection = args.arrowDirection or "default"
        self.curve = args.curve or "default"


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def buildArgumentParser():
    parser = argparse.ArgumentParser(
        prog="heading2diagram.py",
        description="見出し形式Markdownからダイアグラム定義（PlantUML / Mermaid）を生成する。")
    parser.add_argument("input", metavar="INPUT.md", help="見出し形式の入力ファイルパス")
    parser.add_argument("-o", "--output", help="出力ファイルパス（省略時は標準出力）")
    parser.add_argument("-t", "--type", dest="types", nargs="+", action="extend",
                        choices=ALL_TYPES, metavar="TYPE",
                        help="生成する図種ID（複数指定可）: " + ", ".join(ALL_TYPES))
    parser.add_argument("--direction", choices=DIRECTION_CHOICES)
    parser.add_argument("--layout", choices=LAYOUT_CHOICES)
    parser.add_argument("--line", choices=LINE_CHOICES)
    parser.add_argument("--arrowDirection", choices=ARROW_DIRECTION_CHOICES)
    parser.add_argument("--curve", choices=CURVE_CHOICES)
    return parser


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    args = buildArgumentParser().parse_args(argv)

    try:
        with open(args.input, "rb") as inputFile:
            sourceText = inputFile.read().decode("utf-8-sig")
    except OSError as exc:
        errorExit(f"入力ファイルを読めない: {args.input} ({exc.strerror or exc})")
    except UnicodeDecodeError:
        errorExit(f"入力ファイルをUTF-8として復号できない: {args.input}")

    roots = parseInput(sourceText)
    if not roots:
        errorExit("有効な見出し行が1行も無い")
    nodes = preorder(roots)
    options = ResolvedOptions(args)
    hasAnyLabel = any(node.label for node in nodes)

    if args.types:
        explicit = True
        typeIds = list(dict.fromkeys(args.types))
    else:
        explicit = False
        typeIds = ["hier-mindlabel" if hasAnyLabel else "hier-mind", "hier-block", "hier-flow",
                   "fishBone", "pie", "venn", "table", "struct-flow", "quadrant"]

    # 図種の決定と入力条件の判定（すべて判定してから生成する）
    targets = []
    errors = []
    for typeId in typeIds:
        actualType = typeId
        if typeId == "hier-mind" and hasAnyLabel:
            actualType = "hier-mindlabel"
        violation = checkConditions(actualType, roots, nodes)
        if violation:
            if explicit:
                errors.append(f"図種 {typeId} の入力条件を満たさない: {violation}")
            else:
                warn(f"図種 {actualType} の入力条件を満たさないためスキップする: {violation}")
            continue
        targets.append((typeId, actualType))
    if errors:
        for message in errors:
            sys.stderr.write(f"error: {message}\n")
        sys.exit(1)

    blocks = []
    for typeId, actualType in targets:
        if typeId != actualType:
            warn("入力にラベル（|x|）が含まれるため、hier-mind を hier-mindlabel として生成する")
        fenceLanguage, bodyLines = generateDiagram(actualType, roots, nodes, options)
        blocks.append("\n".join([buildHeading(actualType, args), f"```{fenceLanguage}"]
                                + bodyLines + ["```"]))
    if not blocks:
        errorExit("生成できた図種が1つも無い")

    outputText = "\n\n".join(blocks) + "\n"
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8", newline="\n") as outputFile:
                outputFile.write(outputText)
        except OSError as exc:
            errorExit(f"出力ファイルへ書き込めない: {args.output} ({exc.strerror or exc})")
    else:
        sys.stdout.flush()
        sys.stdout.buffer.write(outputText.encode("utf-8"))
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
