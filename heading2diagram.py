#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""heading2diagram: 見出し形式Markdownからダイアグラム定義を生成するCLIプログラム.

Markdownの見出し（# 〜）だけで記述された階層データを読み込み、
PlantUML（mindmap / salt）および Mermaid（flowchart / block / ishikawa / pie / venn / quadrantChart）
のダイアグラム定義をMarkdown文書として出力する。標準ライブラリのみを使用する。
"""

import argparse
import math
import re
import sys
import unicodedata

sys.setrecursionlimit(10000)

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

typeIdList = [
    'hier-mind', 'hier-mindlabel', 'hier-block', 'hier-flow', 'fishBone', 'pie', 'venn',
    'table', 'tablec', 'table1', 'table1c', 'table2', 'table2c', 'table3', 'table3c',
    'struct-flow', 'quadrant', 'star',
]
tableTypeIds = ['table', 'tablec', 'table1', 'table1c', 'table2', 'table2c', 'table3', 'table3c']
defaultTypeIds = [
    'hier-mind', 'hier-block', 'hier-flow', 'fishBone', 'pie', 'venn', 'table',
    'struct-flow', 'quadrant', 'star',
]
plantumlTypeIds = {'hier-mind', 'hier-mindlabel'} | set(tableTypeIds)

directionChoices = ['TB', 'TD', 'BT', 'LR', 'RL']
layoutChoices = ['tight', 'normal', 'spacyX', 'spacyY', 'spacyXY', 'spacyPadding']
lineChoices = ['dotted', 'solid', 'thick', 'dottedArrow', 'solidArrow', 'thickArrow']
arrowDirectionChoices = ['default', 'reverse']
curveChoices = ['default', 'linear', 'bumpX', 'bumpY', 'cardinal', 'catmullRom',
          'monotoneX', 'monotoneY', 'natural', 'step']

# 見出しに含めるオプション（3.2）
headingOptions = {
    'hier-mind': ['direction', 'layout', 'line'],
    'hier-mindlabel': ['direction', 'layout', 'line'],
    'hier-block': ['direction', 'layout', 'line', 'arrowDirection'],
    'hier-flow': ['direction', 'layout', 'line', 'arrowDirection', 'curve'],
    'struct-flow': ['layout', 'line'],
    'star': ['layout', 'line', 'arrowDirection', 'degree', 'span', 'radius', 'blockWidth'],
}

# 線種名（5.3）
lineStyleNames = {
    '実線': 'solid', 'solid': 'solid',
    '点線': 'dotted', 'dotted': 'dotted',
    '太線': 'thick', 'thick': 'thick',
    '実線矢印': 'solidArrow', 'solidArrow': 'solidArrow',
    '点線矢印': 'dottedArrow', 'dottedArrow': 'dottedArrow',
    '太線矢印': 'thickArrow', 'thickArrow': 'thickArrow',
}

# 形状名（4.3）
shapeNames = {
    '四角': 'rect', 'rect': 'rect',
    '角丸': 'rounded', 'rounded': 'rounded',
    'スタ': 'stadium', 'stadium': 'stadium',
    'サブ': 'fr-rect', 'fr-rect': 'fr-rect',
    '円柱': 'cyl', 'cyl': 'cyl',
    '円形': 'circle', 'circle': 'circle',
    '非対': 'odd', 'odd': 'odd',
    'ひし': 'diam', 'diam': 'diam',
    '六角': 'hex', 'hex': 'hex',
    '四右': 'lean-r', 'lean-r': 'lean-r',
    '四左': 'lean-l', 'lean-l': 'lean-l',
    '台形': 'trap-b', 'trap-b': 'trap-b',
    '逆台': 'trap-t', 'trap-t': 'trap-t',
    '重円': 'dbl-circ', 'dbl-circ': 'dbl-circ',
    '無枠': 'borderless', 'borderless': 'borderless',
}

# Mermaidの形状書式（開き記号, 閉じ記号）
shapeBrackets = {
    'rect': ('[', ']'),
    'rounded': ('(', ')'),
    'stadium': ('([', '])'),
    'fr-rect': ('[[', ']]'),
    'cyl': ('[(', ')]'),
    'circle': ('((', '))'),
    'odd': ('>', ']'),
    'diam': ('{', '}'),
    'hex': ('{{', '}}'),
    'lean-r': ('[/', '/]'),
    'lean-l': ('[\\', '\\]'),
    'trap-b': ('[/', '\\]'),
    'trap-t': ('[\\', '/]'),
    'dbl-circ': ('(((', ')))'),
    'borderless': ('[', ']'),
}

# 線の記法（5.3, 5.4）
flowSymbols = {
    'solid': '---', 'dotted': '-.-', 'thick': '===',
    'solidArrow': '-->', 'dottedArrow': '-.->', 'thickArrow': '==>',
}
blockSymbols = {
    'solid': '---', 'dotted': '-.-', 'thick': '===',
    'solidArrow': '--->', 'dottedArrow': '-.->', 'thickArrow': '===>',
}
blockReverseSymbols = {
    'solidArrow': '<---', 'dottedArrow': '<-.-', 'thickArrow': '<===',
}
reverseDirection = {'TB': 'BT', 'TD': 'BT', 'BT': 'TB', 'LR': 'RL', 'RL': 'LR'}

# star の定数（10.9.1）
wideCharWidth = 16
narrowCharWidth = 9
blockPaddingX = 30
blockHeight = 40
labelPaddingX = 8
labelHeight = 24
angleWeight = 2.0
sizePenalty = 0.5
searchRange = 1.5

# star の --layout による値（10.9.2）: (minLineLength, labelMargin, minBlockGap, cellGap)
starLayoutValues = {
    'tight': (15, 8, 8, 8),
    'normal': (30, 16, 16, 8),
    'spacyX': (60, 32, 32, 8),
    'spacyY': (60, 32, 32, 8),
    'spacyXY': (60, 32, 32, 8),
    'spacyPadding': (30, 16, 16, 30),
}

blockPaddingFrontmatter = ['---', 'config:', '  block:', '    padding: 30', '---']

fullWidthSpace = '　'

headingRe = re.compile(r'^(#+)(?:[ \t]+(.*))?$')
headingTypoRe = re.compile(r'^#+[^ \t#]')
colorRe = re.compile(r':#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$')
colorTypoRe = re.compile(r':#\S*$')
modifierRe = re.compile(r'([^ \t;]*);')
numberRe = re.compile(r'[0-9]+(\.[0-9]+)?')


# ---------------------------------------------------------------------------
# 警告・エラー
# ---------------------------------------------------------------------------

class Reporter:
    """警告をstderrへ出力する。同一の警告は1回のみ出力する。"""

    def __init__(self):
        self.seenMessages = set()

    def warn(self, message):
        if message in self.seenMessages:
            return
        self.seenMessages.add(message)
        sys.stderr.write('warning: ' + message + '\n')
        sys.stderr.flush()

    @staticmethod
    def error(message):
        sys.stderr.write('error: ' + message + '\n')
        sys.stderr.flush()


reporter = Reporter()


class ConditionError(Exception):
    """図種の入力条件違反（4.4）。"""


class InputError(Exception):
    """入力エラー（終了コード1）。"""


# ---------------------------------------------------------------------------
# 入力の解析（4.1）
# ---------------------------------------------------------------------------

class ContentInfo:
    """見出し行の内容の解析結果。"""

    def __init__(self):
        self.label = None
        self.lineType = None
        self.shape = None
        self.text = ''
        self.color = None


class HeadingRecord:
    """見出し行1行分の情報。"""

    def __init__(self, lineNo, level, info):
        self.lineNo = lineNo
        self.level = level
        self.info = info

    @property
    def isEmpty(self):
        return self.info.text == ''


def stripBlank(text):
    """半角スペースとタブのみを前後から取り除く。"""
    return text.strip(' \t')


def parseContent(content, lineNo):
    """見出し行の内容を ラベル・色・修飾・テキスト に分解する。"""
    info = ContentInfo()
    rest = stripBlank(content)

    # 1. ラベル
    if rest.startswith('|'):
        closeIndex = rest.find('|', 1)
        if closeIndex < 0:
            reporter.warn(f'line {lineNo}: ラベルの閉じ "|" が無い。先頭の "|" を含めて内容全体をテキストとして扱う')
            info.text = rest
            return info
        labelText = stripBlank(rest[1:closeIndex])
        rest = stripBlank(rest[closeIndex + 1:])
        if labelText == '':
            reporter.warn(f'line {lineNo}: ラベルが空である。ラベル無しとして扱う')
        else:
            info.label = labelText

    # 2. 色
    colorMatch = colorRe.search(rest)
    if colorMatch:
        info.color = '#' + colorMatch.group(1)
        rest = rest[:colorMatch.start()]
    elif colorTypoRe.search(rest):
        reporter.warn(f'line {lineNo}: ":#" の後が16進3桁・6桁でない（色の書き間違いの可能性）。テキストの一部として扱う')

    # 3. 修飾（線種名・形状名）
    for _ in range(2):
        modifierMatch = modifierRe.match(rest)
        if not modifierMatch:
            break
        name = modifierMatch.group(1)
        if name in lineStyleNames:
            if info.lineType is not None:
                reporter.warn(f'line {lineNo}: 線種名 "{name}" が重複している。テキストの一部として扱う')
                break
            info.lineType = lineStyleNames[name]
        elif name in shapeNames:
            if info.shape is not None:
                reporter.warn(f'line {lineNo}: 形状名 "{name}" が重複している。テキストの一部として扱う')
                break
            info.shape = shapeNames[name]
        else:
            reporter.warn(f'line {lineNo}: "{name};" は未知の線種名・形状名である（書き間違いの可能性）。テキストの一部として扱う')
            break
        rest = rest[modifierMatch.end():].lstrip(' \t')

    # 4. テキスト
    info.text = stripBlank(rest)
    return info


def parseLines(lines):
    """入力の各行を解析し、見出し行の記録のリストを返す。"""
    records = []
    for index, rawLine in enumerate(lines):
        lineNo = index + 1
        line = rawLine.rstrip('\r\n')
        headingMatch = headingRe.match(line)
        if headingMatch:
            level = len(headingMatch.group(1))
            content = headingMatch.group(2)
            if content is None or stripBlank(content) == '':
                info = ContentInfo()
            else:
                info = parseContent(content, lineNo)
            records.append(HeadingRecord(lineNo, level, info))
        elif line.strip() == '':
            continue
        elif headingTypoRe.match(line):
            reporter.warn(f'line {lineNo}: "#" の直後に空白が無い（見出し行の書き間違いの可能性）。無視する')
        else:
            reporter.warn(f'line {lineNo}: 見出し行でも空行でもない行である。無視する')
    return records


# ---------------------------------------------------------------------------
# 木構造（4.2, 5.1）
# ---------------------------------------------------------------------------

class Node:
    """木の節。"""

    def __init__(self, record, level):
        info = record.info
        self.label = info.label
        self.lineType = info.lineType
        self.shape = info.shape
        self.text = info.text
        self.color = info.color
        self.level = level
        self.lineNo = record.lineNo
        self.children = []
        self.parent = None
        self.nodeId = ''


class Tree:
    """節の木（ルートは複数あり得る）。"""

    def __init__(self, roots):
        self.roots = roots

    def allNodes(self):
        """全節を深さ優先（出現順）で返す。"""
        result = []
        stack = list(reversed(self.roots))
        while stack:
            node = stack.pop()
            result.append(node)
            stack.extend(reversed(node.children))
        return result

    def maxLevel(self):
        return max((node.level for node in self.allNodes()), default=0)

    def nodesAtLevel(self, level):
        return [node for node in self.allNodes() if node.level == level]


def assignIds(nodes, prefix):
    for index, node in enumerate(nodes, start=1):
        node.nodeId = f'{prefix}{index}' if prefix == 'N' else f'{prefix}_{index}'
        assignIds(node.children, node.nodeId)


def buildTree(records, includeEmpty):
    """見出し行の記録から木を構築する。includeEmpty=True で table系用の木となる。"""
    roots = []
    stack = []
    prevLevel = 0
    for record in records:
        if record.isEmpty and not includeEmpty:
            continue
        level = record.level
        if level > prevLevel + 1:
            effectiveLevel = prevLevel + 1
            reporter.warn(f'line {record.lineNo}: レベル飛び（レベル{level}、直前の見出しはレベル{prevLevel}）。'
                          f'レベル{effectiveLevel}として扱う')
            level = effectiveLevel
        node = Node(record, level)
        if level == 1:
            roots.append(node)
        else:
            parent = stack[level - 2]
            parent.children.append(node)
            node.parent = parent
        del stack[level - 1:]
        stack.append(node)
        prevLevel = level
    assignIds(roots, 'N')
    return Tree(roots)


# ---------------------------------------------------------------------------
# 共通の補助関数
# ---------------------------------------------------------------------------

def quoteText(text):
    """Mermaid向けに " を #quot; に置換する（5.2）。"""
    return text.replace('"', '#quot;')


