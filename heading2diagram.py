#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""heading2diagram: 見出し形式Markdownからダイアグラム定義を生成するCLIプログラム.

Markdownの見出し（# 〜）だけで記述された階層データを読み込み、
PlantUML（mindmap / salt）および Mermaid（flowchart / block / ishikawa /
pie / venn / quadrantChart）のダイアグラム定義（テキスト）を生成する。
標準ライブラリのみを使用する（Python 3.10以上）。
"""

import argparse
import re
import sys
import unicodedata

# ---------------------------------------------------------------------------
# 定数（図種・オプション・記法の対応表）
# ---------------------------------------------------------------------------

typeIdList = [
    'hier-mind', 'hier-mindlabel', 'hier-block', 'hier-flow', 'fishBone',
    'pie', 'venn', 'table', 'tablec', 'table1', 'table1c', 'table2',
    'table2c', 'table3', 'table3c', 'struct-flow', 'quadrant',
]
tableTypeIds = ['table', 'tablec', 'table1', 'table1c', 'table2', 'table2c',
                'table3', 'table3c']
plantumlTypeIds = {'hier-mind', 'hier-mindlabel'} | set(tableTypeIds)

directionChoices = ['TB', 'TD', 'BT', 'LR', 'RL']
layoutChoices = ['tight', 'normal', 'spacyX', 'spacyY', 'spacyXY', 'spacyPadding']
lineChoices = ['dotted', 'solid', 'thick', 'dottedArrow', 'solidArrow', 'thickArrow']
arrowDirectionChoices = ['default', 'reverse']
curveChoices = ['default', 'linear', 'bumpX', 'bumpY', 'cardinal', 'catmullRom',
                'monotoneX', 'monotoneY', 'natural', 'step']

# 見出し行に含めるオプション（図種ごと・この順）
optionOrder = ['direction', 'layout', 'line', 'arrowDirection', 'curve']
optionFlags = {
    'direction': '--direction', 'layout': '--layout', 'line': '--line',
    'arrowDirection': '--arrowDirection', 'curve': '--curve',
}
meaningfulOptions = {
    'hier-mind': ['direction', 'layout', 'line'],
    'hier-mindlabel': ['direction', 'layout', 'line'],
    'hier-block': ['direction', 'layout', 'line', 'arrowDirection'],
    'hier-flow': ['direction', 'layout', 'line', 'arrowDirection', 'curve'],
    'struct-flow': ['layout', 'line'],
}

lineStyleNames = {
    '実線': 'solid', 'solid': 'solid',
    '点線': 'dotted', 'dotted': 'dotted',
    '太線': 'thick', 'thick': 'thick',
    '実線矢印': 'solidArrow', 'solidArrow': 'solidArrow',
    '点線矢印': 'dottedArrow', 'dottedArrow': 'dottedArrow',
    '太線矢印': 'thickArrow', 'thickArrow': 'thickArrow',
}

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

# Mermaid の形状記法（開き括弧, 閉じ括弧）
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

headingRe = re.compile(r'(#+)(?:[ \t]+(.*))?')
headingTypoRe = re.compile(r'#+[^ \t#]')
colorRe = re.compile(r'(.*):(#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3}))', re.S)
badColorRe = re.compile(r':#\S*$')
modifierRe = re.compile(r'([^ \t;]*);')
numberRe = re.compile(r'[0-9]+(\.[0-9]+)?')

fullWidthSpace = '\u3000'


# ---------------------------------------------------------------------------
# 入出力・診断
# ---------------------------------------------------------------------------

def writeStream(stream, text):
    """UTF-8 で文字列をストリームへ書き出す."""
    bufferObj = getattr(stream, 'buffer', None)
    if bufferObj is not None:
        stream.flush()
        bufferObj.write(text.encode('utf-8'))
        bufferObj.flush()
    else:
        stream.write(text)
        stream.flush()


class Diagnostics:
    """警告・エラーを stderr へ出力する（同一の警告は1回のみ）."""

    def __init__(self):
        self.seenWarnings = set()

    def warn(self, message):
        if message in self.seenWarnings:
            return
        self.seenWarnings.add(message)
        writeStream(sys.stderr, 'warning: ' + message + '\n')

    def error(self, message):
        writeStream(sys.stderr, 'error: ' + message + '\n')


class InputError(Exception):
    """入力エラー（終了コード1）."""


# ---------------------------------------------------------------------------
# 入力の解析
# ---------------------------------------------------------------------------

class HeadingEntry:
    """見出し行1行分の解析結果."""

    def __init__(self, lineNo, rawLevel, label, lineStyle, shape, text, color):
        self.lineNo = lineNo
        self.rawLevel = rawLevel
        self.label = label
        self.lineStyle = lineStyle
        self.shape = shape
        self.text = text
        self.color = color

    @property
    def isEmpty(self):
        return self.text == ''


class Node:
    """木構造の節."""

    def __init__(self, entry, level):
        self.entry = entry
        self.level = level
        self.children = []
        self.parent = None
        self.nodeId = ''

    label = property(lambda self: self.entry.label)
    lineStyle = property(lambda self: self.entry.lineStyle)
    shape = property(lambda self: self.entry.shape)
    text = property(lambda self: self.entry.text)
    color = property(lambda self: self.entry.color)
    lineNo = property(lambda self: self.entry.lineNo)


def parseContent(content, lineNo, diag):
    """見出し行の内容をラベル・修飾・テキスト・色に分解する（4.1）."""
    rest = content.rstrip(' \t')
    label = None

    # 1. ラベル
    if rest.startswith('|'):
        closeIndex = rest.find('|', 1)
        if closeIndex < 0:
            diag.warn(f'{lineNo}行目: ラベルの閉じ "|" が無いため、"|" を含めて内容全体をテキストとして扱う')
        else:
            labelText = rest[1:closeIndex].strip(' \t')
            if labelText == '':
                diag.warn(f'{lineNo}行目: ラベルが空（||）のため、ラベル無しとして扱う')
            else:
                label = labelText
            rest = rest[closeIndex + 1:].lstrip(' \t')

    # 2. 色
    color = None
    colorMatch = colorRe.fullmatch(rest)
    if colorMatch:
        rest = colorMatch.group(1)
        color = colorMatch.group(2)
    elif badColorRe.search(rest):
        diag.warn(f'{lineNo}行目: 色の指定 ":#..." が16進3桁または6桁ではない（書き間違いの可能性）。テキストの一部として扱う')

    # 3. 修飾（線種名・形状名）
    lineStyle = None
    shape = None
    for _ in range(2):
        modifierMatch = modifierRe.match(rest)
        if not modifierMatch:
            break
        name = modifierMatch.group(1)
        if name in lineStyleNames:
            if lineStyle is not None:
                diag.warn(f'{lineNo}行目: 線種名が2回指定されている。"{name};" はテキストの一部として扱う')
                break
            lineStyle = lineStyleNames[name]
        elif name in shapeNames:
            if shape is not None:
                diag.warn(f'{lineNo}行目: 形状名が2回指定されている。"{name};" はテキストの一部として扱う')
                break
            shape = shapeNames[name]
        else:
            diag.warn(f'{lineNo}行目: "{name};" は既知の線種名・形状名ではない（書き間違いの可能性）。テキストの一部として扱う')
            break
        rest = rest[modifierMatch.end():].lstrip(' \t')

    # 4. テキスト
    text = rest.strip(' \t')
    return label, lineStyle, shape, text, color


def parseInput(sourceText, diag):
    """入力全体を解析し、見出し行のリストを返す."""
    entries = []
    for index, rawLine in enumerate(sourceText.split('\n')):
        lineNo = index + 1
        line = rawLine.rstrip('\r')
        if line.strip(' \t') == '':
            continue
        headingMatch = headingRe.fullmatch(line)
        if headingMatch is None:
            if headingTypoRe.match(line):
                diag.warn(f'{lineNo}行目: "#" の直後に空白が無い（見出し行の書き間違いの可能性）。この行を無視する')
            else:
                diag.warn(f'{lineNo}行目: 見出し行でも空行でもない行を無視する')
            continue
        rawLevel = len(headingMatch.group(1))
        content = headingMatch.group(2) or ''
        label, lineStyle, shape, text, color = parseContent(content, lineNo, diag)
        entries.append(HeadingEntry(lineNo, rawLevel, label, lineStyle, shape, text, color))
    return entries


def assignNodeIds(roots):
    """ノードID（5.1）を付与する."""
    def assign(node, nodeId):
        node.nodeId = nodeId
        for childIndex, child in enumerate(node.children, start=1):
            assign(child, f'{nodeId}_{childIndex}')

    for rootIndex, root in enumerate(roots, start=1):
        assign(root, f'N{rootIndex}')


def buildTree(entries, includeEmpty, diag):
    """見出し行のリストから木構造を構築する（4.2）."""
    roots = []
    stack = []
    prevLevel = 0
    for entry in entries:
        if entry.isEmpty and not includeEmpty:
            continue
        level = entry.rawLevel
        if level > prevLevel + 1:
            effectiveLevel = prevLevel + 1
            if prevLevel == 0:
                diag.warn(f'{entry.lineNo}行目: 先頭の見出し行のレベルが{level}である（レベル飛び）。ルート（レベル1）として扱う')
            else:
                diag.warn(f'{entry.lineNo}行目: レベル飛び（直前の見出し行のレベル{prevLevel}に対してレベル{level}）。'
                          f'直前の見出し行の節の子（レベル{effectiveLevel}）として扱う')
        else:
            effectiveLevel = level
        node = Node(entry, effectiveLevel)
        del stack[effectiveLevel - 1:]
        if effectiveLevel == 1:
            roots.append(node)
        else:
            parent = stack[-1]
            parent.children.append(node)
            node.parent = parent
        stack.append(node)
        prevLevel = effectiveLevel
    assignNodeIds(roots)
    return roots


def walkDepthFirst(roots):
    """深さ優先（出現順）で全節を列挙する."""
    result = []

    def visit(node):
        result.append(node)
        for child in node.children:
            visit(child)

    for root in roots:
        visit(root)
    return result


def walkBreadthFirst(root):
    """幅優先で親子の組を列挙する（10.4）."""
    pairs = []
    queue = [root]
    queueIndex = 0
    while queueIndex < len(queue):
        parent = queue[queueIndex]
        queueIndex += 1
        for child in parent.children:
            pairs.append((parent, child))
            queue.append(child)
    return pairs


# ---------------------------------------------------------------------------
# 共通ヘルパー
# ---------------------------------------------------------------------------

def quoteText(text):
    """Mermaid 用に " を #quot; へ置換する（5.2）."""
    return text.replace('"', '#quot;')


