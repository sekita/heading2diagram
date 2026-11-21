## star (--line dotted --degree 30)
```mermaid
block
columns 20
space:12 N1_1["議題の確定"]:4 space:4
space:2 N1_5("備品確認"):4 space:14
space:20
space:8 N1(("会議の準備")):4 space:8
N1_4["日程調整"]:4 space:12 N1_2["資料作成"]:4
space:20
space:9 N1_3[["会場手配"]]:4 space:7

N1 -.- N1_1
N1 -- "前回議事録" ---> N1_2
N1 -- "参加者確定" ---> N1_3
N1 -- "会場確定" -.-> N1_4
N1 -.- N1_5

style N1 fill:#ffd
style N1_3 fill:#0FF
```
