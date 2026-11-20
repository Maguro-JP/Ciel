# 致命的なバグの修正版を出す手順と、バグの帳簿（クラッシュの出力は失敗した実行に出る）

- 日付: 2026-11-21
- 語: バグ、バグ修正、致命的、クラッシュ、操作不能、破損、漏洩、修正版、`hotfix`、重さ、triage、再現、テスト、版、patch、semver、変更履歴、changelog、Release、タグ、帳簿、Traceback、panic、PostToolUse、bug-first

## 情報
- 致命的なバグの修正版を出す公開のスキルがある。Donchitos/Claude-Code-Game-Studios の `hotfix` は、重さを 3 段に分けて上の 2 段だけを受け、記録を作り、出した版のタグから修正のブランチを切り、最小の修正だけを入れ、マージとタグの前に必ず確認を取る。タグから切った修正を main ブランチに入れ忘れると次の版でバグが戻る、と書いてある（https://github.com/Donchitos/Claude-Code-Game-Studios 、MIT、SKILL.md と LICENSE を 2026-11-21 に読んだ）
- バグの直し方の公開のスキルは、どれも同じ順番を持つ。duthaho/skillhub の `bugfix` は、再現（動かした出力が無い再現は数えない）、原因、落ちるテストを先に書く、最小の修正、最初の再現をもう一度動かす、1 件 1 行の記録（https://github.com/duthaho/skillhub 、MIT、2026-11-21）。eugenelim/agent-ready-repo の `bug-fix` は、害が続いているときは手当てが先で、手当ては根の直しではない、落ちたテストが意図した理由で落ちているかを見る、と書く（https://github.com/eugenelim/agent-ready-repo 、Apache-2.0 か MIT、2026-11-21）。2 つの出所で順番が一致した
- 重さの決め方は、mohitagw15856/pm-claude-skills の `bug-triage-pack` が、影響・頻度・回避の 3 つで決め、感覚で決めない、と書く（https://github.com/mohitagw15856/pm-claude-skills 、MIT、2026-11-21）
- 版の上げ方は Semantic Versioning 2.0.0 に決まりがある。バグ修正だけなら patch を上げる（仕様の 6）。一度出した版の中身は変えず、新しい版として出す（仕様の 3）（https://semver.org/spec/v2.0.0.html 、CC BY 3.0、2026-11-21）
- 変更履歴は Keep a Changelog 1.1.0 に形がある。新しい版が先頭、日付を書く、バグ修正は Fixed、脆弱性は Security、使ってはいけない版は見出しに YANKED を付ける（https://keepachangelog.com/en/1.1.0/ 、MIT、2026-11-21）
- Tauri の版は、tauri.conf.json の version に書くのが勧められていて、書いていなければ src-tauri の Cargo.toml の版が使われる。v2 で package.version が先頭に移った（Tauri の公式の文書の Versioning と Tauri 2.0 の節、Context7 経由、2026-11-21）
- Claude Code のフックの事実（https://code.claude.com/docs/en/hooks 、2026-11-21）。UserPromptSubmit と SessionStart は、標準出力の文が文脈に入る。PostToolUse は「ツールが成功したあと」に動き、文は additionalContext で返す。Bash の tool_response は stdout、stderr、interrupted、isImage を持つ。失敗は PostToolUseFailure に来るが、配る登録には無い
- 動かして確かめた: 確認のフック（pr_gate.py）は、❔ の行に「PR」「マージ」「push」「出し」のどれかと、リポジトリの名前か PR の番号があることと、直後の人の返事を見る。1 行の ❔ に返事があれば、PR の作成・通知のあとのマージ・Release・タグの 4 つとも通った。返事が無いとき、止める返事のときは、終了コード 2 で止まった
- 動かして確かめた: Actions の順番のフック（ci_gate.py）は、❔ の行に「マージして」があって PR の番号が無いと差し戻す。「マージまで進めて」と書いた同じ行は通った。言い方で結果が変わる
- 動かして確かめた: `gh release create --help` のように、作らずに読むだけの呼び出しも、pr_gate.py の Release の判定に当たって止まる
- 読んでいない物: bobmatnyc/claude-mpm-skills の `emergency-release-workflow` は、一覧のページの要約だけを読み、本文は取れなかった。gonimar の `hotfix` と Comfy-Org/ComfyUI_frontend の `red-green-fix` は、検索の結果の断片だけを見た。この 3 つは取り込んでいない

## 知識
バグの放置は、作業の量ではなく、順番と場所と出口の 3 つが無いことで起きる。見つけても今の作業を続ける（順番が無い）。会話の中だけにあって、セッションが閉じると消える（場所が無い）。
直しても版を出さないので、使う人の手元は壊れたまま（出口が無い）。順番は作業を選ぶ表の先頭に置き、場所は 1 件 1 節の帳簿にし、出口は修正版の手順にする。