def shapeDefinition(node):
    """Mermaid のノード定義（4.3）."""
    openBracket, closeBracket = shapeBrackets[node.shape or 'rect']
    return f'{node.nodeId}{openBracket}"{quoteText(node.text)}"{closeBracket}'


def styleLines(nodes):
    """色・無枠の style 行（6章冒頭の共通規則）."""
    lines = []
    for node in nodes:
        if node.shape == 'borderless':
            if node.color:
                lines.append(f'style {node.nodeId} fill:{node.color},stroke:none')
            else:
                lines.append(f'style {node.nodeId} fill:none,stroke:none')
        elif node.color:
            lines.append(f'style {node.nodeId} fill:{node.color}')
    return lines


def spaceToken(count):
    return 'space' if count == 1 else f'space:{count}'


def renderGridRow(cells):
    """グリッド1行分を出力文字列にする（10.1）."""
    parts = []
    emptyRun = 0
    for cell in cells:
        if cell is None:
            emptyRun += 1
        else:
            if emptyRun:
                parts.append(spaceToken(emptyRun))
                emptyRun = 0
            parts.append(cell)
    if emptyRun:
        parts.append(spaceToken(emptyRun))
    return ' '.join(parts)


def tightCoordinates(nodes, maxLevel):
    """tight 時のレベル座標 t(L) と T を求める（10.1）."""
    gapFlags = {level: 0 for level in range(1, maxLevel)}
    for node in nodes:
        if node.level >= 2 and node.label:
            gapFlags[node.level - 1] = 1
    levelCoord = {1: 1}
    for level in range(1, maxLevel):
        levelCoord[level + 1] = levelCoord[level] + 1 + gapFlags[level]
    return levelCoord, levelCoord[maxLevel]


