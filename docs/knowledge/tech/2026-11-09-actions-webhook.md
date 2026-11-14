# GitHub Actions の通知を会話の記録から読む

- 日付: 2026-11-09
- 語: GitHub Actions, 通知, webhook, check_suite, head_sha, transcript, 購読

## 情報
- 動かして確かめた: クラウドのセッションに届く通知は、`kind="check_suite.completed"` の目印のあとに、説明の文を挟んで `"head_sha"` と `"pr"`（`Owner/Repo#番号` の形）が続く。会話の記録の実物を読んだ
- 動かして確かめた: 記録（jsonl）の中では引用符が `\"` に化け、作り方によって `:` のあとに空白が入る。化けていない形だけを待つ正規表現は 1 件も拾えなかった
- 動かして確かめた: 通知はユーザーの発言としても、ReadNotifications の結果としても記録に入る
- 落ちたときの文（conclusion の位置）は実物を見ていない。作った文で確かめただけ

## 知識
フックは会話の記録しか見られないので、「Actions が終わったか」は記録の中の通知で判定する。
通知は PR と head の組で 1 件なので、通知のあとに push があれば、その通知は古い（今の head の結果ではない）。
記録の中の文は、元の文と引用符の形が違う。正規表現は化けた形と化けていない形の両方を受ける。
使えない場合: workflow の無いリポジトリ（通知が来ない）と、購読していない PR（通知が届かない）。前者は確認の行に「Actions は無い」と書いて通す。

## アルゴリズム
入力は会話の記録（jsonl）と PR の番号。出力は、その PR の最後の通知（通った・落ちた・動いている）と、そのあとの push の有無。
1. 記録を 1 行ずつ読み、head_sha を含む行だけ正規表現に当てて、kind・sha・pr・conclusion を拾う
2. kind が完了で、conclusion が失敗の語でなければ「通った」、失敗の語なら「落ちた」、それ以外は「動いている」
3. assistant の行から、push と PR の作成の呼び出しを行番号つきで拾う
4. PR の番号で通知を絞り、最後の 1 件を取る
5. その行より後ろに push か作成があれば「古い」とする
6. 最後の通知が「通った」で古くないときだけ、マージの確認とマージを通す
端の場合: 通知が 1 件も無ければ「まだ無い」。conclusion は pr の前にも後ろにも来るので、目印の前後 400 文字を見る。費用は記録の全行の読み 1 回。

## 技術
- 場所: `.claude/skills/actions-watch/scripts/ci_state.py` の `read` と `latest`
- 場所: `.claude/skills/actions-watch/hooks/ci_gate.py`（Stop）、`.claude/skills/actions-watch/hooks/ci_merge_gate.py`（PreToolUse）
- テスト: `.claude/skills/actions-watch/scripts/test_ci_state.py`

## 実装
- Stop・PreToolUse・UserPromptSubmit の 3 つのフックとして settings.json に入れた
- このセッションの記録に当てた出力: `通知 81 件 / push と作成 267 回`
- 作った直後に Stop フックが「マージに触れただけの確認」を止めたので、マージを頼む行だけを見るように直した
