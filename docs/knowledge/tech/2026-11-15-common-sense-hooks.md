# 推測と古い知識をフックで止める（失敗は PostToolUse に来ない）

- 日付: 2026-11-15
- 語: 推測, たぶん, はず, 知識の古さ, 学習の知識, 一次情報, 根本原因, 同じ失敗, PostToolUse, PostToolUseFailure, last_assistant_message, Stop, フック, common-sense, 当たり前, おかしい, 会話の記録, transcript

## 情報
- PostToolUse は「ツールが成功したあと」にだけ動く。失敗したツールは PostToolUseFailure に来て、入力の `error` に文が入る。Bash は 1 行目が `Exit code N`。文書は、失敗も見たいなら同じフックを PostToolUseFailure にも登録するよう書いている（https://code.claude.com/docs/en/hooks 、2026-11-15）
- 動かして確かめた: Claude Code 2.1.325 の実際の会話の記録で、結果が is_error の Bash 39 件のうち、PostToolUse のフックが動いた物は 0 件だった。成功した Bash では動いていた
- フックや権限に止められた呼び出しは、PostToolUseFailure も動かない（同じ文書の PostToolUseFailure の注）。記録には is_error の結果として残り、文は `PreToolUse:<ツール> hook error` か `Permission` で始まる（実際の記録で確かめた）
- Stop の入力には `last_assistant_message`（最後の返答の文）がある。会話の記録は遅れて書かれ、Stop の時点で最後の返答が入っているとは限らないので、最後の返答はこの欄で見るよう書いてある（同じ文書の Stop input、2026-11-15）
- Stop フックが続けさせる回数には上限がある（続けて 8 回）。`stop_hook_active` は、Stop フックで続いている間は真（同じ文書）
- フックの差し込み（additionalContext、標準出力）は 1 つ 10,000 文字まで（同じ文書）
- 記録の中の人の発言は `origin.kind` が `human`。裏の処理の通知は `task-notification`。Stop フックの差し戻しは `isMeta` が真で `Stop hook feedback` の文で始まる。要約は `isCompactSummary` が真。どれも type は user（2.1.325 の記録を数えて確かめた。文書には無いので、版が変わると変わり得る）
- Write の結果には `originalFile`（書く前の中身）と `type`（`create` か `update`）がある。Edit の結果には `originalFile` と `oldString`、Bash の結果には `stdout` と `stderr` がある。実際の記録の toolUseResult の欄を数えて確かめた（文書が載せているのは、Write の `filePath` と `type`、Bash の 4 つの欄だけ）
- 推測の語を Stop フックで見る公開の実装がある。florianbuetow/claude-code の agent-guardrails は英語の語の一覧を grep で当て、`decision: block` を返す（https://github.com/florianbuetow/claude-code 、MIT、2026-11-15）。skymanbp/cc-enforcer は、語を一人称の不確かさに絞り、素の should は当てない（技術の文で普通に使うため）と書いている（https://github.com/skymanbp/cc-enforcer 、MIT、2026-11-15）
- 学習の知識の古さを扱う公開のスキルがある。houseofmvps/ultraship の staying-current は、版に左右される事実を一次情報で確かめる決まりを持つ。事実の例は API・版・フラグ・モデルの ID・値段・「最新」で、UserPromptSubmit のフックが思い出させる（https://github.com/houseofmvps/ultraship 、MIT、2026-11-15）。Soju06/knowpatch は「変わった所は文書に、版はパッケージの管理のツールに聞く」と分けている（https://github.com/Soju06/knowpatch 、MIT、2026-11-15）
- 原因の調べ方は obra/superpowers の systematic-debugging が詳しい。原因を掴む前に直さない、部品の境目で入った物と出た物を見る、直しが 3 回外れたら前提を疑う（https://github.com/obra/superpowers 、MIT、2026-11-15）
- 確かめていない: PostToolUseFailure が、配った先の全部の版で動くか。手元の 2.1.325 の実行ファイルに名前があることだけを見た

## 知識
推測の語は、調べていないことの合図として機械で拾える。ただし語だけで止めると、技術の文の普通の言い回し（「はずがない」「〜したいと思います」「確かに」）と、
言われたことのコピーで偽の差し戻しになる。断定の形に絞り、コード・引用・コピー・疑いの行を落とし、そのターンに調べる呼び出しが 1 回でもあれば通す。
止めるのは「語がある」と「調べていない」が両方そろったときだけにする。

失敗を PostToolUse で見ることはできない。成功した呼び出しでしか動かないからで、「同じ失敗の 2 回目」をその場で知らせるには PostToolUseFailure が要る。
この登録が配れない先と、フックや権限に止められた呼び出し（どちらのフックも動かない）は、次に成功した呼び出しのときに、会話の記録の後ろから is_error の結果を拾う。
拾った呼び出しの ID を覚えれば、2 つの道で同じ失敗を 2 回数えない。

会話の記録で「人の発言」を数えるときは、type が user というだけでは足りない。ツールの結果、Stop フックの差し戻し、裏の処理の通知、要約が同じ type で入る。
通知は 1 つの文に複数並ぶ。これらを人の発言と数えると、ターンが割れて「このターンに調べていない」が偽になる。

使えない場合: 推測の語の一覧は日本語だけ。返答が英語のセッションでは当たらない。記録の欄（origin、isMeta）は文書に無く、版で変わり得るので、
欄が無いときは文の出だし（`Stop hook feedback`、`task-notification`）で見分ける形を残す。外の事実を見に行ったかは呼び出しの名前とコマンドで見るので、
調べた中身が書いた物と合っているかまでは見ない。