直す順番は、再現、落ちるテスト、最小の修正、最初の再現をもう一度、で決まっている。急ぐ修正ほど、この順を飛ばすと 2 つ目の事故になる。
再現できない物は直さない。落ちるテストは、バグそのものの理由で落ちていることを出力で見る。修正に、整理や作り直しを混ぜない。

修正版で抜けやすいのは版で、場所がリポジトリごとに違い、複数ある（package.json と package-lock.json、Cargo.toml と Cargo.lock と tauri.conf.json、pyproject.toml と `__version__`）。
一部だけ上げると、インストーラーの版と中身の版がずれる。場所は機械で探し、版の文字だけを置き換える。JSON や TOML を読み直して書き出すと、並びと字下げが変わって差分が読めなくなる。

クラッシュの出力は、失敗した実行に出る。PostToolUse は成功したツールでしか動かないので、その場では見えない。次に成功した Bash のときに、会話の記録から失敗した結果を拾う。
印の文字（Traceback など）は、テストの出力、探した結果、ソースの表示、その場で書いた 1 行のスクリプトの誤りにも出る。行の形（行頭にあること、あとに続く枠）と、コマンドの種類で落とす。

使えない場合: 重さの語の判定は日本語だけ。帳簿の節の形（「## B-001」と「- 欄: 値」）を手で崩すと、数えられない。版の場所は決まった名前のファイルだけで、インストーラーの設定や画面に出す定数は探さない。
X.Y.Z でない版（先行版の印の付いた版）は上げない。Release の workflow の読み取りは、文字を探すだけで、動くかどうかまでは見ない。

## アルゴリズム
帳簿の読み（入力は帳簿の文、出力は節の列）。
1. HTML のコメントの範囲を取る（ひな形の見本の節が入っている）
2. 行頭の「## 」の位置のうち、コメントの外にある物で文を切る
3. 切った節の頭が「## B-数」なら、番号と題を取り、「- 欄: 値」の行から欄を取る
4. 状態が 修正済み と 対象外 以外は、直していない側に数える（空や書き損じも）。重さが致命的で直していない物のうち、確認待ち以外が、ほかの開発を止める
端の場合: 書き換えは、同じ切り方で節を選んで、その節の欄だけを置き換える。見本の節も同じ番号を持つので、コメントの中を節として読むと、見本を書き換えてしまう。

別の編集の差し戻し（Stop。入力は帳簿、会話の記録、最後の返答。出力は通す（0）か差し戻す（2 と 1 行））。
1. stop_hook_active が真か、帳簿に止める致命的が無いか、記録の読み手（common-sense）が無ければ通す
2. 返答に「❕ バグ: 」の行があれば通す
3. 最後のターンの呼び出しを順に見る。その節の番号がある、帳簿を書き換えた（Edit か bugs.py の --add と --set が成功）、なら通す
4. 成功した編集のうち、リポジトリの外、記録（docs/reports、docs/knowledge、LESSONS.md）、修正のブランチ（名前に `fix`、`hotfix`、`bug`）にあるファイルを除く
5. 残りがあれば差し戻す
端の場合: 止められた呼び出しと失敗した編集は数えない。ブランチはファイルの場所で聞く（worktree は根と違うブランチにいる）。通知と差し戻しは人の発言ではないので、ターンを割らない。

クラッシュの知らせ（PostToolUse、Bash。入力はコマンド、出力、呼び出しの ID、記録。出力は 1 行か無し）。
1. 今のターンの、まだ見ていない失敗した Bash の結果を記録から拾い、今の出力と合わせて順に見る
2. 探すコマンドと、ソースや文書を見るコマンドの出力は見ない
3. 強い印（Segmentation fault、core dumped、FATAL、メモリ不足）があれば当たり
4. テストを動かすコマンドか、テストの出力の形なら、弱い印は見ない
5. 弱い印（行頭の Traceback、panic、Unhandled、Uncaught）を探す。Traceback は、枠が全部その場のスクリプトか、全部入れてある物の中なら外す。最後の行が KeyboardInterrupt、BrokenPipeError なら外す
6. 印の名前と、最後の行から数・ハッシュ・パスを落とした形を組にし、同じ組は 1 セッションに 1 回だけ知らせる
7. 同じ失敗の行が 3 件以上並ぶ出力は、common-sense の odd_nudge.py が言うので黙る
費用: 記録の後ろ 256KB の読みと、その中の行の JSON の読み 1 回。

版を上げる（入力はリポジトリの根。出力は場所ごとの今の版と上げたあとの版）。
1. 根から 3 階層まで歩く。node_modules、仮想環境、ビルドの出力、tests、docs、.claude は降りない
2. 決まった名前のファイルから版を取り、版の文字の位置を覚える。JSON は字下げのいちばん浅い version、TOML は節の中の version
3. X.Y.Z の形だけ、Z を 1 つ上げる。ほかの形は注意を出して触らない
4. 書くときは、ファイルごとに後ろの位置から置き換える（桁が増えても前の位置がずれない）
端の場合: package-lock.json は先頭と packages の "" だけ。Cargo.lock は自分のパッケージの名前の次の行だけ。場所によって版が違えば注意を出し、勝手にそろえない。

