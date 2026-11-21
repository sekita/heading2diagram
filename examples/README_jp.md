# 使用例

このディレクトリには、`heading2diagram` の日本語の入力例と参照出力を収録している。

[メイン README に戻る](../README_jp.md)

以下のコマンドは、この `examples/` ディレクトリをカレントディレクトリとして実行する想定である。

## 例1 — 基本的な階層

入力: `example1.md`

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

```sh
python ../heading2diagram.py example1.md -t hier-block -o out1_hier-block.md
python ../heading2diagram.py example1.md -t hier-flow -o out1_hier-flow.md
python ../heading2diagram.py example1.md -t hier-mind -o out1_hier-mind.md
python ../heading2diagram.py example1.md -t struct-flow --layout tight -o out1_struct-flow_tight.md
```

| 出力 | 図種 | 主な設定 |
|---|---|---|
| `out1_hier-block.md` | `hier-block` | 既定 |
| `out1_hier-flow.md` | `hier-flow` | 既定 |
| `out1_hier-mind.md` | `hier-mind` | 既定 |
| `out1_struct-flow_tight.md` | `struct-flow` | `--layout tight` |

## 例2 — 形状・色・接続線ラベル

入力: `example2.md`

```text
# サブ;会議の準備
## 議題の確定
## スタ;資料作成:#FAF
### 前回議事録
### 実績データ
### 提案書
## 六角;会場手配:#0FF
### |参加者確定|実線矢印;四右;日程調整
### |会場確定|実線矢印;備品確認
```

```sh
python ../heading2diagram.py example2.md -t hier-block --direction LR --layout tight -o out2_hier-block_LR_tight.md
python ../heading2diagram.py example2.md -t hier-flow --direction LR -o out2_hier-flow_LR.md
python ../heading2diagram.py example2.md -t hier-mindlabel --direction LR -o out2_hier-mindlabel_LR.md
python ../heading2diagram.py example2.md -t struct-flow --layout tight -o out2_struct-flow_tight.md
```

| 出力 | 図種 | 主な設定 |
|---|---|---|
| `out2_hier-block_LR_tight.md` | `hier-block` | `--direction LR --layout tight` |
| `out2_hier-flow_LR.md` | `hier-flow` | `--direction LR` |
| `out2_hier-mindlabel_LR.md` | `hier-mindlabel` | `--direction LR` |
| `out2_struct-flow_tight.md` | `struct-flow` | `--layout tight` |

`example2.md` では、ノード形状、色、接続線ラベルなどの要素属性を確認できる。なお、`hier-mindlabel` では枠の形状と要素ごとの線種を表現できないため、この出力では標準エラー出力に警告が出る。

## 例3 — fishBone と逆向き階層

入力: `example3.md`

```sh
python ../heading2diagram.py example3.md -t fishBone -o out3_fishBone.md
python ../heading2diagram.py example3.md -t hier-flow --direction RL --line thickArrow --arrowDirection reverse -o out3_hier-flow_RL_thickArrow_arrowReverse.md
```

## 例4 — Venn 図

入力: `example4.md`

```sh
python ../heading2diagram.py example4.md -t venn -o out4_venn.md
```

## 例5 — 表

入力: `example5.md`

```sh
python ../heading2diagram.py example5.md -t table1c -o out5_table1c.md
```

## 例6 — 4象限

入力: `example6.md`

```sh
python ../heading2diagram.py example6.md -t quadrant -o out6_quadrant.md
```

## 例7 — 円グラフ

入力: `example7.md`

入力では、各項目を `項目名:数値:#色` の形式で記述できる。

```text
# 作業時間の内訳
## 資料作成:60:#aff
## 会場手配:40:#afa
## 日程調整:30:#ffa
## 議題の確定:15:#faa
```

```sh
python ../heading2diagram.py example7.md -t pie -o out7_pie.md
```

## 例8 — 放射状の図（star）

入力: `example8.md`

第1階層の要素を中心とし、第2階層の要素を中心の真上から記述順に時計回りで配置する。

```text
# 円形;会議の準備:#ffd
## 議題の確定
## |前回議事録|実線矢印;資料作成
## |参加者確定|実線矢印;サブ;会場手配:#0FF
## |会場確定|点線矢印;日程調整
## 角丸;備品確認
```

```sh
python ../heading2diagram.py example8.md -t star -o out8_star.md
python ../heading2diagram.py example8.md -t star --degree 30 --line dotted -o out8_star_degree30_dotted.md
```

| 出力 | 図種 | 主な設定 |
|---|---|---|
| `out8_star.md` | `star` | 既定 |
| `out8_star_degree30_dotted.md` | `star` | `--degree 30 --line dotted` |

`--degree 30` は配置全体を時計回りに30度回転させる。`--line dotted` は既定の線種を点線にするが、要素ごとに指定した線種が優先される。

## 参照出力の確認

リポジトリのルートディレクトリから次を実行すると、参照出力と現在のプログラム出力が完全一致するかを確認できる。

```sh
python -m unittest discover -s tests -v
```