def blockEdge(parentId, childId, lineStyle, label, reverse):
    """block の線（5.3, 5.4）."""
    symbol = blockSymbols[lineStyle]
    if reverse and lineStyle in blockReverseSymbols:
        symbol = blockReverseSymbols[lineStyle]
    if label:
        return f'{parentId} -- "{quoteText(label)}" {symbol} {childId}'
    return f'{parentId} {symbol} {childId}'


def displayWidth(text):
    """表示幅（8.3.2）."""
    return sum(2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1 for ch in text)


def parsePieText(text):
    """pie のスライス「名称:数値」を分解する。不適合なら None."""
    if ':' not in text:
        return None
    name, value = text.rsplit(':', 1)
    name = name.strip(' \t')
    value = value.strip(' \t')
    if name == '' or not numberRe.fullmatch(value):
        return None
    return name, value


def parseVennText(text):
    """venn の「名称[:数値]」を分解する."""
    if ':' in text:
        name, value = text.rsplit(':', 1)
        value = value.strip(' \t')
        if numberRe.fullmatch(value):
            return name.strip(' \t'), value
    return text.strip(' \t'), None


def formatCoordinate(hundredths):
    """quadrant の座標表記（9.1）."""
    if hundredths % 10 == 0:
        return f'{hundredths / 100:.1f}'
    return f'{hundredths / 100:.2f}'


# ---------------------------------------------------------------------------
# 入力条件（4.4）
# ---------------------------------------------------------------------------

def checkCondition(typeId, mainRoots, tableRoots):
    """入力条件を判定し、違反があれば違反内容の文字列を返す."""
    if typeId.startswith('hier-') or typeId == 'fishBone':
        if len(mainRoots) != 1:
            return f'ルートがちょうど1個であること（ルートが{len(mainRoots)}個ある）'
        return None

    if typeId in tableTypeIds:
        if len(tableRoots) < 1:
            return 'ルートが1個以上であること'
        if max(n.level for n in walkDepthFirst(tableRoots)) > 2:
            return 'レベルが2以下であること（レベル3以上の節が存在する）'
        return None

    if typeId == 'struct-flow':
        if len(mainRoots) < 1:
            return 'ルートが1個以上であること'
        return None

    nodes = walkDepthFirst(mainRoots)

    if typeId == 'pie':
        if len(mainRoots) != 1:
            return f'ルートがちょうど1個であること（ルートが{len(mainRoots)}個ある）'
        slices = [n for n in nodes if n.level == 2]
        if not slices:
            return 'レベル2の節が1個以上であること'
        if any(n.level >= 3 for n in nodes):
            return 'レベル3以上の節が存在しないこと'
        for node in slices:
            if parsePieText(node.text) is None:
                return f'レベル2の節が「名称:数値」形式であること（{node.lineNo}行目 "{node.text}"）'
        return None

    if typeId == 'venn':
        if any(n.level > 3 for n in nodes):
            return 'レベルが3以下であること（レベル4以上の節が存在する）'
        level1Count = sum(1 for n in nodes if n.level == 1)
        level2Count = sum(1 for n in nodes if n.level == 2)
        level3Count = sum(1 for n in nodes if n.level == 3)
        if not 1 <= level1Count <= 3:
            return f'レベル1の節が1個以上3個以下であること（{level1Count}個ある）'
        if level2Count > 3:
            return f'レベル2の節が高々3個であること（{level2Count}個ある）'
        if level3Count > 1:
            return f'レベル3の節が高々1個であること（{level3Count}個ある）'
        seenSets = 0
        seenLevel2 = 0
        requiredForLevel2 = [2, 3, 3]
        for node in nodes:
            name, _ = parseVennText(node.text)
            if name == '':
                return f'全節の名称が空でないこと（{node.lineNo}行目）'
            if node.level == 1:
                seenSets += 1
            elif node.level == 2:
                seenLevel2 += 1
                if seenSets < requiredForLevel2[seenLevel2 - 1]:
                    return (f'対応集合の出現（{node.lineNo}行目の{seenLevel2}番目のレベル2の領域に必要な集合が'
                            f'それより前に出現していない）')
            else:
                if seenSets < 3:
                    return f'対応集合の出現（{node.lineNo}行目のレベル3の領域に必要な集合 N1・N2・N3 がそれより前に出現していない）'
        return None

    if typeId == 'quadrant':
        if len(mainRoots) != 2:
            return f'ルートがちょうど2個であること（ルートが{len(mainRoots)}個ある）'
        if any(n.level >= 4 for n in nodes):
            return 'レベル4以上の節が存在しないこと'
        for root in mainRoots:
            if len(root.children) != 2:
                return f'レベル2の節が各ルートにちょうど2個であること（{root.lineNo}行目のルートに{len(root.children)}個ある）'
            for child in root.children:
                if not 1 <= len(child.children) <= 9:
                    return (f'レベル3の節が各レベル2節に1個以上9個以下であること'
                            f'（{child.lineNo}行目の節に{len(child.children)}個ある）')
        return None

    return None


# ---------------------------------------------------------------------------
# 図種別の生成
# ---------------------------------------------------------------------------

def generateMindmap(roots, options, labelMode, typeId, diag):
    """hier-mind / hier-mindlabel（6.1, 6.2）."""
    root = roots[0]
    nodes = walkDepthFirst(roots)

    if any(n.shape not in (None, 'borderless', 'rounded') for n in nodes):
        diag.warn(f'{typeId}: PlantUML mindmapでは枠の形状を表現できない（「無枠」「角丸」以外の形状指定を無視する）')
    if any(n.lineStyle for n in nodes):
        diag.warn(f'{typeId}: PlantUML mindmapでは節ごとの線種を変更できない（線種名指定を無視する）')

    direction = options['direction']
    if direction == 'BT':
        diag.warn(f'{typeId}: PlantUML mindmapでは方向 BT はサポートされていないため、TB として扱う')
        direction = 'TB'
    directionLine = {
        'TB': 'top to bottom direction', 'TD': 'top to bottom direction',
        'LR': 'left to right direction', 'RL': 'right to left direction',
    }[direction]

    lineStyle = options['line']
    if lineStyle.endswith('Arrow'):
        plainStyle = lineStyle[:-len('Arrow')]
        diag.warn(f'{typeId}: PlantUML mindmapでは矢印を付けられないため、--line {lineStyle} を {plainStyle} として扱う')
        lineStyle = plainStyle

    layout = options['layout']
    if layout == 'tight':
        padding, margin = 3, 2
    elif layout == 'normal':
        padding, margin = 3, 5
    else:
        padding, margin = 5, 10

    out = ['@startmindmap', '<style>', 'mindmapDiagram {',
           '  node {', '    RoundCorner 0', f'    Padding {padding}', f'    Margin {margin}', '  }']
    for node in nodes:
        isRounded = node.shape == 'rounded'
        if node.color or isRounded:
            out.append(f'  .{node.nodeId}Node {{')
            if isRounded:
                out.append('    RoundCorner 8')
            if node.color:
                out.append(f'    BackgroundColor {node.color}')
            out.append('  }')
    if lineStyle == 'dotted':
        out += ['  arrow {', '    LineStyle 2-2', '  }']
    elif lineStyle == 'thick':
        out += ['  arrow {', '    LineThickness 4', '  }']
    out += ['}', '</style>', directionLine]

    if labelMode and root.label:
        diag.warn(f'{typeId}: {root.lineNo}行目: ルートのラベル "{root.label}" は無視する')

    isVertical = direction in ('TB', 'TD')
    if lineStyle == 'dotted':
        alternativeLabel = ':' if isVertical else '\u2026'
    else:
        alternativeLabel = '|' if isVertical else '-'

    def nodeLine(node, depth):
        marker = '*' * depth + ('_' if node.shape == 'borderless' else '')
        suffix = f' <<{node.nodeId}Node>>' if (node.color or node.shape == 'rounded') else ''
        return f'{marker} {node.text}{suffix}'

    def emit(node, depth):
        out.append(nodeLine(node, depth))
        groupHasLabel = labelMode and any(child.label for child in node.children)
        for child in node.children:
            if groupHasLabel:
                out.append('*' * (depth + 1) + '_ ' + (child.label or alternativeLabel))
                emit(child, depth + 2)
            else:
                emit(child, depth + 1)

    emit(root, 1)
    out.append('@endmindmap')
    return '\n'.join(out)


