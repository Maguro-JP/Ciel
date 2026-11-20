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
| 「ツールの成否は結果で信じる」（token-efficiency）と「AI が作ったものには間違いがある。書いたら読み直す」（verify-before-done の reread_check） | 信じるのはツールの成否（編集が入ったか）。自分が書いた中身は差分を 1 回読み、2 回目は読まない。完了の語の根拠はそのターンのツールの出力で、貼るのは最後の行と場所だけ |
| 「尋ねずにマージ」（workspace-policy の auto_merge）と確認ゲート | auto_merge は、ユーザーが「確認なし」と言ったときだけ効く |
| フックの差し込み（lang-rule、directives、focus、token-efficiency、brief）と CLAUDE.md | CLAUDE.md が元。フックは短い思い出しだけにし、1 ターン合計 1,200 文字、SessionStart 5,000 文字を目安にする。token-efficiency の measure_hooks.py で測る |
| 「反抗の禁止」（follow-instructions）と「落ちた出力をそのまま書く」（verify-before-done） | 事実の報告は反抗ではない。出力を貼って 1 行で言い、判断はユーザーに渡す |
| desktop-app の no_browser.py と、CLI でよいもの（Ciel のスクリプト、ライブラリ） | フックは app/ src/ gui/ desktop/ の下だけを見る |
| 「subagent は頼まれたときだけ」（token-efficiency、環境の既定）と「基本バックグラウンド」（background-first） | ユーザーが「基本バックグラウンド」と決めたので、3 手以上の調べもの・検査は Agent（run_in_background）に出してよい。❔ と PR・マージ・push は親のセッションがする。1 秒で終わるものは裏に出さない（通知で 1 ターン使う） |
| 「ツールの成否は結果で信じる」（token-efficiency）と「裏の処理の結果はファイルの末尾を読む」（background-first） | 裏の処理は exit の数と末尾の数行を読んで、通った・落ちたを言う。全部は読まない |
| 「訂正は 1 文で認めて直す」（follow-instructions の directives.py）と「感情を読んで 1〜2 行」（user-emotion の emotion.py） | 同じターンに両方が差し込む。感情の行は動き方（量と確認の数）、訂正の行は手順（認めて直す）で、重ねて守る。差し込みは合わせて 2 行まで |
| 「要請を受けたら作る」（skill-request）と「PR の前に ❔」（pr_gate）、「公開に非公開の名前を書かない」（content-audit） | 要請を受けても PR とマージはユーザーの返事のあと。要請した側の返事はユーザーの返事ではない。Ciel に置く要請は非公開の名前を伏せる。要請の受け付けは skill-upkeep の観察に入れ、別のルーティンを作らない |
| 「UI は使いやすさ」（ui-design）と「見た目の個性」（frontend-design）と「起動はウィンドウ」（desktop-app） | 3 つは重ならない。ui-design は使いやすさ（手数、答え、戻せる、邪魔しない）だけを決め、色や書体は frontend-design、起動の形は desktop-app。ui_nudge.py は tests・docs・design の下を見ない |
| 「人が開いたセッションは消さない」（feedback-session、tidy）と「無駄なセッションを消す」（session-watch） | AI が立てたものは消す。人が開いたものは見ない・聞かない・知らせない。ルーティンに紐づいた人のセッションは、ルーティンの動き（サボり・落ちた）だけ催促する |
| 「その日のうちに更新する」（vuln-watch）と「PR の前に ❔ で確認」（pr_gate.py） | 周知（★ と通知）と更新のブランチの用意は確認なしで行う。PR の作成とマージは ❔ を当日に出して待つ。返事が無ければ pending.md に「PR 待ち」 |
| 「開発者の間で通る語」（ja-proofread の glossary.md。「Routine」「PR」は原文のまま）と「ユーザーの語」（user-terms の対応表。ルーティン） | ユーザーの語が先。glossary は訳語を戻す先の既定で、ユーザーが別の語を使っていれば user-terms の表に行を足し、そちらに直す。両方に同じ行を書かない |
| 「README を魅せる」（readme-showcase）と「README を今に合わせる」（docs-upkeep）と「公開前の精査」（content-audit、secret-leak-check） | readme-showcase は書く側（節の順、根拠、点数）で、docs-upkeep は保つ側（壊れたリンク、一覧の抜け）。どちらも precheck で動き、readme は注意、docs は誤りで止める。出す前の名前・鍵の検査は content-audit と secret-leak-check に任せ、readme_check.py は見ない |
| 「リポジトリ管理の 12 段」（repo-management）と「自律開発の表」（patrol）と「整理整頓」（tidy） | repo-management は管理の段（揃っているか）、patrol は動きの状態（コミット・PR・Actions・判断待ち）、tidy は整理整頓の作業そのもの。repo_check.py は各段のスキルの検査を呼ぶだけで、判定の決まりを自分で持たない |
| 「作った物の機械の確認」（code-check）と「鍵の有無」（secret-leak-check）と「非公開の名前・費用」（content-audit）と「依存の CVE の見張り」（vuln-watch）と組み込みの `/security-review` | code-check は自分のコードの穴・クラッシュ・情報の扱いを実績のあるツールで見る側で、鍵の型は secret-leak-check、名前と費用は content-audit、依存の週 1 回は vuln-watch がそれぞれ持つ。code-check はその 3 つの要約を取り込むだけで、決まりを 2 か所に書かない。`/security-review` は読んで判断する側で、PR の差分で併用する |
| 「Actions の通知と順番」（actions-watch）と「PR の流れ」（solo-pr-flow）と「落ちた原因」（ci-triage） | actions-watch は購読と通知と ❔ の順番だけを機械で守る側で、PR の作り方・マージ・後片付けは solo-pr-flow、落ちたときの原因の特定は ci-triage が持つ。決まりを 2 か所に書かず、solo-pr-flow の表から actions-watch を指す |
| 「調べ物を技術にする」（research-to-tech）と「目標を決めて練習する」（self-learn）と「失敗の記録」（lessons）と「日の作業の記録」（auto-dev の docs/knowledge/） | research-to-tech は開発の途中の調べ物を 5 段で 1 件 1 ファイルにする側（docs/knowledge/tech/）で、判定と練習の周回が要る物は self-learn（docs/knowledge/learning/）、間違えた記録は lessons が持つ。同じ中身を 2 か所に書かず、技術にした物の場所を指す |
| 「開発を速くするために子のセッションに分ける」（feedback-session、background-first）と「ルーティンの紐づけ先はユーザーが使っているセッション」（scheduler、long-dev） | 子に出すのは、親のブランチに積む区切りのある作業だけ。ルーティンと long-dev の紐づけ先は移さず、子はルーティンを作らない。ユーザーがセッションを増やさないと言ったリポジトリでは、子も立てない |
| 「独立した作業は子のセッションに分ける」（feedback-session の fanout、background-first）と「未完成があるうちは新しい成果物を始めない」（finish-first）と「セッションを 1 つ立てるだけで文脈が乗る」（token-efficiency） | 分けるのは今の成果物の残りと、既にある未完成だけ。新しい成果物を始める口実にしない。10 手に満たない作業と、触る場所の重なる作業は分けない。週の上限に近い（`rate_limit_info.status` が `allowed` 以外）ときは増やさない |
| 「モデルは難易度で選ぶ」（feedback-session の models.md）と、ユーザーがモデルを名指しした指示 | 名指しが先。表は、言われていないときの既定。分からなければ普通 |
| 「子は PR を作らない・質問しない」（fanout のプロンプト）と「PR の前に ❔」（pr_gate）、「Actions の通知」（actions-watch） | PR と ❔ と購読は親だけがする。子は親のブランチに push して終わる |
| 「長いターンを分ける」（fanout_gate.py、Stop）と「足りない 1 行だけを足す」（Stop フックの差し戻しの決まり） | 差し戻されたら、分けるか「❕ 並列: 分けない（理由）」の 1 行だけを足す。前の行を出し直さない |
| 「疑いの 1 行を必ず書く」（verify-before-done の reread_check）と「疑いに残すのは調べられなかったことだけ」（common-sense の guess_gate.py） | 疑いの行は書く。そこに書くのは、確かめていないことと、調べられなかったこと（理由を添える）。調べれば分かることは、調べてから断定で書く。推測の語は、疑いの行の外に書かない |
| 「調べたら知識に残す」（research-to-tech の research_gate.py）と「調べずに済ませない」（common-sense） | common-sense は調べる前（調べるかどうか、調べる順）を持ち、research-to-tech は調べたあと（残す形）を持つ。調べる順の表は common-sense の lookup.md、残す手順は research-to-tech に 1 か所ずつ書く |
| 「成功したツールを信じる」（token-efficiency）と「おかしいと思う」（common-sense） | 信じるのは、ツールの成否（編集が入ったか、コマンドが終わったか）。返った中身が予想と違うとき（数の桁、全部が同じ失敗、状態が変わらない）は、疑って一次情報で確かめる。確かめるのは 1 回で、同じ確認を繰り返さない |
| 「読む前に探す」「通った検査を回し直さない」（token-efficiency の trajectory_guard.py）と「一次情報で確かめる」「同じ失敗」（common-sense の odd_nudge.py） | 節約で削るのは読み直しと再実行で、調べ物は削らない。調べるときも、探してから要る範囲だけ読む。trajectory_guard.py は通った検査の再実行を見て、odd_nudge.py は失敗だけを見るので、同じ呼び出しで両方は言わない |
| 「戻せる判断はデフォルトで進める」（finish-first）と「当たり前の次の手順を最後までやる」（common-sense）と「PR とマージの前に ❔」（pr_gate.py） | 次の手順は、確認の要らない所（用意、検査、配布のブランチ）まで進める。PR の作成とマージは ❔ を 1 回出して待つ。答えをもらったことは聞き直さない。止められて進めないときだけ、何が止めたか・何と言えば通るかを 1 行で書く |
| 「反抗の禁止」「ユーザーがすべての一番上」（follow-instructions）と「おかしいと思ったら先に原因を調べる」（common-sense） | 疑う相手は、機械の判定と自分の認識。ユーザーの指示を、おかしいと言って止めない。ユーザーの言葉と機械の判定が逆なら、機械の側を調べる。気づいた事実は ❕ で 1 行書き、判断はユーザーに渡す |
| 「次は〜しますを書かない」（work-style、done_check.py）と「❕ 次: の行」（common-sense の followup_gate.py） | `❕ 次:` には、予定ではなく、次の手順と、いま始めたこと（裏で動かしている物、用意した物）を書く。差し戻されたら、この 1 行だけを足す |
| 「Release とタグは頼まれたときだけ」（tidy、pr_gate.py）と「致命的なバグは即修正版を出す」（bug-first） | 致命的なバグの修正版の Release とタグは、ユーザーが即修正版を出すと決めたので、頼まれた物として出す。重い・軽いバグの修正では作らない。版もタグも持たないリポジトリでは、マージまでが修正版 |
| 「PR の作成・マージ・main への push の前に ❔」（pr_gate.py）と「即修正版を出す」（bug-first） | 確認は残る。修正・テスト・版・変更履歴・precheck まで全部済ませてから ❔ を 1 行だけ出し、返事があり次第、その場で PR・マージ・Release まで出す。返事が無いまま作らない。確認そのものを外すのは、ユーザーが自分の手でゲートを変えたときだけ |
| 「Actions が終わる前にマージの ❔ を出さない」「PR の確認とマージの確認を分ける」（actions-watch の ci_gate.py、ci_merge_gate.py）と「❔ は 1 行だけ」（bug-first） | 致命的なバグの修正版だけ、PR の作成・Actions が通ったあとのマージ・Release を 1 行の ❔ で前もって聞く（文は bug-first の references/hotfix.md の 9 の形）。マージそのものは、完了の通知のあと。Actions が落ちたら ci-triage で直し、そのあとの ❔ は PR の番号と結果を添えて出し直す。重い・軽いバグの修正は、今までどおり確認を分ける |
| 「未完成があるうちは新しい成果物を始めない」（finish-first）、「壊れているもの・詰まっているものが先」（auto-dev の作業を選ぶ表）と「何よりもバグ修正を優先」（bug-first） | バグ修正が先。auto-dev の表の 0 に置き、今の成果物の「残り」より先に直す。バグ修正は新しい成果物に数えない。致命的は、サイクルの途中でも今の作業を止めて区切り、修正版まで出してから戻る |
| 「ユーザーがはっきり指示した操作は、そのまま行う」「AI の基準でユーザーの指示を止めない」（follow-instructions）と「致命的が残っているのに別の編集で終えない」（bug-first の bug_gate.py） | ユーザーが別の作業をはっきり指示したら、指示に従う。`❕ バグ: <残っているバグと、先にしなかった理由>` を 1 行書けば、フックは通す。フックは、黙って別の作業へ進むのを止めるだけ |
| 「同じ失敗を知らせる」（common-sense の odd_nudge.py）、「書き込みのたびに重大を見る」（code-check の code_nudge.py）と「クラッシュの出力を知らせる」（bug-first の crash_nudge.py） | odd_nudge.py は繰り返し（同じ失敗が 3 件以上、同じ失敗の 2 回目）、code_nudge.py は書いたファイルの構文と重大、crash_nudge.py は実行の出力のクラッシュの印を見る。同じ失敗が並ぶ出力では crash_nudge.py が黙り、同じクラッシュの 2 回目は odd_nudge.py だけが言う。1 回の呼び出しに、同じ中身を 2 行出さない |
| 「作った物を機械で確認する」（code-check）、「落ちた Actions の原因を読む」（ci-triage）と「バグは帳簿に書いて先に直す」（bug-first） | code-check と ci-triage は見つける側、bug-first は見つかった物の順番と修正版の側。その場で直さない重大と、main ブランチで落ちているテストは、帳簿（docs/reports/bugs.md）に書く。重さの表は bug-first の references/severity.md に 1 か所だけ置く |
