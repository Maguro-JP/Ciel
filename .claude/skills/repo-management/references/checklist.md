# 段ごとの判定と直し方

`scripts/repo_check.py` が機械で出す判定の基準。人が見るときも同じ基準で見る。

| 段 | OK | 注意 | NG | 直し方 |
|---|---|---|---|---|
| 土台 | CLAUDE.md があり、`.claude/settings.json` に hooks がある | settings.json はあるが hooks が無い | CLAUDE.md か settings.json が無い | repo-bootstrap の `bootstrap.sh`。既にある物には触らない |
| 方針 | `.claude/policy/*.json` がある | 無い | ― | workspace-policy で自動マージの可否、同時に開く PR の本数、人のレビューの要否を決めて記録する |
| README | readme_check.py の 10 項目に NG が無い | NG がある（点数が 10 未満） | README.md が無い | readme-showcase。雛形から書き、NG を直して 10/10 にする。LICENSE の無い物は先にライセンスを決める |
| 文書 | docs_check.py の誤り 0、注意 0 | 注意がある（古くなる数、予定の語、重複、強調の記号） | 誤りがある（壊れたリンク、無いファイル、一覧の抜け、辿れない文書） | docs-upkeep。スキルやスクリプトを足した・消した PR で一覧とリンクを直す |
| 鍵 | 作業ツリーに検出なし | ― | 検出あり | secret-leak-check。先にローテートし、次に消す。公開の前は `--history` で履歴も見る |
| 公開の精査 | 重大 0、注意 0 | 注意がある | 重大がある | content-audit。名前・メール・ID・費用・内部の場所を伏せる。スクリーンショットに写った物も見る |
| 脆弱性 | 棚卸しができている | inventory.py が無い（vuln-watch が入っていない） | ― | vuln-watch を入れ、週 1 回のルーティンに載せる。悪用済みと重大は更新のブランチを用意して ❔ |
| 整理整頓 | 余計なファイルが追跡されていない、要る `.gitignore` の行がある、デフォルトブランチに入ったリモートブランチが無い | どれかがある | ― | tidy。余計なファイルは消して `.gitignore` に足す。入ったブランチは消す。月に 1 回は `tidy_report.py` |
| 出し方 | 最後の precheck が通っている | 記録が無い、または落ちている | ― | solo-pr-flow。PR の前に `precheck.py` を通し、❔ で返事を待つ |

## 公開の前に足すこと

作業ツリーだけでは足りない。private を public にする前は、次も見る。

- 鍵: `scan.py --history`（全コミット）。見つかったら、消しても戻らないので先にローテート
- 公開の精査: `audit.py --history` と `audit.py --github <owner>/<repo>`（Issue、PR の本文、履歴の著者）
- README: スクリーンショットに、名前・メール・鍵・内部の場所が写っていないか
- ライセンス: LICENSE が無いまま公開しない

## 月に 1 回

tidy の月初の回と skill-upkeep の月初の回で `repo_check.py --md` を回し、表を月報の「整理整頓」の節に入れる。
注意のまま残す段は、理由を 1 行で書く。