## アルゴリズム
推測の差し戻し（Stop）。入力は最後の返答、会話の記録、stop_hook_active。出力は通す（0）か差し戻す（2 と 1 行）。
1. stop_hook_active が真か、記録が無ければ通す
2. 最後の返答を last_assistant_message から取る。無ければ、記録の最後のターンの最後の文
3. 返答に「❕ 疑い: …調べられない」の行があるか、人の発言が予想や意見を聞いていれば通す
4. 返答からコード、引用、↩ の行、❕ 疑い と ❕ おかしい の行を落とす
5. 残りに推測の語（断定の形）が無ければ通す。語の前後 4 文字ごと人の発言にあれば、コピーなので数えない
6. 最後のターン（最後の人の発言から後ろ）に調べる呼び出しが 1 回でもあれば通す
7. 差し戻す
端の場合: 記録が長い（数十 MB）ので、後ろの 1MB から読み、人の発言が見つからなければ 8MB、全部と広げる。
費用: 普段は 1MB の読みと、その中の行の JSON の読み 1 回。

同じ失敗の知らせ（PostToolUse と PostToolUseFailure）。入力はツールの名前、入力、結果か error、呼び出しの ID、記録。出力は 1 行か無し。
1. 失敗の行（失敗の語があり、0 件の行ではない）から、数・ハッシュ・パス・引用された名前を落とした形を作る。先頭の名前を除いた形と、エラーの種類から後ろの形も作る
2. 同じ形が 3 回以上あれば「同じ失敗が N 件」。同じ形には 1 セッションに 1 回
3. 失敗（error、または記録の is_error の結果）は、呼び出しと失敗の形の組で数える。フックに止められたときは、ツールの名前と理由の組で数える
4. 2 回目で「同じ失敗の 2 回目」。3 回目からは黙る
5. 見た呼び出しの ID を覚え、記録から拾うときに飛ばす
端の場合: 探すコマンド（grep）の出力は見ない。ソースコードの行（except、raise で始まる行など）は、失敗の語を含んでいても数えない。人が止めた・権限で断られた結果は数えない。1 セッションの知らせは 8 回まで。

## 技術
- 場所: `.claude/skills/common-sense/hooks/_cs.py` の `is_human`、`parse`、`last_turns`（記録からターンを取り出す）、`is_lookup`、`is_external_lookup`（調べる呼び出しの判定）
- 場所: `.claude/skills/common-sense/hooks/guess_gate.py` の `guesses`、`prose`
- 場所: `.claude/skills/common-sense/hooks/odd_nudge.py` の `same_failures`、`record`、`catch_up`
- 場所: `.claude/skills/common-sense/hooks/memory_nudge.py` の `deps`、`.claude/skills/common-sense/hooks/followup_gate.py` の `rows`、`.claude/skills/common-sense/hooks/today.py`
- テスト: `.claude/skills/common-sense/scripts/test_gates.py`、`.claude/skills/common-sense/scripts/test_nudges.py`

## 実装
- common-sense のスキルとして入れ、`.claude/settings.json` とひな形に登録した（SessionStart、UserPromptSubmit、Stop、PostToolUse、PostToolUseFailure）
- テストの出力: `Ran 28 tests in 1.858s` `OK`（test_gates.py）、`Ran 28 tests in 3.259s` `OK`（test_nudges.py）
- 実際の会話の記録（人のターン 70、Bash と MCP の結果 1412）の全部に判定を当てた出力: `guess_gate {'語なし': 69, '通す（疑いの行か、聞かれた）': 1}`、`followup_gate {'マージが成功したターン': 17}`（差し戻し 0）、`同じ失敗が 3 件以上': 12`、`同じ失敗の 2 回目 5`（5 件ともフックに同じ理由で止められた形）、memory_nudge の知らせ 0
- 当てる前は「同じ失敗が 3 件以上」が 24 件で、半分は偽の知らせだった。ファイルの中身を出したときの `except Exception:` の行と、検査の結果の「まだ止められる」の語に当たっていた。ソースコードの行を外し、語を減らして 12 件になった。残りには、配った先の 10 本で同じテストが落ちた出力が入っている。作った判定は、実際の記録に当てないと偽の当たりが分からない
- 記録の読みの速さ（39MB の記録）: `last_turns(1) 0.009 秒 / last_turns(3) 0.081 秒`
- 配った先の形（そのリポジトリ自身の登録がある settings.json）のコピーに sync.py で配り、そこで動かした出力: `test_gates.py exit 0 | Ran 28 tests in 1.795s  OK`、`test_nudges.py exit 0 | Ran 26 tests in 2.634s  OK`、`hooks-smoke --root exit 0 | フックの誤り 0`
- 差し込みの量: `SessionStart 合計 3848 文字（目安 5000）: 目安内`、`UserPromptSubmit 合計 1065 文字（目安 1200）: 目安内`。today.py は SessionStart で 84 文字、普段のターンは 0 文字
- テストが効いているかを、スキルのコピーの 1 か所を壊して確かめた。人の発言の見分けを外すと `FAILED (failures=4)`、重複の確認を外すと `FAILED (failures=1)`
- 壊しても落ちないテストが 1 組あった。テストの組に `fail` という名前の関数を置いていて、unittest の `fail`（検査が落ちたときに呼ばれる）を上書きしていた。名前を変えると落ちるようになった。壊して落ちるのを見ないと、通っているテストが何も見ていないことに気づけない