def generateFlowchart(roots, options):
    """hier-flow（6.3）."""
    root = roots[0]
    direction = options['direction']
    reverse = options['arrowDirection'] == 'reverse'
    isVertical = direction in ('TB', 'TD', 'BT')

    padding, nodeSpacing, rankSpacing = 8, 30, 30
    layout = options['layout']
    if layout == 'tight':
        nodeSpacing = rankSpacing = 15
    elif layout == 'spacyXY':
        nodeSpacing = rankSpacing = 50
    elif layout == 'spacyX':
        if isVertical:
            nodeSpacing = 50
        else:
            rankSpacing = 50
    elif layout == 'spacyY':
        if isVertical:
            rankSpacing = 50
        else:
            nodeSpacing = 50
    elif layout == 'spacyPadding':
        padding = 16

    out = ['---', 'config:', '  flowchart:', f'    padding: {padding}',
           f'    nodeSpacing: {nodeSpacing}', f'    rankSpacing: {rankSpacing}',
           '    diagramPadding: 5', '---']
    if options['curve'] != 'default':
        out.append('%%{init:{"flowchart":{"curve":"' + options['curve'] + '"}}}%%')
    out.append('flowchart ' + (reverseDirection[direction] if reverse else direction))

    definedIds = set()

    def reference(node):
        if node.nodeId in definedIds:
            return node.nodeId
        definedIds.add(node.nodeId)
        return shapeDefinition(node)

    pairs = walkBreadthFirst(root)
    if not pairs:
        out.append(reference(root))
    for parent, child in pairs:
        symbol = flowSymbols[child.lineStyle or options['line']]
        labelPart = f'|"{quoteText(child.label)}"|' if child.label else ''
        if reverse:
            leftText = reference(child)
            rightText = reference(parent)
        else:
            leftText = reference(parent)
            rightText = reference(child)
        if labelPart:
            out.append(f'{leftText} {symbol} {labelPart}{rightText}')
        else:
            out.append(f'{leftText} {symbol} {rightText}')

    styles = styleLines(walkDepthFirst(roots))
    if styles:
        out.append('')
        out += styles
    return '\n'.join(out)


def blockFrontmatter():
    return ['---', 'config:', '  block:', '    padding: 30', '---']


def generateHierBlock(roots, options):
    """hier-block（6.4, 10.2〜10.4）."""
    root = roots[0]
    nodes = walkDepthFirst(roots)
    maxLevel = max(n.level for n in nodes)
    layout = options['layout']
    direction = options['direction']
    reverse = options['arrowDirection'] == 'reverse'
    isSpacyX = layout in ('spacyX', 'spacyXY')
    isSpacyY = layout in ('spacyY', 'spacyXY')
    isTight = layout == 'tight'

    # 10.2 位置決定
    positions = {}
    leafCounter = [0]

    def assignPosition(node):
        if not node.children:
            leafCounter[0] += 1
            positions[node.nodeId] = leafCounter[0]
            return
        for child in node.children:
            assignPosition(child)
        childPositions = [positions[c.nodeId] for c in node.children]
        positions[node.nodeId] = (min(childPositions) + max(childPositions)) // 2

    assignPosition(root)
    leafCount = leafCounter[0]
    levelCoord, tightTotal = tightCoordinates(nodes, maxLevel)

    # 10.3 グリッドへの展開
    cellOf = {}
    if direction in ('TB', 'TD', 'BT'):
        width = 2 * leafCount - 1 if isSpacyX else leafCount
        if isTight:
            rowCount = tightTotal
        elif isSpacyY:
            rowCount = 3 * maxLevel - 2
        else:
            rowCount = 2 * maxLevel - 1
        for node in nodes:
            position = positions[node.nodeId]
            column = 2 * position - 1 if isSpacyX else position
            if isTight:
                row = levelCoord[node.level]
            elif isSpacyY:
                row = 3 * node.level - 2
            else:
                row = 2 * node.level - 1
            if direction == 'BT':
                row = rowCount + 1 - row
            cellOf[node.nodeId] = (row, column)
    else:
        if isTight:
            width = tightTotal
        elif isSpacyX:
            width = 3 * maxLevel - 2
        else:
            width = 2 * maxLevel - 1
        rowCount = 2 * leafCount - 1 if isSpacyY else leafCount
        for node in nodes:
            position = positions[node.nodeId]
            if isTight:
                column = levelCoord[node.level]
            elif isSpacyX:
                column = 3 * node.level - 2
            else:
                column = 2 * node.level - 1
            if direction == 'RL':
                column = width + 1 - column
            row = 2 * position - 1 if isSpacyY else position
            cellOf[node.nodeId] = (row, column)

    grid = [[None] * width for _ in range(rowCount)]
    for node in nodes:
        row, column = cellOf[node.nodeId]
        grid[row - 1][column - 1] = shapeDefinition(node)

    out = []
    if layout == 'spacyPadding':
        out += blockFrontmatter()
    out += ['block', f'columns {width}']
    out += [renderGridRow(cells) for cells in grid]

    # 10.4 線の出力順
    edges = [blockEdge(parent.nodeId, child.nodeId, child.lineStyle or options['line'], child.label, reverse)
             for parent, child in walkBreadthFirst(root)]
    if edges:
        out.append('')
        out += edges
    styles = styleLines(nodes)
    if styles:
        out.append('')
        out += styles
    return '\n'.join(out)


