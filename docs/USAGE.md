# 使い方

## 目次

- [スキルはどこに置くと効くのか](#スキルはどこに置くと効くのか)
- [入れる](#入れる)
- [呼び出す](#呼び出す)
- [スキル一覧](#スキル一覧)
- [設定ファイル](#設定ファイル)
- [更新する](#更新する)
- [トークンと CI の消費を抑える](#トークンと-ci-の消費を抑える)

## スキルはどこに置くと効くのか

Claude Code が読むのは `.claude/skills/` の下だけです。 他の場所に置いても発動しません。

| 置き場所 | PC | スマホ・Web | 共同開発者 |
|---|---|---|---|
| `~/.claude/skills/` | 効く | 効かない | 見えない |
| リポジトリの `.claude/skills/` | 効く | 効く | 見える |

スマホや Web のセッションは毎回コンテナが作り直されるので、`~/.claude/` に
置いたものは残りません。どこからでも使いたいなら、リポジトリに入れてコミットします。

同じ名前のスキルが両方にあるときは、`~/.claude/skills/` の方が勝ちます。

## 入れる

```bash
git clone https://github.com/Maguro-JP/Ciel.git

./Ciel/scripts/install.sh                          # 一覧を見る
./Ciel/scripts/install.sh auto-dev ~/              # この機械の全プロジェクト
./Ciel/scripts/install.sh --all /path/to/repo      # そのリポジトリに全部
```

リポジトリに入れた場合はコミットが要ります。

```bash
cd /path/to/repo
git add .claude/skills && git commit -m "Ciel のスキルを取り込む"
```

## 呼び出す

2通りあります。

自分で打つ。 `/` に続けてスキル名を入れます。

```
/auto-dev E=1d L=1h テストを先に通して
/ci-triage
/secret-leak-check
```

これは PC のターミナル版だけで使えます。スマホや Web の画面では
「認識されないコマンドです」と出ます。その場合は普通の文で頼みます。

```
auto-dev を使って。E=1d L=1h、TODO の空欄を優先
ci-triage で CI の失敗を見て
```

スキル名を文中に書けば、description の条件に当たって読み込まれます。

Claude が判断して発動する。 description の条件に当てはまると自動で読み込まれます。
「CI 落ちてる」と言えば `ci-triage` が、「公開して大丈夫?」と言えば
`secret-leak-check` が立ち上がります。

ただし簡単に片付く依頼では発動しません。基本ツールで直接処理できてしまうためです。
スキルは面倒な多段階の作業に効きます。

## スキル一覧

| スキル | 何をするか | いつ呼ばれるか |
|---|---|---|
| `work-style` | 確認してから動く、一つずつ、動かしてから完了、確かめていないことは言わない | 作業を引き受けた直後、完了と言う前 |
| `verify-before-done` | 動かした出力を貼る。本番の前に1件で試す。予約と結果を区別する | 「できました」と言う前、本番に当てる前 |
| `follow-instructions` | 指示に従う。ユーザーの一言が最優先。訂正は1文で認めて言われた通りに直す。セッション内の指示をフックが毎ターン差し込む | 「違う」「言った通りに」「勝手に変えるな」「聞いてない」 |
| `finish-first` | 成果物を1つずつ完成させる。完成条件を先に書く、1つずつ、戻せる判断はデフォルトで進める、完成は出力で判定 | 「完成させて」「いつ終わる?」「何か月も終わらない」「中途半端」 |
| `prompt-from-context` | 短い一言を、前の文脈から全文のプロンプト（対象・やること・形・完成条件）にしてから動く。読んだ形を ↩ で1行出す。聞き返さない | 「やれ」「それも」「同じように」「続けて」「直して」のような、対象や形の無い一言 |
| `desktop-app` | アプリはウィンドウで開き、機能は画面に置く。CLI ではなく GUI、ブラウザではなくアプリケーション | 「アプリにして」「ブラウザじゃなくて」「GUI で」「Setup.exe」 |
| `repo-bootstrap` | CLAUDE.md、フック、スキル、最小 CI を一度で置く | 新規リポジトリ、「初期設定して」 |
| `lessons` | 失敗を4行で記録し、開始時に「次から」だけ差し込む | 「また間違えた」、判定の誤りが分かったとき |
| `long-dev` | 終わりのない自律開発。原則に従い auto-dev を期限無しで回し続ける | 「ずっと開発を続けて」「継続的に改善して」 |
| `dev-report` | 日報・週報・月報。週報は来週の計画、月報は今月の週ごとの計画 | 「日報」「週報」「月報」、Routine |
| `scheduler` | Routine の作成・一覧・停止。cron の決まりと費用 | 「毎日回して」「定期実行して」「スケジュールを止めて」 |
| `auto-dev` | 自律的に開発を進める。時間制限と優先指示を受け取る | 「自動で進めて」「あとは任せる」 |
| `solo-pr-flow` | PR を作る前とマージの前に precheck を通し、出す内容を ❔ で見せて返事を待つ。返事なしに作らない・マージしない | PR を作る前、「マージして」 |
| `ci-triage` | チェックの失敗を、落ちたステップまで特定する | 「CI が落ちた」、チェック完了の通知 |
| `secret-leak-check` | 機密情報の混入をスキャンし、漏洩時の対応順序を案内する | 「秘密情報入ってない?」「公開前に確認」 |
| `content-audit` | 人に見られる前に中身を精査する。機密・個人情報・不快な表現。履歴と GitHub 側まで | 「人に見せて大丈夫?」「個人情報入ってない?」「public にして大丈夫?」 |
| `ja-proofread` | 日本語の精度を上げる。文字の混入・翻訳調・ら抜き・表記ゆれを機械で拾い、残りは読み直す | 「日本語を直して」「校正して」「文章を整えて」 |
| `token-efficiency` | トークンと文脈を節約する。フックが毎ターン決まりを差し込み、読み直しと再実行を知らせる | 「トークンを節約して」「文脈が膨らむ」「頭打ちになる」 |
| `workspace-policy` | リポジトリでの進め方を一度だけ決めて記録する | 初めて PR を作る前、「設定して」 |
| `skill-audit` | 既存スキルを診断する | 「このスキル発動しない」 |
| `skill-sync` | Ciel のスキルを取り込む。差分だけ入れ替える | 「スキルを入れて」「最新にして」 |
| `skill-upkeep` | セッションを観察してスキルを直し、新しく作る。Ciel 自身の自律開発 | 毎週土曜 0:00 JST の Routine、「スキルを見直して」 |
| `docs-upkeep` | README と docs を今のリポジトリに合わせる。壊れたリンク、無いファイル、一覧の抜け、辿れない文書を止める | スキルやスクリプトを足した・消したあと、「README が古い」「最新化して」 |
| `tidy` | 散らかさない決まり。月に 1 回の整理整頓（Routine の月初の回）。使い終えたブランチと一回きりの Routine の掃除 | 「散らかさないで」「整理して」「ブランチが多い」、月の最初の Routine |
| `patrol` | 自律開発を回しているリポジトリ全部の状態を 1 つの表で見る | 「動いてる?」「全体の状況は?」 |
| `pending` | 自律開発が脇に置いた判断待ちを、横断して見る・答える | 「判断待ちは?」「何を決めればいい?」 |
| `feedback-session` | セッションをフィードバック専用に整える。1 トピック 1 セッション 1 ブランチ | `feedback-session <トピック>`、「成果物だけ見せて」 |
| `self-learn` | 知らないことを調べて身につけ、次から使える形で残す | 「学習して」「○○風を覚えて」 |
| `shared-models` | AI の模型の置き場を 1 か所にそろえる | 「モデルの保存先」「モデルを共有」 |

依存関係があります。

```
auto-dev ──┬─> solo-pr-flow ──┬─> workspace-policy   方針を読む（あれば）
           │                  ├─> ci-triage          CI の失敗を見る
           │                  └─> secret-leak-check   差分の秘密情報を見る
           └─> ci-triage
```

`auto-dev` だけ入れても、PR やマージの判断は他のスキルに任せる形になっています。
まとめて入れるのが前提です。

## 設定ファイル

`.claude/policy/<GitHubのユーザー名>.json` に、そのリポジトリでの方針を書きます。
`workspace-policy` が作ります。ユーザーごとにファイルが分かれるので競合しません。

```json
{
  "version": 1,
  "user": "Maguro-JP",
  "repo": "Maguro-JP/Ciel",
  "auto_merge": true,
  "merge_method": "squash",
  "delete_branch": true,
  "draft_is_default": true,
  "max_open_prs": null,
  "human_review_required": false,
  "loop_interval": null,
  "push_policy": "batch",
  "protected_paths": [".github/workflows/"],
  "policy_checks": [],
  "acknowledged": []
}
```

主なもの。

| キー | 効くスキル | 意味 |
|---|---|---|
| `auto_merge` | solo-pr-flow | 確認なしでマージしてよいか。ユーザーが「確認なし」と言ったときだけ効く |
| `human_review_required` | solo-pr-flow | true なら自動マージしない。規約から自動で立つ |
| `max_open_prs` | solo-pr-flow | 同時に開いてよい PR の本数 |
| `loop_interval` | auto-dev | ループの間隔。`"30m"` `"2h"` など。`null` は自動 |
| `push_policy` | auto-dev | `"batch"` はまとめて push、`"never"` は push しない |
| `policy_checks` | ci-triage | 規約を検査する CI の名前。落ちてもコードを直さない |

## 更新する

Ciel は public なので、認証なしで取り直せます。

```bash
cd /path/to/Ciel && git pull
./scripts/install.sh --all /path/to/repo
cd /path/to/repo && git add .claude/skills && git commit -m "Ciel のスキルを更新"
```

`skill-sync` を使うと、差分があるものだけ入れ替わります。同じなら何も出ません。

```bash
git -C Ciel pull
Ciel/.claude/skills/skill-sync/scripts/sync.py /path/to/repo --apply
cd /path/to/repo && git add .claude/skills && git commit -m "Ciel のスキルを更新"
```

アーカイブ済み・fork・書き込み権限のないリポジトリは対象外です。明示的に外したいものは
Ciel の `.claude/sync-exclude.txt` に書きます。

自動で配るのは配布用の private リポジトリの役目です。毎週土曜 09:00（日本時間）に
Ciel を読んで、差分のあるリポジトリに `ciel-sync` ブランチで PR を出し、
本人しか見ていないリポジトリならマージまで進めます。

各リポジトリに workflow を置く必要はありません。以前はその形でしたが、
同じことをするジョブがリポジトリの数だけ動くため、配布用の 1 本に集約しました。

Ciel に鍵は置きません。Ciel は public なので、全リポジトリへ書ける PAT を
置くと被害範囲が最大になります。鍵は配布用の private リポジトリにだけあります。
詳しくは [skill-sync の配り方](../.claude/skills/skill-sync/references/distribution.md)。

## トークンと CI の消費を抑える

`auto-dev` を長く回すと、ここが効いてきます。

ループの間隔を長くする。 `loop_interval` を `"30m"` 以上にします。
変化がないのに実行されるのは枠を捨てるだけです。待つものがないなら20〜30分、
CI の完了を待つならその所要時間に合わせます。

push をまとめる。 `push_policy` を `"batch"` にすると、検証済みの変更を
まとめてから push します。CI を起動するためだけの push をしません。
ローカルで通っているものは CI でも通ります。

会話を長く続けない。 送信のたびに会話全体を送り直すので、長いほど 1 回が重く
なります。区切りのいいところで新しいセッションを開くのが、いちばん効きます。
リポジトリにコミットしたものは引き継がれるので、失うものはありません。

PR の購読を切る。 CI 完了やマージのたびに起動され、その 1 回ごとに会話全体を
読み直します。監視が要らないなら購読しない方が安上がりです。