## 技術
- 場所: `.claude/skills/bug-first/scripts/bugs.py` の `parse`、`set_fields`、`blocking_fatal`、`judge`、`stats`
- 場所: `.claude/skills/bug-first/scripts/version.py` の `places`、`plan`、`apply`、`release_workflows`
- 場所: `.claude/skills/bug-first/hooks/bug_prompt.py` の `report`、`start_line`
- 場所: `.claude/skills/bug-first/hooks/bug_gate.py` の `other_edits`、`.claude/skills/bug-first/hooks/crash_nudge.py` の `crash`、`traceback_sig`、`catch_up`
- 場所: `.claude/skills/bug-first/references/hotfix.md`（手順）、`.claude/skills/bug-first/references/severity.md`（重さ）
- テスト: `.claude/skills/bug-first/scripts/test_bugs.py`、`.claude/skills/bug-first/scripts/test_version.py`、`.claude/skills/bug-first/scripts/test_hooks.py`

## 実装
- bug-first のスキルとして入れ、`.claude/settings.json` とひな形に登録した（SessionStart、UserPromptSubmit、Stop、PostToolUse の Bash）
- テストの出力: `Ran 21 tests in 0.442s` `OK`（test_bugs.py）、`Ran 17 tests in 0.364s` `OK`（test_version.py）、`Ran 45 tests in 1.807s` `OK`（test_hooks.py）
- 動かして見つけた不具合: 帳簿の書き換えが、ひな形の見本の節（コメントの中）を書き換えていた。出力は「状態 未修正」のままで、見本の方が変わっていた。節を切るときにコメントの中を外して直し、テストにした
- 動かして見つけた不具合: Traceback の最後の行として、見出しの行そのものを取っていた。行頭の空白に改行も当てる正規表現（`\s*`）が、前の空行から当たっていた。空白とタブだけにして直した
- テストが効いているかを、スキルのコピーの 1 か所を壊して確かめた（14 か所）。最初の回は 1 か所が落ちなかった（package-lock.json の依存の行を外す条件が、作った入力では要らなかった）。取り方を直し、古い形の lock の入力を足して、14 か所とも `FAILED` になった。最後の行は `壊しても落ちないテスト 0`
- 実際の会話の記録（親の 1 本と、subagent の 3 本の写し。人の発言 9、Bash の結果 273、うち失敗 9）に判定を当てた出力: 発言の当たり 0（決まりを言う発言と、依頼文 3 本には出ない）、クラッシュの印 0。記録には、テストが落ちたときの Traceback と、ソースの表示が入っているが、どれも知らせなかった。本物のクラッシュは記録に無かったので、当たる側は作った入力（Python、Rust、Go、Node、ログ）で見た
- 差し込みの量（measure_hooks.py）: `SessionStart 合計 3848 文字（目安 5000）: 目安内`、`UserPromptSubmit 合計 1065 文字（目安 1200）: 目安内`。普段のターンと、帳簿の無いリポジトリでは、bug-first の 2 行は 0 文字。バグの報告のターン（「保存したらクラッシュする」）は合計 958 文字で、うち bug-first が 51 文字。帳簿に致命的と重いが 1 件ずつあるセッションの始めは 115 文字
- 目安を超える発言が 1 つあった。バグ修正の決まりそのものを言う発言（優先、バグ、致命的、修正版の語が並ぶ）は、skill-nudge.sh の行が 4 つ重なって合計 1243 文字になる。bug-first の行を 73 文字に縮めたが、残りはほかのスキルの行
- 確認のフックとの関係を、作った会話の記録で確かめた出力: ❔ のターンの Stop フック（done_check、ci_gate、reread_check、terms_check、guess_gate）は全部 `exit (0, '')`。返事のあとの pr_gate は、PR の作成・マージ・Release・タグの push が `(0, '')`。返事が無いときは `2`
- 配った先の形（そのリポジトリ自身の登録と許可がある settings.json、帳簿は無い）の写しに sync.py で配り、そこで動かした出力: `test_bugs.py exit 0 | Ran 21 tests in 0.399s  OK`、`test_version.py exit 0 | Ran 17 tests in 0.368s  OK`、`test_hooks.py exit 0 | Ran 45 tests in 1.961s  OK`、`hooks-smoke exit 0 | フックの誤り 0`。フックの 4 つの登録は無害な入力で `exit 0 出力 0 文字`。そのリポジトリ自身の許可（`permissions`）は、配る前のまま残った
- precheck で 1 件落ちた。テストに入れた 4 つ組の版の例が、content-audit のグローバルアドレスの検出に当たった（`確認 ciel ed9fc3d base=origin/main: 落ちた 50/51`）。例を日付の形の版に替えて通した。差分の検査は、HEAD との差分だけでなく、main ブランチとの差分に当てる
