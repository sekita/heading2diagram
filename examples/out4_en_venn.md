## venn
```mermaid
venn-beta
  set N1["Paper"]:30
  set N2["Digital"]:20
  union N1,N2["Paper and digital"]:10
  set N3["Audio"]
  union N1,N3["Paper and audio"]:5
  union N2,N3["Digital and audio"]:5
  union N1,N2,N3["All three"]

  style N1 fill:#f88
  style N2 fill:#88f
  style N3 fill:#5f5
```