def mermaidNodeDef(node):
    """4.3 の書式でMermaidのノード定義を返す。"""
    openMark, closeMark = shapeBrackets[node.shape or 'rect']
    return f'{node.nodeId}{openMark}"{quoteText(node.text)}"{closeMark}'


def mermaidStyleLines(nodes):
    """6章冒頭の色の出力規則による style 行のリストを返す。"""
    result = []
    for node in nodes:
        if node.shape == 'borderless':
            if node.color:
                result.append(f'style {node.nodeId} fill:{node.color},stroke:none')
            else:
                result.append(f'style {node.nodeId} fill:none,stroke:none')
        elif node.color:
            result.append(f'style {node.nodeId} fill:{node.color}')
    return result


def blockEdge(sourceId, targetId, lineType, label, reverse):
    """block の線の記法（5.3, 5.4）。"""
    operator = blockSymbols[lineType]
    if reverse:
        operator = blockReverseSymbols.get(lineType, operator)
    if label:
        return f'{sourceId} -- "{quoteText(label)}" {operator} {targetId}'
    return f'{sourceId} {operator} {targetId}'


def spaceToken(count):
    return 'space' if count == 1 else f'space:{count}'


def renderGridRow(cells, width):
    """1行分（width列）のセルを出力文字列にする。cells は 列(1始まり) → ノード定義。"""
    parts = []
    emptyRun = 0
    for col in range(1, width + 1):
        if col in cells:
            if emptyRun:
                parts.append(spaceToken(emptyRun))
                emptyRun = 0
            parts.append(cells[col])
        else:
            emptyRun += 1
    if emptyRun:
        parts.append(spaceToken(emptyRun))
    return ' '.join(parts)


