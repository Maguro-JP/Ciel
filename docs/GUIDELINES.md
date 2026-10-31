# スキル設計ガイドライン

## 1. description がすべて

スキルは `description` を見て発動するかどうかが決まります。本文がどれだけ良くても、
description が曖昧なら永遠に呼ばれません。

**悪い例**
```yaml
description: PDFを扱うのに便利なスキル
```

**良い例**
```yaml
description: PDFの読み取り・結合・分割・フォーム入力を行うとき。ユーザーが .pdf ファイル名に
  言及したり、PDFの生成を求めたときに使う。画像やWord文書には使わない。
```

書くべきもの：
- 発動する**具体的な状況**とキーワード
- 発動**しない**ケース（誤爆を防ぐ）

## 2. 本文は短く保つ

SKILL.md は発動するたびに読み込まれます。長いほど毎回コストがかかる。

- 中核の手順だけを SKILL.md に
- 詳細な仕様・APIリファレンス・長い例は `references/*.md` に逃がし、
  「必要になったら references/foo.md を読む」と本文から指示する
- 決まりきった処理はドキュメントで説明せず `scripts/` の実行可能ファイルにする

目安：SKILL.md 本文は 500 行以内、できれば 200 行以内。

## 3. ディレクトリ構成

```
.claude/.claude/skills/<skill-name>/
├── SKILL.md          必須
├── references/       必要に応じて読む長い資料
├── scripts/          実行するスクリプト
└── assets/           テンプレート・画像など
```

## 4. 命名

- ディレクトリ名 = `name` フィールド
- 小文字・数字・ハイフンのみ（`skill-audit`, `pdf-form-filler`）
- 動詞ベースだと発動しやすい（`review-x` `generate-x` `audit-x`）

## 5. 一つのスキルに一つの責務

「PDFとExcelとWordを扱うスキル」は分割する。責務が広いと description がぼやけ、
発動判定が不安定になる。


## 6. 発動はタスクの重さにも左右される

description が完璧でも、**AI が自力で簡単に片付けられる依頼ではスキルは呼ばれない**。
基本ツールで直接処理できてしまうため。複雑・多段階・専門的な依頼なら確実に発動する。

帰結:

- 軽い1ステップ作業のスキルを作っても、そもそも呼ばれない。**面倒な多段階作業に効く**
- 発動テストを「ファイルXを読んで」のような軽い依頼で行うと、
  何を直しても発動しないので評価にならない。テストは実務並みの重さで書く

## 7. 三層のロードを意識する

| 層 | 内容 | 読み込まれるタイミング | 目安 |
|---|---|---|---|
| 1 | name + description | **常時** | 約100語 |
| 2 | SKILL.md 本文 | 発動時 | 500行以内 |
| 3 | references / scripts / assets | 必要時のみ | 無制限（スクリプトは読み込まずに実行できる） |

300行を超える参考資料には**目次を付ける**。

## 8. 実測に基づく目安

公開スキル271本の測定結果（詳細は [OBSERVATIONS.md](OBSERVATIONS.md)）:

- SKILL.md 本文の実勢は**中央値168行**。500行超は271本中7本のみ
- description は**中央値47語**。20語未満はほぼ存在せず、100語超は少数派
- 85% が "Use when 〜" 系の明示的なトリガー句を持つ
- 除外句を書いているのは全体で39%。ただし**108本を運用する Google は75%**。
  スキルが増えるほど誤爆が問題になり、除外句が効いてくる
- `scripts/` 同梱は全体で9%だが、**Anthropic 公式は44%**。
  決定的な処理が要る領域では必須と考える

## 9. 検証

追加・変更したら必ず：

```bash
./scripts/validate.sh
```

そして実際に使ってみる。想定した場面で発動しなければ description を書き直す。

## 10. スキルどうしの干渉と優先

スキルは別々に書くので、決まりが重なったり逆を向いたりする。重なったら、ここで決めた側に従う。
スキルを足す・直すときは、この表に当たるかを見て、当たれば行を足す（skill-audit の 4、skill-upkeep の 3）。

| 重なる決まり | どちらに従うか |
|---|---|
| 「聞き返さない」（prompt-from-context、finish-first）と「出す前に ❔ で確認」（solo-pr-flow、pr_gate.py） | 確認を取るのは PR の作成・マージ・main への push・Release とタグの作成だけ。それ以外は聞き返さない |
| 「1 ターンに ❔ は 1 つ」（verify-before-done の done_check）と、配布など複数の確認 | 1 つの ❔ に全部を並べる。出し直すときは前の ❔ を指して短く書く |
| 「戻せる判断はデフォルトで進める」（finish-first、auto-dev）と確認ゲート | PR・マージ・push は戻せない側に数える。自律で回っているときは PR を作らず pending.md に「PR 待ち」 |
| 「分からなければ 1 つ聞く」（follow-instructions、work-style）と「文脈から補う」（prompt-from-context） | まず前の文脈から補う。聞くのは読み方で成果物が変わるときだけで、直したあとに ❔ を 1 行 |
| 「依頼を自分の言葉で返す」（work-style）と「了解・経過を書かない」 | ↩ 読み取り の 1 行がその返しで、ほかに書かない |
| 「通ったツールを信じて読み直さない」（token-efficiency）と「出力を貼る」（verify-before-done） | 読み直さないのはファイルの確認。完了の語の根拠は、そのターンのツールの出力で、貼るのは最後の行と場所だけ |
| 「尋ねずにマージ」（workspace-policy の auto_merge）と確認ゲート | auto_merge は、ユーザーが「確認なし」と言ったときだけ効く |
| フックの差し込み（lang-rule、directives、focus、token-efficiency、brief）と CLAUDE.md | CLAUDE.md が元。フックは短い思い出しだけにし、1 ターン合計 1,200 文字、SessionStart 5,000 文字を目安にする。token-efficiency の measure_hooks.py で測る |
| 「反抗の禁止」（follow-instructions）と「落ちた出力をそのまま書く」（verify-before-done） | 事実の報告は反抗ではない。出力を貼って 1 行で言い、判断はユーザーに渡す |
| desktop-app の no_browser.py と、CLI でよいもの（Ciel のスクリプト、ライブラリ） | フックは app/ src/ gui/ desktop/ の下だけを見る |
| 「開発者の間で通る語」（ja-proofread の glossary.md。「Routine」「PR」は原文のまま）と「ユーザーの語」（user-terms の対応表。ルーティン） | ユーザーの語が先。glossary は訳語を戻す先の既定で、ユーザーが別の語を使っていれば user-terms の表に行を足し、そちらに直す。両方に同じ行を書かない |
