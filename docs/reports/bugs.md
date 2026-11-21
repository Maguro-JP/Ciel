# バグの帳簿

直していないバグと、直した記録です。1 件 1 節で、`.claude/skills/bug-first/scripts/bugs.py` が読み書きします（bug-first）。
重さは 致命的・重い・軽い、状態は 未修正・修正中・確認待ち・修正済み・対象外 です。致命的は、今の作業を止めて修正版を出します。
漏洩のバグでは、漏れた値そのものを書きません。場所と種類だけを書きます。

<!-- 節の形（bugs.py --add が作ります。手で足すときも同じ形にします）

## B-001 保存のあとに起動しない
- 重さ: 致命的
- 状態: 未修正
- 見つけた日: 2026-01-01 09:00
- 知った所: ユーザーの発言
- 症状: 設定を保存して閉じると、次の起動でウィンドウが出ない
- 再現の手順: 設定を開く、保存を押す、閉じる、起動する
- 直したコミット:
- 修正版:
- 直した日:
-->

## B-001 配るひな形のフック 4 本が手元より古く、配った先の差し込みが目安を超える
- 重さ: 重い
- 状態: 修正済み
- 見つけた日: 2026-11-21 17:08
- 知った所: 配った先の形で測った measure_hooks.py の出力
- 症状: repo-bootstrap/templates/hooks/ の 4 本（lang-check.sh、lang-rule.sh、lessons.sh、pr-nudge.sh）が .claude/hooks/ より古く、配った先には古い方が配られていました。配った先の形で測ると、SessionStart が 8635 文字、UserPromptSubmit が 1538 文字でした（目安は 5000 と 1200 です）
- 再現の手順: 空のリポジトリに sync.py --apply で配り、そこで measure_hooks.py を動かします
- 直したコミット: d8ad30a
- 修正版:
- 直した日: 2026-11-21 17:08

## B-002 sync.py が、PreToolUse と PostToolUseFailure のフックの登録を配らない
- 重さ: 重い
- 状態: 未修正
- 見つけた日: 2026-11-21 17:08
- 知った所: 配った先の形の settings.json と、ひな形の settings.json の比較
- 症状: sync.py の HOOK_EVENTS が 4 つ（SessionStart、UserPromptSubmit、Stop、PostToolUse）だけです。ひな形にある PreToolUse の 4 本（pr_gate.py、ci_merge_gate.py、background_first.py、no_self_grant.py）と PostToolUseFailure の 1 本（odd_nudge.py）が、配った先の settings.json に足されません。PR の前の確認のフックが、配った先では動いていません
- 再現の手順: 空のリポジトリに sync.py --apply で配り、settings.json の hooks のキーを見ます。PreToolUse と PostToolUseFailure がありません
- 直したコミット:
- 修正版:
- 直した日:
