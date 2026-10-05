# 使用例

このディレクトリには、`heading2diagram` の入力例と参照出力を収録している。

[メイン README に戻る](../README_jp.md)

以下のコマンドは、この `examples/` ディレクトリをカレントディレクトリとして実行する想定である。

## 例1 — 基本的な階層

入力: `example1.md`

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

`example2.md` では、ノード形状、色、接続線ラベルなどの要素属性を確認できる。

## 例3 — fishBone と逆向き階層

入力: `example3.md`

```sh
python ../heading2diagram.py example3.md -t fishBone -o out3_fishBone.md
python ../heading2diagram.py example3.md -t hier-flow --direction RL --line thickArrow --arrowDirection reverse -o out3_hier-flow_RL_thickArrow_arrowReverse.md
```

## 例4 — Venn 図

```sh
python ../heading2diagram.py example4.md -t venn -o out4_venn.md
```

## 例5 — 表

```sh
python ../heading2diagram.py example5.md -t table1c -o out5_table1c.md
```

## 例6 — 4象限

```sh
python ../heading2diagram.py example6.md -t quadrant -o out6_quadrant.md
```

## 例7 — 円グラフ

```sh
python ../heading2diagram.py example7.md -t pie -o out7_pie.md
```

入力では、各項目を `項目名:数値:#色` の形式で記述できる。

```text
# 作業時間の内訳
## 資料作成:60:#aff
## 会場手配:40:#afa
## 日程調整:30:#ffa
## 議題の確定:15:#faa
```

## 参照出力の確認

リポジトリのルートディレクトリから次を実行すると、上記14個の参照出力と現在のプログラム出力が完全一致するかを確認できる。

```sh
python -m unittest discover -s tests -v
```
