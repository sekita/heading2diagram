# heading2diagram

**heading2diagram** は、Markdown に似た「見出し形式」のテキストから、Mermaid または PlantUML の図表ソースを生成するコマンドラインツールである。

- English: [README.md](README.md)
- 見出し形式の文法: [docs/見出し形式文法.md](docs/見出し形式文法.md)
- 使用例: [examples/README_jp.md](examples/README_jp.md)

## バージョン

`1.1.0`

## 動作環境

- Python 3.10 以上
- 外部 Python パッケージ不要（標準ライブラリのみ）

Mermaid または PlantUML の図そのものを描画する場合は、生成されたコードをそれぞれ対応するレンダラーで表示する。

## 基本的な使い方

リポジトリを取得した後、次のように実行する。

```sh
python heading2diagram.py INPUT.md
```

生成する図種を明示する場合は `-t` を使用する。

```sh
python heading2diagram.py INPUT.md -t hier-flow
```

出力をファイルへ保存する場合は `-o` を使用する。

```sh
python heading2diagram.py INPUT.md -t hier-flow -o output.md
```

複数の図種を一度に指定することもできる。

```sh
python heading2diagram.py INPUT.md -t hier-mind hier-block hier-flow -o output.md
```

利用可能な引数は次のコマンドで確認できる。

```sh
python heading2diagram.py -h
```

`-t` を省略した場合は、入力条件を満たす図種を判定し、生成可能な図を出力する。入力条件を満たさない図種は警告を出してスキップする。一方、`-t` で図種を明示した場合、その図種の入力条件を満たさなければエラーとして終了する。

## 見出し形式

見出し形式では、行頭の `#` の個数によって階層構造を表す。`#` が1個増えると親要素の子要素となり、同じ個数の `#` を持つ要素は同じ階層の兄弟要素となる。

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

例えば、上記を階層フローチャートへ変換するには次のように実行する。

```sh
python heading2diagram.py examples/example1.md -t hier-flow
```

## 図種

図種IDは `-t` / `--type` で指定する。

| 目的 | 図種ID |
|---|---|
| 階層・分類をマインドマップで表す | `hier-mind` |
| 接続線ラベル付きマインドマップ | `hier-mindlabel` |
| 階層・分類を格子状に表す | `hier-block` |
| 階層・分類をフローチャートで表す | `hier-flow` |
| 因果関係を特性要因図で表す | `fishBone` |
| 構成比・内訳を円グラフで表す | `pie` |
| 集合とその重なりをベン図で表す | `venn` |
| 表を生成する | `table`, `tablec`, `table1`, `table1c`, `table2`, `table2c`, `table3`, `table3c` |
| 手順・流れを表す | `struct-flow` |
| 2つの観点による4象限を表す | `quadrant` |
| 中心の要素と周囲の要素を放射状に表す | `star` |

接続線ラベルを含む入力に対して `hier-mind` を指定した場合は、`hier-mindlabel` が自動的に用いられる。

### 放射状の図（`star`）

`star` はバージョン 1.1.0 で追加した図種である。第1階層に中心の要素を1個、第2階層に周囲の要素を記述する。周囲の要素は、中心の真上から始めて、記述順に時計回りで配置される。第3階層以下は記述しない。

```text
# 円形;会議の準備:#ffd
## 議題の確定
## |前回議事録|実線矢印;資料作成
## |参加者確定|実線矢印;サブ;会場手配:#0FF
## |会場確定|点線矢印;日程調整
## 角丸;備品確認
```

```sh
python heading2diagram.py examples/example8.md -t star
python heading2diagram.py examples/example8.md -t star --degree 30 --line dotted
```

## 要素ごとの属性指定

`hier-mind`、`hier-flow`、`hier-block`、`struct-flow`、`star` では、各要素に属性を付加できる。

```text
[|ラベル|][線種;][形状;]テキスト[:#色]
```

角括弧 `[]` は「省略可能」を示す説明上の記号であり、実際の入力には記述しない。

例：

```text
|先方待ち|実線矢印;サブ;備品確認
```

この例では、「備品確認」へ接続する線に「先方待ち」というラベルを付け、実線矢印を使用し、枠形状を「サブ」とする。

### 接続線の種類

| 日本語指定 | 英語指定 |
|---|---|
| 実線 | `solid` |
| 点線 | `dotted` |
| 太線 | `thick` |
| 実線矢印 | `solidArrow` |
| 点線矢印 | `dottedArrow` |
| 太線矢印 | `thickArrow` |