def generateStructFlow(roots, options):
    """struct-flow（10.5〜10.6）."""
    nodes = walkDepthFirst(roots)
    maxLevel = max(n.level for n in nodes)
    layout = options['layout']
    isSpacyX = layout in ('spacyX', 'spacyXY')
    isSpacyY = layout in ('spacyY', 'spacyXY')
    levelCoord, tightTotal = tightCoordinates(nodes, maxLevel)

    if layout == 'tight':
        width = tightTotal
    elif isSpacyX:
        width = 3 * maxLevel - 2
    else:
        width = 2 * maxLevel - 1

    def columnOf(node):
        if layout == 'tight':
            return levelCoord[node.level]
        if isSpacyX:
            return 3 * node.level - 2
        return 2 * node.level - 1

    # 行の割り当て（ルートごとのグループ）
    groups = []
    for root in roots:
        groupRows = []

        def place(node, rowIndex):
            if rowIndex is None:
                groupRows.append([None] * width)
                rowIndex = len(groupRows) - 1
            groupRows[rowIndex][columnOf(node) - 1] = shapeDefinition(node)
            for childIndex, child in enumerate(node.children):
                place(child, rowIndex if childIndex == 0 else None)

        place(root, None)
        groups.append([renderGridRow(cells) for cells in groupRows])

    out = []
    if layout == 'spacyPadding':
        out += blockFrontmatter()
    out += ['block', f'columns {width}']
    blankRow = spaceToken(width)
    for groupIndex, groupRows in enumerate(groups):
        if groupIndex > 0:
            out.append('')
            if isSpacyY:
                out.append(blankRow)
        for rowIndex, rowText in enumerate(groupRows):
            if rowIndex > 0 and isSpacyY:
                out.append(blankRow)
            out.append(rowText)

    # 10.6 線
    defaultLine = options['line']

    def subtreeEdges(node, edgeList):
        for childIndex, child in enumerate(node.children):
            lineStyle = child.lineStyle or defaultLine
            if child.label:
                edgeList.append(blockEdge(node.nodeId, child.nodeId, lineStyle, child.label, False))
            elif childIndex == 0:
                edgeList.append(blockEdge(node.nodeId, child.nodeId, lineStyle, None, False))
            else:
                previous = node.children[childIndex - 1]
                edgeList.append(blockEdge(previous.nodeId, child.nodeId, lineStyle, None, False))
            subtreeEdges(child, edgeList)

    edgeGroups = []
    for rootIndex, root in enumerate(roots):
        edgeList = []
        if rootIndex > 0:
            previousRoot = roots[rootIndex - 1]
            edgeList.append(blockEdge(previousRoot.nodeId, root.nodeId,
                                      root.lineStyle or defaultLine, None, False))
        subtreeEdges(root, edgeList)
        if edgeList:
            edgeGroups.append(edgeList)
    for edgeList in edgeGroups:
        out.append('')
        out += edgeList

    styles = styleLines(nodes)
    if styles:
        out.append('')
        out += styles
    return '\n'.join(out)


def generateFishBone(roots):
    """fishBone（7章）."""
    out = ['ishikawa-beta']
    for node in walkDepthFirst(roots):
        out.append(' ' * (2 * node.level) + node.text)
    return '\n'.join(out)


def generatePie(roots, diag):
    """pie（8.1）."""
    root = roots[0]
    slices = []
    for child in root.children:
        name, value = parsePieText(child.text)
        slices.append((name, value, child.color))
    if len(slices) >= 13:
        diag.warn(f'pie: スライスが{len(slices)}個ある（Mermaidのテーマ変数は pie1〜pie12 まで）。'
                  '13個目以降の色指定は無視する')
    themeItems = []
    for sliceIndex, (_, _, color) in enumerate(slices[:12], start=1):
        if color:
            themeItems.append(f'"pie{sliceIndex}":"{color}"')
    themeItems.append('"pieOpacity":1')
    out = ['%%{init: {"theme":"base","themeVariables":{']
    for itemIndex, item in enumerate(themeItems):
        out.append('  ' + item + (',' if itemIndex < len(themeItems) - 1 else ''))
    out.append('}}}%%')
    out.append('pie showData')
    out.append(f'title {root.text}')
    for name, value, _ in slices:
        out.append(f'"{quoteText(name)}" : {value}')
    return '\n'.join(out)