def breadthFirstEdges(root):
    """親→子の組を幅優先（10.4）で返す。"""
    edges = []
    queue = [root]
    index = 0
    while index < len(queue):
        parent = queue[index]
        index += 1
        for child in parent.children:
            edges.append((parent, child))
            queue.append(child)
    return edges


def requireSingleRoot(tree, typeId):
    if len(tree.roots) != 1:
        raise ConditionError(f'{typeId}: ルートがちょうど1個である必要がある（ルートが{len(tree.roots)}個ある）')
    return tree.roots[0]


def displayWidth(text):
    """表示幅（8.3.2）。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1 for ch in text)


def textPixelWidth(text):
    """star の推定幅 tw(s)（10.9.3）。"""
    return sum(wideCharWidth if unicodedata.east_asian_width(ch) in ('W', 'F') else narrowCharWidth
               for ch in text)


def levelGaps(tree, maxDepth):
    """tight 用のレベル間のラベル有無 g(L)（10.1）。gapList[L] = g(L)。"""
    gapList = [0] * (maxDepth + 1)
    for node in tree.allNodes():
        if node.level >= 2 and node.label:
            gapList[node.level - 1] = 1
    return gapList


def tightLevelCoords(tree, maxDepth):
    """tight 時のレベル座標 t(L) と T を返す（10.1）。"""
    gapList = levelGaps(tree, maxDepth)
    coords = [0] * (maxDepth + 1)
    coords[1] = 1
    for level in range(1, maxDepth):
        coords[level + 1] = coords[level] + 1 + gapList[level]
    return coords, coords[maxDepth]


# ---------------------------------------------------------------------------
# 6.1 / 6.2 hier-mind / hier-mindlabel
# ---------------------------------------------------------------------------

def generateMindmap(tree, opts, typeId, withLabel):
    root = requireSingleRoot(tree, typeId)
    nodes = tree.allNodes()

    direction = opts.direction
    if direction == 'BT':
        reporter.warn(f'{typeId}: PlantUML mindmapでは --direction BT はサポートされていない。TB として扱う')
        direction = 'TB'
    if direction == 'TD':
        direction = 'TB'

    lineStyle = opts.line
    if lineStyle.endswith('Arrow'):
        reporter.warn(f'{typeId}: PlantUML mindmapでは矢印を付けられない。--line {lineStyle} を '
                      f'{lineStyle[:-5]} として扱う')
        lineStyle = lineStyle[:-5]

    if any(node.shape not in (None, 'borderless', 'rounded') for node in nodes):
        reporter.warn(f'{typeId}: PlantUML mindmapでは枠の形状を表現できない。形状の指定を無視する')
    if any(node.lineType is not None for node in nodes):
        reporter.warn(f'{typeId}: PlantUML mindmapでは節ごとの線種を変更できない。線種名の指定を無視する')
    if withLabel and root.label:
        reporter.warn(f'line {root.lineNo}: {typeId}: ルートのラベルは無視する')

    if opts.layout == 'tight':
        padding, margin = 3, 2
    elif opts.layout == 'normal':
        padding, margin = 3, 5
    else:
        padding, margin = 5, 10

    out = ['@startmindmap', '<style>', 'mindmapDiagram {',
           '  node {', '    RoundCorner 0', f'    Padding {padding}', f'    Margin {margin}', '  }']
    for node in nodes:
        if node.shape == 'rounded' or node.color:
            out.append(f'  .{node.nodeId}Node {{')
            if node.shape == 'rounded':
                out.append('    RoundCorner 8')
            if node.color:
                out.append(f'    BackgroundColor {node.color}')
            out.append('  }')
    if lineStyle == 'dotted':
        out += ['  arrow {', '    LineStyle 2-2', '  }']
    elif lineStyle == 'thick':
        out += ['  arrow {', '    LineThickness 4', '  }']
    out += ['}', '</style>']
    out.append({'TB': 'top to bottom direction', 'LR': 'left to right direction',
                'RL': 'right to left direction'}[direction])

    if direction == 'TB':
        altLabel = ':' if lineStyle == 'dotted' else '|'
    else:
        altLabel = '…' if lineStyle == 'dotted' else '-'

    def bodyLine(node, depth):
        mark = '*' * depth + ('_' if node.shape == 'borderless' else '')
        suffix = f' <<{node.nodeId}Node>>' if (node.shape == 'rounded' or node.color) else ''
        return f'{mark} {node.text}{suffix}'

    def emit(node, depth):
        out.append(bodyLine(node, depth))
        hasLabel = withLabel and any(child.label for child in node.children)
        for child in node.children:
            if hasLabel:
                out.append('*' * (depth + 1) + '_ ' + (child.label if child.label else altLabel))
                emit(child, depth + 2)
            else:
                emit(child, depth + 1)

    emit(root, 1)
    out.append('@endmindmap')
    return out


# ---------------------------------------------------------------------------
# 6.3 hier-flow
# ---------------------------------------------------------------------------

def generateHierFlow(tree, opts):
    root = requireSingleRoot(tree, 'hier-flow')
    reverse = opts.arrowDirection == 'reverse'
    flowDirection = reverseDirection[opts.direction] if reverse else opts.direction
    isHorizontal = opts.direction in ('LR', 'RL')

    padding, nodeSpacing, rankSpacing = 8, 30, 30
    layout = opts.layout
    if layout == 'tight':
        nodeSpacing = rankSpacing = 15
    elif layout == 'spacyXY':
        nodeSpacing = rankSpacing = 50
    elif layout == 'spacyX':
        if isHorizontal:
            rankSpacing = 50
        else:
            nodeSpacing = 50
    elif layout == 'spacyY':
        if isHorizontal:
            nodeSpacing = 50
        else:
            rankSpacing = 50
    elif layout == 'spacyPadding':
        padding = 16

    out = ['---', 'config:', '  flowchart:', f'    padding: {padding}', f'    nodeSpacing: {nodeSpacing}',
           f'    rankSpacing: {rankSpacing}', '    diagramPadding: 5', '---']
    if opts.curve != 'default':
        out.append('%%{init:{"flowchart":{"curve":"' + opts.curve + '"}}}%%')
    out.append('flowchart ' + flowDirection)

    definedIds = set()

    def reference(node):
        if node.nodeId in definedIds:
            return node.nodeId
        definedIds.add(node.nodeId)
        return mermaidNodeDef(node)

    edges = breadthFirstEdges(root)
    if not edges:
        out.append(mermaidNodeDef(root))
    for parent, child in edges:
        operator = flowSymbols[child.lineType or opts.line]
        left, right = (child, parent) if reverse else (parent, child)
        leftText = reference(left)
        rightText = reference(right)
        if child.label:
            out.append(f'{leftText} {operator} |"{quoteText(child.label)}"|{rightText}')
        else:
            out.append(f'{leftText} {operator} {rightText}')

    styles = mermaidStyleLines(tree.allNodes())
    if styles:
        out.append('')
        out += styles
    return out


# ---------------------------------------------------------------------------
# 6.4 / 10.2〜10.4 hier-block
# ---------------------------------------------------------------------------

def computeLeafPositions(root):
    """10.2 の位置決定。節 → 位置 の辞書と葉の総数を返す。"""
    positions = {}
    leafCounter = [0]

    def visit(node):
        if not node.children:
            leafCounter[0] += 1
            positions[node] = leafCounter[0]
            return
        for child in node.children:
            visit(child)
        childPositions = [positions[child] for child in node.children]
        positions[node] = (min(childPositions) + max(childPositions)) // 2

    visit(root)
    return positions, leafCounter[0]


def generateHierBlock(tree, opts):
    root = requireSingleRoot(tree, 'hier-block')
    direction = 'TB' if opts.direction == 'TD' else opts.direction
    layout = opts.layout
    isTight = layout == 'tight'
    isSpacyX = layout in ('spacyX', 'spacyXY')
    isSpacyY = layout in ('spacyY', 'spacyXY')

    positions, leafCount = computeLeafPositions(root)
    maxDepth = tree.maxLevel()
    tightCoords, tightTotal = tightLevelCoords(tree, maxDepth)
    nodes = tree.allNodes()

    grid = {}
    if direction in ('TB', 'BT'):
        if isSpacyX:
            width = 2 * leafCount - 1
            colOf = lambda p: 2 * p - 1
        else:
            width = leafCount
            colOf = lambda p: p
        if isTight:
            rowOfLevel = lambda level: tightCoords[level]
            rowCount = tightTotal
        elif isSpacyY:
            rowOfLevel = lambda level: 3 * level - 2
            rowCount = 3 * maxDepth - 2
        else:
            rowOfLevel = lambda level: 2 * level - 1
            rowCount = 2 * maxDepth - 1
        for node in nodes:
            row = rowOfLevel(node.level)
            if direction == 'BT':
                row = rowCount + 1 - row
            grid.setdefault(row, {})[colOf(positions[node])] = mermaidNodeDef(node)
    else:
        if isTight:
            colOfLevel = lambda level: tightCoords[level]
            width = tightTotal
        elif isSpacyX:
            colOfLevel = lambda level: 3 * level - 2
            width = 3 * maxDepth - 2
        else:
            colOfLevel = lambda level: 2 * level - 1
            width = 2 * maxDepth - 1
        if isSpacyY:
            rowOf = lambda p: 2 * p - 1
            rowCount = 2 * leafCount - 1
        else:
            rowOf = lambda p: p
            rowCount = leafCount
        for node in nodes:
            col = colOfLevel(node.level)
            if direction == 'RL':
                col = width + 1 - col
            grid.setdefault(rowOf(positions[node]), {})[col] = mermaidNodeDef(node)

    out = []
    if layout == 'spacyPadding':
        out += blockPaddingFrontmatter
    out += ['block', f'columns {width}']
    for row in range(1, rowCount + 1):
        out.append(renderGridRow(grid.get(row, {}), width))

    reverse = opts.arrowDirection == 'reverse'
    edgeLines = [blockEdge(parent.nodeId, child.nodeId, child.lineType or opts.line, child.label, reverse)
                 for parent, child in breadthFirstEdges(root)]
    if edgeLines:
        out.append('')
        out += edgeLines
    styles = mermaidStyleLines(nodes)
    if styles:
        out.append('')
        out += styles
    return out


# ---------------------------------------------------------------------------
# 7 fishBone
# ---------------------------------------------------------------------------

def generateFishBone(tree, opts):
    requireSingleRoot(tree, 'fishBone')
    out = ['ishikawa-beta']
    for node in tree.allNodes():
        out.append(' ' * (2 * node.level) + node.text)
    return out


# ---------------------------------------------------------------------------
# 8.1 pie
# ---------------------------------------------------------------------------

def parsePieSlice(text):
    """「名称:数値」を分解する。合致しなければ None。"""
    if ':' not in text:
        return None
    name, value = text.rsplit(':', 1)
    name, value = stripBlank(name), stripBlank(value)
    if name == '' or not numberRe.fullmatch(value):
        return None
    return name, value


def generatePie(tree, opts):
    root = requireSingleRoot(tree, 'pie')
    if not root.children:
        raise ConditionError('pie: レベル2の節が1個以上必要である')
    if tree.maxLevel() > 2:
        raise ConditionError('pie: レベル3以上の節が存在してはならない')
    slices = []
    for child in root.children:
        parsed = parsePieSlice(child.text)
        if parsed is None:
            raise ConditionError(f'pie: line {child.lineNo}: レベル2の節が「名称:数値」形式でない（"{child.text}"）')
        slices.append((parsed[0], parsed[1], child.color))
    if len(slices) >= 13:
        reporter.warn(f'pie: スライスが{len(slices)}個ある。Mermaidのテーマ変数は pie1〜pie12 までのため、'
                      '13個目以降の色指定は無視する')

    themeItems = []
    for index, (_, _, color) in enumerate(slices, start=1):
        if color and index <= 12:
            themeItems.append(f'"pie{index}":"{color}"')
    themeItems.append('"pieOpacity":1')

    out = ['%%{init: {"theme":"base","themeVariables":{']
    for index, item in enumerate(themeItems):
        out.append('  ' + item + (',' if index < len(themeItems) - 1 else ''))
    out.append('}}}%%')
    out += ['pie showData', f'title {root.text}']
    for name, value, _ in slices:
        out.append(f'"{quoteText(name)}" : {value}')
    return out


# ---------------------------------------------------------------------------
# 8.2 venn
# ---------------------------------------------------------------------------

vennLevel2Sets = [(1, 2), (1, 3), (2, 3)]


def parseVennName(text):
    if ':' in text:
        name, value = text.rsplit(':', 1)
        value = stripBlank(value)
        if numberRe.fullmatch(value):
            return stripBlank(name), value
    return text, None


def generateVenn(tree, opts):
    nodes = tree.allNodes()
    if tree.maxLevel() > 3:
        raise ConditionError('venn: レベルは3以下である必要がある')
    level1Count = len(tree.nodesAtLevel(1))
    level2Count = len(tree.nodesAtLevel(2))
    level3Count = len(tree.nodesAtLevel(3))
    if not 1 <= level1Count <= 3:
        raise ConditionError(f'venn: レベル1は1個以上3個以下である必要がある（{level1Count}個ある）')
    if level2Count > 3:
        raise ConditionError(f'venn: レベル2は高々3個である必要がある（{level2Count}個ある）')
    if level3Count > 1:
        raise ConditionError(f'venn: レベル3は高々1個である必要がある（{level3Count}個ある）')

    bodyLines = []
    styleLines = []
    setsSeen = 0
    level2Seen = 0
    for node in nodes:
        name, value = parseVennName(node.text)
        if name == '':
            raise ConditionError(f'venn: line {node.lineNo}: 名称が空である')
        if node.level == 1:
            setsSeen += 1
            region = f'N{setsSeen}'
            line = f'  set {region}["{quoteText(name)}"]'
        else:
            if node.level == 2:
                required = vennLevel2Sets[level2Seen]
                level2Seen += 1
            else:
                required = (1, 2, 3)
            if max(required) > setsSeen:
                needed = '・'.join(f'N{k}' for k in required)
                raise ConditionError(f'venn: line {node.lineNo}: 領域 "{name}" に必要な集合（{needed}）が'
                                     'それより前に出現していない')
            region = ','.join(f'N{k}' for k in required)
            line = f'  union {region}["{quoteText(name)}"]'
        if value is not None:
            line += f':{value}'
        bodyLines.append(line)
        if node.color:
            styleLines.append(f'  style {region} fill:{node.color}')

    out = ['venn-beta'] + bodyLines
    if styleLines:
        out.append('')
        out += styleLines
    return out


# ---------------------------------------------------------------------------
# 8.3 table系
# ---------------------------------------------------------------------------

tableSettings = {
    'table': (None, False), 'tablec': (None, True),
    'table1': (1, False), 'table1c': (1, True),
    'table2': (2, False), 'table2c': (2, True),
    'table3': (3, False), 'table3c': (3, True),
}


def generateTable(tableTree, opts, typeId):
    if not tableTree.roots:
        raise ConditionError(f'{typeId}: ルートが1個以上必要である')
    if tableTree.maxLevel() > 2:
        raise ConditionError(f'{typeId}: レベル3以上の節が存在してはならない')
    boldColumn, centering = tableSettings[typeId]

    # 8.3.0 空セルの置換
    rows = []
    for root in tableTree.roots:
        texts = [root.text] + [child.text for child in root.children]
        rows.append([fullWidthSpace if text.replace(' ', '').replace('\t', '') == '' else text
                     for text in texts])

    columnWidths = {}
    if centering:
        for cells in rows:
            for colIndex, text in enumerate(cells):
                columnWidths[colIndex] = max(columnWidths.get(colIndex, 0), displayWidth(text))

    out = ['@startsalt', '{#']
    for rowIndex, cells in enumerate(rows):
        cellStrings = []
        for colIndex, text in enumerate(cells):
            cellText = text
            # 8.3.1 太字化
            if boldColumn is not None and (rowIndex == 0 or colIndex == boldColumn - 1):
                cellText = f'<b>{cellText}</b>'
            # 8.3.2 センタリング
            if centering:
                padWidth = columnWidths[colIndex] - displayWidth(text)
                spaceCount = padWidth // 2
                leftCount = spaceCount // 2
                rightCount = spaceCount - leftCount
                if colIndex == len(cells) - 1:
                    rightCount = 0
                cellText = fullWidthSpace * leftCount + cellText + fullWidthSpace * rightCount
            cellStrings.append(cellText)
        out.append('| ' + ' | '.join(cellStrings))
    out += ['}', '@endsalt']
    return out


# ---------------------------------------------------------------------------
# 9 quadrant
# ---------------------------------------------------------------------------

def formatHundredths(value):
    """小数第2位までの値（100倍した整数）を 9.1 の表記で返す。"""
    if value % 10 == 0:
        return f'{value // 100}.{(value % 100) // 10}'
    return f'{value // 100}.{value % 100:02d}'


def generateQuadrant(tree, opts):
    roots = tree.roots
    if len(roots) != 2:
        raise ConditionError(f'quadrant: ルートがちょうど2個である必要がある（{len(roots)}個ある）')
    for root in roots:
        if len(root.children) != 2:
            raise ConditionError(f'quadrant: レベル2の節が各ルートにちょうど2個必要である（"{root.text}" の子は'
                                 f'{len(root.children)}個）')
        for child in root.children:
            if not 1 <= len(child.children) <= 9:
                raise ConditionError(f'quadrant: レベル3の節が各レベル2節に1個以上9個以下必要である（"{child.text}" の子は'
                                     f'{len(child.children)}個）')
    if tree.maxLevel() > 3:
        raise ConditionError('quadrant: レベル4以上の節が存在してはならない')

    leftBottom, leftTop = roots[0].children
    rightBottom, rightTop = roots[1].children
    quadrantNodes = {1: rightTop, 2: leftTop, 3: leftBottom, 4: rightBottom}

    out = []
    fills = [(k, quadrantNodes[k].color) for k in (1, 2, 3, 4) if quadrantNodes[k].color]
    if fills:
        out += ['---', 'config:', '  themeVariables:']
        for k, color in fills:
            out.append(f'    quadrant{k}Fill: "{color}"')
        out.append('---')
    out.append('quadrantChart')
    out.append(f'  x-axis "{quoteText(roots[0].text)}" --> "{quoteText(roots[1].text)}"')
    out.append(f'  y-axis "{quoteText(leftBottom.text)}" --> "{quoteText(leftTop.text)}"')
    for k in (1, 2, 3, 4):
        out.append(f'  quadrant-{k} "{quoteText(quadrantNodes[k].children[0].text)}"')
    for rootIndex, root in enumerate(roots):
        xValue = 25 if rootIndex == 0 else 75
        for childIndex, child in enumerate(root.children):
            baseY = 40 if childIndex == 0 else 90
            for pointIndex, point in enumerate(child.children[1:], start=1):
                yValue = baseY - 5 * (pointIndex - 1)
                out.append(f'  "{quoteText(point.text)}": [{formatHundredths(xValue)}, '
                           f'{formatHundredths(yValue)}] radius:0')
    return out


# ---------------------------------------------------------------------------
# 10.5〜10.6 struct-flow
# ---------------------------------------------------------------------------

def generateStructFlow(tree, opts):
    roots = tree.roots
    if not roots:
        raise ConditionError('struct-flow: ルートが1個以上必要である')
    layout = opts.layout
    maxDepth = tree.maxLevel()
    tightCoords, tightTotal = tightLevelCoords(tree, maxDepth)
    if layout == 'tight':
        colOfLevel = lambda level: tightCoords[level]
        width = tightTotal
    elif layout in ('spacyX', 'spacyXY'):
        colOfLevel = lambda level: 3 * level - 2
        width = 3 * maxDepth - 2
    else:
        colOfLevel = lambda level: 2 * level - 1
        width = 2 * maxDepth - 1
    isSpacyY = layout in ('spacyY', 'spacyXY')

    groups = []
    for root in roots:
        rows = []

        def place(node, sameRow):
            if not sameRow:
                rows.append({})
            rows[-1][colOfLevel(node.level)] = mermaidNodeDef(node)
            for childIndex, child in enumerate(node.children):
                place(child, childIndex == 0)

        place(root, False)
        groups.append(rows)

    out = []
    if layout == 'spacyPadding':
        out += blockPaddingFrontmatter
    out += ['block', f'columns {width}']
    blankRow = spaceToken(width)
    for groupIndex, rows in enumerate(groups):
        if groupIndex > 0:
            out.append('')
            if isSpacyY:
                out.append(blankRow)
        for rowIndex, cells in enumerate(rows):
            if rowIndex > 0 and isSpacyY:
                out.append(blankRow)
            out.append(renderGridRow(cells, width))

    def subtreeLines(node):
        result = []
        for childIndex, child in enumerate(node.children):
            if child.label or childIndex == 0:
                source = node
            else:
                source = node.children[childIndex - 1]
            result.append(blockEdge(source.nodeId, child.nodeId, child.lineType or opts.line, child.label, False))
            result += subtreeLines(child)
        return result

    segments = [subtreeLines(roots[0])]
    for rootIndex in range(1, len(roots)):
        previous, current = roots[rootIndex - 1], roots[rootIndex]
        segment = [blockEdge(previous.nodeId, current.nodeId, current.lineType or opts.line, None, False)]
        segment += subtreeLines(current)
        segments.append(segment)
    segments = [segment for segment in segments if segment]
    if segments:
        out.append('')
        for segmentIndex, segment in enumerate(segments):
            if segmentIndex > 0:
                out.append('')
            out += segment

    styles = mermaidStyleLines(tree.allNodes())
    if styles:
        out.append('')
        out += styles
    return out


# ---------------------------------------------------------------------------
# 10.8〜10.10 star
# ---------------------------------------------------------------------------

def estimateBlockSize(node):
    """ブロックの推定寸法（10.9.3）。"""
    textWidth = textPixelWidth(node.text)
    shape = node.shape or 'rect'
    if shape == 'cyl':
        return textWidth + 6, 43 + 0.18 * textWidth
    if shape == 'circle':
        diameter = math.hypot(textWidth, labelHeight) + 6
        return diameter, diameter
    if shape == 'dbl-circ':
        diameter = math.hypot(textWidth, labelHeight) + 24
        return diameter, diameter
    if shape == 'diam':
        return textWidth + 38, textWidth + 38
    return textWidth + blockPaddingX, blockHeight


def roundHalfAway(value):
    if value == 0:
        return 0
    sign = 1 if value > 0 else -1
    return sign * math.floor(abs(value) + 0.5)


class StarGeometry:
    """star の配置計算に用いる寸法一式。"""

    def __init__(self, root, opts):
        self.span = opts.spanValue
        self.degree = opts.degreeValue
        (self.minLineLength, self.labelMargin,
         self.minBlockGap, self.cellGap) = starLayoutValues[opts.layout]
        peripherals = root.children
        self.count = len(peripherals)
        sizes = [estimateBlockSize(node) for node in [root] + peripherals]
        naturalWidth = opts.blockWidthValue if opts.blockWidthValue is not None else max(w for w, _ in sizes)
        self.cellHeight = max(h for _, h in sizes)
        columnWidth = naturalWidth / self.span
        self.colPitch = columnWidth + self.cellGap
        self.rowPitch = self.cellHeight + self.cellGap
        self.drawnWidth = columnWidth * self.span + self.cellGap * (self.span - 1)
        self.needs = []
        for node in peripherals:
            if node.label:
                needX = textPixelWidth(node.label) + labelPaddingX + 2 * self.labelMargin
                needY = labelHeight + 2 * self.labelMargin
            else:
                needX = needY = self.minLineLength
            self.needs.append((needX, needY))

    def gapX(self, cellA, cellB):
        return abs(cellA[0] - cellB[0]) * self.colPitch - self.drawnWidth

    def gapY(self, cellA, cellB):
        return abs(cellA[1] - cellB[1]) * self.rowPitch - self.cellHeight

    def cellsForRadius(self, radius):
        cells = []
        for index in range(self.count):
            theta = math.radians(self.degree + 360 * index / self.count)
            xValue = radius * math.sin(theta)
            yValue = -radius * math.cos(theta)
            cells.append((roundHalfAway(xValue / self.colPitch), roundHalfAway(yValue / self.rowPitch)))
        return cells

    def isValid(self, cells):
        center = (0, 0)
        for index, cell in enumerate(cells):
            needX, needY = self.needs[index]
            if not (self.gapX(center, cell) >= needX or self.gapY(center, cell) >= needY):
                return False
        for i in range(len(cells)):
            for j in range(i + 1, len(cells)):
                if not (self.gapX(cells[i], cells[j]) >= self.minBlockGap
                        or self.gapY(cells[i], cells[j]) >= self.minBlockGap):
                    return False
        return True

    def distortion(self, cells):
        step = 360 / self.count
        maxDelta = 0.0
        distances = []
        for index, (col, row) in enumerate(cells):
            xPos = col * self.colPitch
            yPos = row * self.rowPitch
            actualAngle = math.degrees(math.atan2(xPos, -yPos)) % 360
            targetAngle = (self.degree + step * index) % 360
            diff = abs(actualAngle - targetAngle) % 360
            maxDelta = max(maxDelta, min(diff, 360 - diff))
            distances.append(math.hypot(xPos, yPos))
        meanDistance = sum(distances) / len(distances)
        return angleWeight * maxDelta / step + (max(distances) - min(distances)) / meanDistance


def searchStarCells(geometry, radiusOption):
    """半径の探索（10.9.10）。有効な配置のセル座標リストを返す。"""
    if radiusOption is not None:
        cells = geometry.cellsForRadius(radiusOption)
        if not geometry.isValid(cells):
            raise ConditionError(f'star: --radius {radiusOption:g} では周辺ブロックや線ラベルが重なる')
        return cells
    radiusStep = min(geometry.colPitch, geometry.rowPitch) / 8
    firstRadius = None
    bestCells = None
    bestScore = None
    k = 0
    while True:
        radius = geometry.rowPitch + k * radiusStep
        if radius > geometry.rowPitch * 1000:
            raise ConditionError('star: 有効な配置が見つからない')
        cells = geometry.cellsForRadius(radius)
        if geometry.isValid(cells):
            if firstRadius is None:
                firstRadius = radius
            score = geometry.distortion(cells) + sizePenalty * (radius / firstRadius - 1)
            if bestCells is None or score < bestScore - 1e-9:
                bestCells = cells
                bestScore = score
        if firstRadius is not None and radius > firstRadius * searchRange:
            return bestCells
        k += 1


def generateStar(tree, opts):
    root = requireSingleRoot(tree, 'star')
    if not root.children:
        raise ConditionError('star: レベル2の節が1個以上必要である')
    if tree.maxLevel() > 2:
        raise ConditionError('star: レベル3以上の節が存在してはならない')

    geometry = StarGeometry(root, opts)
    cells = searchStarCells(geometry, opts.radiusValue)
    span = geometry.span
    spanSuffix = f':{span}' if span >= 2 else ''

    placed = [(0, 0, root)] + [(col, row, node) for (col, row), node in zip(cells, root.children)]
    minCol = min(col for col, _, _ in placed)
    endCol = max(col for col, _, _ in placed) + span
    width = endCol - minCol
    minRow = min(row for _, row, _ in placed)
    maxRow = max(row for _, row, _ in placed)

    out = []
    if opts.layout == 'spacyPadding':
        out += blockPaddingFrontmatter
    out += ['block', f'columns {width}']
    for row in range(minRow, maxRow + 1):
        rowBlocks = sorted(((col, node) for col, r, node in placed if r == row), key=lambda item: item[0])
        parts = []
        cursor = minCol
        for col, node in rowBlocks:
            if col > cursor:
                parts.append(spaceToken(col - cursor))
            parts.append(mermaidNodeDef(node) + spanSuffix)
            cursor = col + span
        if endCol > cursor:
            parts.append(spaceToken(endCol - cursor))
        out.append(' '.join(parts))

    reverse = opts.arrowDirection == 'reverse'
    out.append('')
    for node in root.children:
        out.append(blockEdge(root.nodeId, node.nodeId, node.lineType or opts.line, node.label, reverse))

    styles = mermaidStyleLines([root] + root.children)
    if styles:
        out.append('')
        out += styles
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def buildArgumentParser():
    parser = argparse.ArgumentParser(
        prog='heading2diagram.py',
        description='見出し形式Markdownからダイアグラム定義（PlantUML / Mermaid）を生成する。')
    parser.add_argument('input', metavar='INPUT.md', help='見出し形式の入力ファイルパス')
    parser.add_argument('-o', '--output', metavar='OUTPUT.md', help='出力ファイルパス（省略時は標準出力）')
    parser.add_argument('-t', '--type', dest='types', metavar='TYPE', nargs='+', action='extend',
                        choices=typeIdList, help='生成する図種ID（複数指定可）: ' + ', '.join(typeIdList))
    parser.add_argument('--direction', choices=directionChoices, default=None)
    parser.add_argument('--layout', choices=layoutChoices, default=None)
    parser.add_argument('--line', choices=lineChoices, default=None)
    parser.add_argument('--arrowDirection', choices=arrowDirectionChoices, default=None)
    parser.add_argument('--curve', choices=curveChoices, default=None)
    parser.add_argument('--degree', default=None)
    parser.add_argument('--span', default=None)
    parser.add_argument('--radius', default=None)
    parser.add_argument('--blockWidth', default=None)
    return parser


def parseFiniteFloat(text):
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


class Options:
    """既定値を適用した実効オプションと、明示指定されたオプション文字列。"""

    def __init__(self, args, parser):
        self.givenOptions = {}
        for name in ('direction', 'layout', 'line', 'arrowDirection', 'curve',
                     'degree', 'span', 'radius', 'blockWidth'):
            value = getattr(args, name)
            if value is not None:
                self.givenOptions[name] = value
        self.direction = args.direction or 'TB'
        self.layout = args.layout or 'normal'
        self.line = args.line or 'solid'
        self.arrowDirection = args.arrowDirection or 'default'
        self.curve = args.curve or 'default'

        self.degreeValue = 0.0
        if args.degree is not None:
            self.degreeValue = parseFiniteFloat(args.degree)
            if self.degreeValue is None:
                parser.error(f'argument --degree: 数値でない値である: {args.degree!r}')
        self.spanValue = 4
        if args.span is not None:
            try:
                self.spanValue = int(args.span)
            except ValueError:
                parser.error(f'argument --span: 1以上の整数を指定すること: {args.span!r}')
            if self.spanValue < 1:
                parser.error(f'argument --span: 1以上の整数を指定すること: {args.span!r}')
        self.radiusValue = None
        if args.radius is not None:
            self.radiusValue = parseFiniteFloat(args.radius)
            if self.radiusValue is None or self.radiusValue <= 0:
                parser.error(f'argument --radius: 正の数を指定すること: {args.radius!r}')
        self.blockWidthValue = None
        if args.blockWidth is not None:
            self.blockWidthValue = parseFiniteFloat(args.blockWidth)
            if self.blockWidthValue is None or self.blockWidthValue <= 0:
                parser.error(f'argument --blockWidth: 正の数を指定すること: {args.blockWidth!r}')

    def headingFor(self, typeId):
        parts = [f'--{name} {self.givenOptions[name]}'
                 for name in headingOptions.get(typeId, []) if name in self.givenOptions]
        return f'## {typeId}' + (f' ({" ".join(parts)})' if parts else '')


def generateDiagram(typeId, trees, opts):
    normalTree, tableTree = trees
    if typeId in tableTypeIds:
        return generateTable(tableTree(), opts, typeId)
    tree = normalTree()
    if typeId == 'hier-mind':
        return generateMindmap(tree, opts, typeId, withLabel=False)
    if typeId == 'hier-mindlabel':
        return generateMindmap(tree, opts, typeId, withLabel=True)
    generators = {
        'hier-block': generateHierBlock,
        'hier-flow': generateHierFlow,
        'fishBone': generateFishBone,
        'pie': generatePie,
        'venn': generateVenn,
        'struct-flow': generateStructFlow,
        'quadrant': generateQuadrant,
        'star': generateStar,
    }
    return generators[typeId](tree, opts)


def readInputLines(path):
    try:
        with open(path, encoding='utf-8-sig', newline=None) as inputFile:
            return inputFile.read().split('\n')
    except FileNotFoundError:
        raise InputError(f'入力ファイルが存在しない: {path}')
    except UnicodeDecodeError:
        raise InputError(f'入力ファイルをUTF-8として復号できない: {path}')
    except OSError as exc:
        raise InputError(f'入力ファイルを読めない: {path} ({exc.strerror})')


def run(argv):
    parser = buildArgumentParser()
    args = parser.parse_args(argv)
    opts = Options(args, parser)

    lines = readInputLines(args.input)
    records = parseLines(lines)
    if not any(not record.isEmpty for record in records):
        raise InputError('有効な見出し行（テキストが空でない見出し行）が1行も無い')

    explicit = bool(args.types)
    if explicit:
        targetTypes = list(dict.fromkeys(args.types))
    else:
        targetTypes = list(defaultTypeIds)

    # 内容が空の見出し行の警告（table系以外の図種が生成対象に含まれる場合のみ）
    if any(typeId not in tableTypeIds for typeId in targetTypes):
        for record in records:
            if record.isEmpty:
                reporter.warn(f'line {record.lineNo}: 内容（テキスト）が空の見出し行である。'
                              'table系以外の図種では無視し、table系では空セルとして扱う')

    # 木は必要になった時点で構築する
    cache = {}

    def normalTree():
        if 'normal' not in cache:
            cache['normal'] = buildTree(records, includeEmpty=False)
        return cache['normal']

    def tableTree():
        if 'table' not in cache:
            cache['table'] = buildTree(records, includeEmpty=True)
        return cache['table']

    trees = (normalTree, tableTree)
    blocks = []
    errors = []
    for typeId in targetTypes:
        actualType = typeId
        if typeId == 'hier-mind' and any(node.label for node in normalTree().allNodes()):
            if explicit:
                reporter.warn('hier-mind: 入力にラベルが含まれるため hier-mindlabel として生成する')
            actualType = 'hier-mindlabel'
        try:
            body = generateDiagram(actualType, trees, opts)
        except ConditionError as exc:
            if explicit:
                errors.append(f'入力条件違反: {exc}')
            else:
                reporter.warn(f'入力条件違反のためスキップする: {exc}')
            continue
        fence = 'plantuml' if actualType in plantumlTypeIds else 'mermaid'
        # 見出しのオプションは指定された図種（hier-mind）の定義で決める
        heading = opts.headingFor(typeId).replace(f'## {typeId}', f'## {actualType}', 1)
        blocks.append('\n'.join([heading, '```' + fence] + body + ['```']))

    if errors:
        for message in errors:
            Reporter.error(message)
        return 1
    if not blocks:
        raise InputError('生成できた図種が1つも無い')

    outputText = '\n\n'.join(blocks) + '\n'
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8', newline='\n') as outputFile:
                outputFile.write(outputText)
        except OSError as exc:
            raise InputError(f'出力ファイルへ書き込めない: {args.output} ({exc.strerror})')
    else:
        sys.stdout.buffer.write(outputText.encode('utf-8'))
        sys.stdout.flush()
    return 0


def main():
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass
    try:
        exitCode = run(sys.argv[1:])
    except InputError as exc:
        Reporter.error(str(exc))
        exitCode = 1
    sys.exit(exitCode)


if __name__ == '__main__':
    main()