### 枠の形

| 日本語指定 | 英語指定 |
|---|---|
| 四角 | `rect` |
| 角丸 | `rounded` |
| スタ | `stadium` |
| サブ | `fr-rect` |
| 円柱 | `cyl` |
| 円形 | `circle` |
| 非対 | `odd` |
| ひし | `diam` |
| 六角 | `hex` |
| 四右 | `lean-r` |
| 四左 | `lean-l` |
| 台形 | `trap-b` |
| 逆台 | `trap-t` |
| 重円 | `dbl-circ` |
| 無枠 | `borderless` |

`hier-mind` では形状表現に制約があり、「角丸」と「無枠」以外の形状指定は表現できない。

### 色

RGBを表す3桁または6桁の16進数として、先頭に `#` を付ける。

```text
:#f88
:#ff8888
```

## 図全体のオプション

| オプション | 主な適用図種 | 指定値 |
|---|---|---|
| `--direction` | `hier-*` | `TB`, `TD`, `BT`, `LR`, `RL` |
| `--layout` | `hier-*`, `struct-flow`, `star` | `tight`, `normal`, `spacyX`, `spacyY`, `spacyXY`, `spacyPadding` |
| `--line` | `hier-*`, `struct-flow`, `star` | `dotted`, `solid`, `thick`, `dottedArrow`, `solidArrow`, `thickArrow` |
| `--arrowDirection` | `hier-flow`, `hier-block`, `star` | `default`, `reverse` |
| `--curve` | `hier-flow` | `default`, `linear`, `bumpX`, `bumpY`, `cardinal`, `catmullRom`, `monotoneX`, `monotoneY`, `natural`, `step` |
| `--degree` | `star` | 周囲の最初の要素を置く角度（度）。既定は `0`（真上）で、時計回りに増える |
| `--span` | `star` | 各ブロックが占める格子の列数（1以上の整数）。既定は `4` |
| `--radius` | `star` | 中心からの距離（推定ピクセル）。既定は自動 |
| `--blockWidth` | `star` | 配置計算に用いるブロック幅（推定ピクセル）。既定は最も幅の広いブロックの推定幅 |

ここで `hier-*` は説明上の総称であり、実際の図種IDではない。詳細は [見出し形式文法](docs/見出し形式文法.md) を参照すること。

## 使用例

`examples/` には、日本語の入力例8種類（`example1.md`〜`example8.md`）と、それぞれの参照出力16個（`out1_*.md`〜`out8_*.md`）を収録している。

```text
examples/
├── example1.md  # 基本階層
├── example2.md  # 形状・色・接続線ラベル
├── example3.md  # fishBone / 逆向き階層
├── example4.md  # Venn図
├── example5.md  # 表
├── example6.md  # 4象限
├── example7.md  # 円グラフ
└── example8.md  # 放射状の図（star）
```

各コマンドと対応する出力については [examples/README_jp.md](examples/README_jp.md) を参照すること。

## テスト

参照出力との一致は、標準ライブラリのみを使用する回帰テストで確認できる。

```sh
python -m unittest discover -s tests -v
```

現バージョンでは、`examples/` のすべての参照出力とプログラム出力が完全一致することを確認している。

## 入力誤りへの対応

入力の一部に誤りがある場合も、可能な範囲で処理を継続する設計である。

- 見出しとして解釈できない行は警告を出して無視する。
- `#` の階層が飛んだ場合は、直前の階層の子要素として補正し、警告する。
- 警告・エラーは標準エラー出力へ出力する。
- `-t` を省略した場合、条件を満たさない図種のみをスキップする。
- `-t` で図種を指定した場合、その図種の条件違反はエラーとなる。

## ファイル構成

```text
heading2diagram/
├── heading2diagram.py
├── README.md
├── README_jp.md
├── CITATION.cff
├── LICENSE
├── VERSION
├── docs/
│   ├── 見出し形式文法.md
│   └── headingBasedFormatSyntax.md
├── examples/
│   ├── README.md
│   ├── README_jp.md
│   ├── example1.md ... example8.md   # 日本語の入力例
│   ├── example1_en.md ... example8_en.md   # 英語の入力例
│   └── out*.md   # 参照出力
└── tests/
    └── test_examples.py
```

## ライセンス

本リポジトリは [MIT License](LICENSE) の下で公開する構成としている。

## 引用

引用情報は [`CITATION.cff`](CITATION.cff) に記載している。