def generateVenn(roots):
    """venn（8.2）."""
    level2Sets = ['N1,N2', 'N1,N3', 'N2,N3']
    out = ['venn-beta']
    styles = []
    level1Count = 0
    level2Count = 0
    for node in walkDepthFirst(roots):
        name, value = parseVennText(node.text)
        valuePart = f':{value}' if value is not None else ''
        if node.level == 1:
            level1Count += 1
            region = f'N{level1Count}'
            out.append(f'  set {region}["{quoteText(name)}"]{valuePart}')
        else:
            if node.level == 2:
                level2Count += 1
                region = level2Sets[level2Count - 1]
            else:
                region = 'N1,N2,N3'
            out.append(f'  union {region}["{quoteText(name)}"]{valuePart}')
        if node.color:
            styles.append(f'  style {region} fill:{node.color}')
    if styles:
        out.append('')
        out += styles
    return '\n'.join(out)


def generateTable(tableRoots, typeId):
    """table系（8.3）."""
    suffix = typeId[len('table'):]
    boldColumn = int(suffix[0]) if suffix[:1].isdigit() else None
    isCentered = suffix.endswith('c')

    rows = []
    for root in tableRoots:
        cells = [root.text] + [child.text for child in root.children]
        # 8.3.0 空セルの置換
        cells = [fullWidthSpace if cell.replace(' ', '').replace('\t', '') == '' else cell
                 for cell in cells]
        rows.append(cells)

    columnWidths = {}
    for cells in rows:
        for columnIndex, cell in enumerate(cells):
            columnWidths[columnIndex] = max(columnWidths.get(columnIndex, 0), displayWidth(cell))

    out = ['@startsalt', '{#']
    for rowIndex, cells in enumerate(rows):
        cellTexts = []
        for columnIndex, cell in enumerate(cells):
            cellText = cell
            # 8.3.1 太字化
            if boldColumn is not None and (rowIndex == 0 or columnIndex + 1 == boldColumn):
                cellText = f'<b>{cellText}</b>'
            # 8.3.2 センタリング
            if isCentered:
                padWidth = columnWidths[columnIndex] - displayWidth(cell)
                spaceCount = padWidth // 2
                leftCount = spaceCount // 2
                rightCount = spaceCount - leftCount
                if columnIndex == len(cells) - 1:
                    rightCount = 0
                cellText = fullWidthSpace * leftCount + cellText + fullWidthSpace * rightCount
            cellTexts.append(cellText)
        out.append('| ' + ' | '.join(cellTexts))
    out += ['}', '@endsalt']
    return '\n'.join(out)


def generateQuadrant(roots):
    """quadrant（9章）."""
    firstRoot, secondRoot = roots
    quadrantOf = {
        firstRoot.children[0].nodeId: 3,
        firstRoot.children[1].nodeId: 2,
        secondRoot.children[0].nodeId: 4,
        secondRoot.children[1].nodeId: 1,
    }
    level2Nodes = firstRoot.children + secondRoot.children

    fills = {}
    for node in level2Nodes:
        if node.color:
            fills[quadrantOf[node.nodeId]] = node.color
    out = []
    if fills:
        out += ['---', 'config:', '  themeVariables:']
        for quadrantNo in range(1, 5):
            if quadrantNo in fills:
                out.append(f'    quadrant{quadrantNo}Fill: "{fills[quadrantNo]}"')
        out.append('---')

    out.append('quadrantChart')
    out.append(f'  x-axis "{quoteText(firstRoot.text)}" --> "{quoteText(secondRoot.text)}"')
    out.append(f'  y-axis "{quoteText(firstRoot.children[0].text)}" --> "{quoteText(firstRoot.children[1].text)}"')

    labels = {quadrantOf[n.nodeId]: n.children[0].text for n in level2Nodes}
    for quadrantNo in range(1, 5):
        out.append(f'  quadrant-{quadrantNo} "{quoteText(labels[quadrantNo])}"')

    for rootIndex, root in enumerate(roots):
        xValue = 25 if rootIndex == 0 else 75
        for childIndex, level2Node in enumerate(root.children):
            baseY = 40 if childIndex == 0 else 90
            for pointIndex, pointNode in enumerate(level2Node.children[1:]):
                yValue = baseY - 5 * pointIndex
                out.append(f'  "{quoteText(pointNode.text)}": '
                           f'[{formatCoordinate(xValue)}, {formatCoordinate(yValue)}] radius:0')
    return '\n'.join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def buildArgumentParser():
    parser = argparse.ArgumentParser(
        prog='heading2diagram.py',
        description='見出し形式Markdownから PlantUML / Mermaid のダイアグラム定義を生成する')
    parser.add_argument('input', metavar='INPUT.md', help='見出し形式の入力ファイル')
    parser.add_argument('-o', '--output', metavar='OUTPUT.md', help='出力ファイル（省略時は標準出力）')
    parser.add_argument('-t', '--type', dest='types', nargs='+', action='extend', choices=typeIdList,
                        metavar='TYPE', help='生成する図種ID（複数指定可）: ' + ', '.join(typeIdList))
    parser.add_argument('--direction', choices=directionChoices, default=None)
    parser.add_argument('--layout', choices=layoutChoices, default=None)
    parser.add_argument('--line', choices=lineChoices, default=None)
    parser.add_argument('--arrowDirection', choices=arrowDirectionChoices, default=None)
    parser.add_argument('--curve', choices=curveChoices, default=None)
    return parser


