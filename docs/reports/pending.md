# 判断待ち

ユーザーに決めてほしいこと。答えが付いたら「答え:」を足し、反映したら「反映済み」と書く。
自律で回っているとき、PR の作成とマージはユーザーの返事が要るので、返事が無い回はここに「PR 待ち」と書いて次の作業へ進む。

## 2026-10-31 PR 待ち: 10/25〜10/26 の直しと、スキルの手入れ 2026-W44
- 決めてほしいこと: 作業ブランチ claude/skill-management-repo-t0s4jc（出す前の確認、散らかさない、docs-upkeep、月に 1 回の整理整頓、user-terms、W44 の週報）を PR にしてマージしてよいか。同じ返事で、9 リポジトリへの配布と、Ciel の PR 本文のセッションの URL の削除も進める
- 推す案: 進める。precheck は通っている（会話の ❔ に HEAD を書いた）
- 決まるまで: このブランチに積む。PR は作らない
- 答え（2026-10-31）: 任せる。Ciel の #89 をマージし、10 本へ配った。反映済み

## 2026-10-31 配布の Actions が、アカウントの課金で始まらない
- 決めてほしいこと: 配布用の private リポジトリの Actions は 10/17 から 3 回とも「recent account payments have failed or your spending limit needs to be increased」で始まっていない。GitHub の Billing & plans で支払いか使用上限を直すか、配布を Actions からこのセッションの週 1 回のルーティン（skill-sync で配り、PR の作成は ❔ で確認）へ移すか
- 推す案: 支払いか上限を直す。Actions の配布は、手元に clone の無いリポジトリにも届く
- 決まるまで: 手で配る。為替の自動売買のリポジトリには claude/SYNC-20261031 を用意した

## 2026-11-02 Dependabot alerts の有効化は、このセッションからできない

- 何: Ciel のスキルを配っている 10 本のリポジトリで Dependabot alerts を有効にする（vuln-watch の補い）
- 止まった所: GitHub の API の `vulnerability-alerts` のパスは、このセッションの経路（リポジトリ単位のプロキシ）で HTTP 403。リポジトリの設定を書き換える `PATCH` は auto mode の classifier（Account & Standing-Rule Changes）で止められた
- ユーザーにしかできないこと: 各リポジトリの Settings → Code security → Dependabot alerts を有効にする。有効にしたら、この項目を「反映済み」にする
- それまで: vuln-watch の毎日のルーティン（OSV・CISA KEV・JVN）で見る

## 2026-11-02 pr_gate の 2 つの不具合は、AI からは直せない

- 何: `verify-before-done/hooks/pr_gate.py` が、Stop フックの差し戻しの文（「Stop hook feedback: …」）を人の発言と数えるので、❔ と返事の間に差し戻しが挟まると「確認なし」になる。PR の番号が付く前にブランチの名前で聞いた ❔ を、マージのときに数えない
- 止まった所: フックの直しは auto mode の classifier（AI が自分のゲートを直す判定）で止められた
- ユーザーにしかできないこと: `SYSTEMISH` に `Stop hook feedback` を足す。`approval()` の `matches` で、PR の番号が無いときは今のブランチの名前でも数える。直したら、この項目を「反映済み」にする
- それまで: ❔ の返事が来たら、別の文が挟まる前にマージを呼ぶ。止まったら、PR の番号を入れた ❔ を 1 行出し直す

## 2026-11-07 PR 待ち: user-emotion と、スキルの手入れ 2026-W45

- 何: ブランチ claude/user-emotion-20261102（user-emotion、session-watch の窓の直し、rules_sync.py、教訓 5 件、週報 2026-W45）を PR にしてマージし、10 本に配る
- 待っているもの: ❔ への返事（11/2 に出した）。返事があれば PR を作り、main に入れて配る
- それまで: 配布の 2 回目（skill-request と見回りの決まり）は 10 本のブランチに積んであり、base への push も同じ返事を待つ
- 答え（2026-11-07）: 進める。Ciel の #95 を main に入れ、9 本の base に push した（1 本は draft の PR のまま）。反映済み

## 2026-11-07 reread_check.py の誤検知は、AI からは直せない

- 何: `verify-before-done/hooks/reread_check.py` が、記録のファイルへの追記（`echo exit=$? >> x.log`）を編集に数え、裏の処理を始めただけの返答に読み直しを求める（この週に 4 回）
- 止まった所: フックの直しは auto mode の classifier（AI が自分のゲートを直す判定）で止められた
- ユーザーにしかできないこと: `BASH_EDIT` の `>>` の部分を `(?<![|&<>])>>\s*(?!/tmp/)(?!\S*\.(?:log|out|txt)\b)\S` にする。直したら、この項目を「反映済み」にする

## 2026-11-14 PR 待ち: 魅せる README・リポジトリ管理・確認・通知・調べ物のスキルと、スキルの手入れ 2026-W46

- 何: ブランチ claude/readme-repo-20261107（readme-showcase、repo-management、code-check、actions-watch、research-to-tech、sync.py と finish-first と observe.py の直し、教訓 6 件、週報 2026-W46）を PR にする。作ったら購読し、Actions の結果が来てからマージの確認を出し、マージのあと 10 本に配る
- 待っているもの: 確認の行への返事（11/7 から出している）。precheck は通っている
- それまで: このブランチに積む。PR は作らない。新しいフック（code-check、actions-watch、research-to-tech）は、main に入って配られ、新しく開いたセッションから効く
- 答え（2026-11-14）: 進める。自律開発の回なので、この PR は作成・Actions の結果の確認・マージ・配布まで聞き直さずに進める