def makeHeading(typeId, explicitOptions):
    optionParts = []
    for optionName in meaningfulOptions.get(typeId, []):
        if optionName in explicitOptions:
            optionParts.append(f'{optionFlags[optionName]} {explicitOptions[optionName]}')
    heading = f'## {typeId}'
    if optionParts:
        heading += ' (' + ' '.join(optionParts) + ')'
    return heading


def run(argv=None):
    parser = buildArgumentParser()
    args = parser.parse_args(argv)
    diag = Diagnostics()

    defaultOptions = {'direction': 'TB', 'layout': 'normal', 'line': 'solid',
                      'arrowDirection': 'default', 'curve': 'default'}
    explicitOptions = {}
    options = {}
    for optionName in optionOrder:
        value = getattr(args, optionName)
        if value is not None:
            explicitOptions[optionName] = value
            options[optionName] = value
        else:
            options[optionName] = defaultOptions[optionName]

    # 入力の読み込み
    try:
        with open(args.input, 'rb') as inputFile:
            sourceBytes = inputFile.read()
        sourceText = sourceBytes.decode('utf-8')
    except FileNotFoundError:
        diag.error(f'入力ファイルが存在しない: {args.input}')
        return 1
    except UnicodeDecodeError:
        diag.error(f'入力ファイルを UTF-8 として復号できない: {args.input}')
        return 1
    except OSError as exc:
        diag.error(f'入力ファイルを読めない: {args.input} ({exc.strerror})')
        return 1
    if sourceText.startswith('\ufeff'):
        sourceText = sourceText[1:]

    entries = parseInput(sourceText, diag)
    if not any(not entry.isEmpty for entry in entries):
        diag.error('有効な見出し行（テキストが空でない見出し行）が1行も無い')
        return 1

    # 生成対象の決定
    isExplicit = args.types is not None
    if isExplicit:
        targets = []
        for typeId in args.types:
            if typeId not in targets:
                targets.append(typeId)
    else:
        targets = None  # 木の構築後に決定

    needsMainTree = (not isExplicit) or any(t not in tableTypeIds for t in targets)
    needsTableTree = (not isExplicit) or any(t in tableTypeIds for t in targets)

    mainRoots = []
    tableRoots = []
    if needsMainTree:
        for entry in entries:
            if entry.isEmpty:
                diag.warn(f'{entry.lineNo}行目: 内容（テキスト）が空の見出し行である。'
                          'table系以外の図種では無視し、table系では空セルとして扱う')
        mainRoots = buildTree(entries, False, diag)
    if needsTableTree:
        tableRoots = buildTree(entries, True, diag)

    hasLabel = any(node.label for node in walkDepthFirst(mainRoots))
    if not isExplicit:
        targets = ['hier-mindlabel' if hasLabel else 'hier-mind', 'hier-block', 'hier-flow',
                   'fishBone', 'pie', 'venn', 'table', 'struct-flow', 'quadrant']

    # 入力条件の判定
    validTargets = []
    hasError = False
    for typeId in targets:
        reason = checkCondition(typeId, mainRoots, tableRoots)
        if reason is None:
            validTargets.append(typeId)
        elif isExplicit:
            diag.error(f'図種 {typeId} の入力条件を満たさない: {reason}')
            hasError = True
        else:
            diag.warn(f'図種 {typeId} の入力条件を満たさないためスキップする: {reason}')
    if hasError:
        return 1
    if not validTargets:
        diag.error('生成できた図種が1つも無い')
        return 1

    # 生成
    blocks = []
    for typeId in validTargets:
        outputTypeId = typeId
        if typeId == 'hier-mind' and hasLabel:
            diag.warn('hier-mind: 入力にラベル（|x|）が含まれるため、hier-mindlabel として生成する')
            outputTypeId = 'hier-mindlabel'

        if outputTypeId in ('hier-mind', 'hier-mindlabel'):
            body = generateMindmap(mainRoots, options, outputTypeId == 'hier-mindlabel', outputTypeId, diag)
        elif typeId == 'hier-flow':
            body = generateFlowchart(mainRoots, options)
        elif typeId == 'hier-block':
            body = generateHierBlock(mainRoots, options)
        elif typeId == 'struct-flow':
            body = generateStructFlow(mainRoots, options)
        elif typeId == 'fishBone':
            body = generateFishBone(mainRoots)
        elif typeId == 'pie':
            body = generatePie(mainRoots, diag)
        elif typeId == 'venn':
            body = generateVenn(mainRoots)
        elif typeId in tableTypeIds:
            body = generateTable(tableRoots, typeId)
        else:
            body = generateQuadrant(mainRoots)

        fenceLanguage = 'plantuml' if outputTypeId in plantumlTypeIds else 'mermaid'
        blocks.append('\n'.join([makeHeading(outputTypeId, explicitOptions),
                                 f'```{fenceLanguage}', body, '```']))

    outputText = '\n\n'.join(blocks) + '\n'

    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8', newline='\n') as outputFile:
                outputFile.write(outputText)
        except OSError as exc:
            diag.error(f'出力ファイルへ書き込めない: {args.output} ({exc.strerror})')
            return 1
    else:
        writeStream(sys.stdout, outputText)
    return 0


def main():
    sys.exit(run())


if __name__ == '__main__':
    main()
