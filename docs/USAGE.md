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

**Claude Code が読むのは `.claude/skills/` の下だけです。** 他の場所に置いても発動しません。

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

**自分で打つ。** `/` に続けてスキル名を入れます。

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

**Claude が判断して発動する。** description の条件に当てはまると自動で読み込まれます。
「CI 落ちてる」と言えば `ci-triage` が、「公開して大丈夫?」と言えば
`secret-leak-check` が立ち上がります。

ただし**簡単に片付く依頼では発動しません**。基本ツールで直接処理できてしまうためです。
スキルは面倒な多段階の作業に効きます。

## スキル一覧

| スキル | 何をするか | いつ呼ばれるか |
|---|---|---|
| `auto-dev` | 自律的に開発を進める。時間制限と優先指示を受け取る | 「自動で進めて」「あとは任せる」 |
| `solo-pr-flow` | PR をマージ・後片付けまで通す。停止条件つき | PR を作った直後、「マージして」 |
| `ci-triage` | チェックの失敗を、落ちたステップまで特定する | 「CI が落ちた」、チェック完了の通知 |
| `secret-leak-check` | 機密情報の混入を走査し、漏洩時の対応順序を案内する | 「秘密情報入ってない?」「公開前に確認」 |
| `workspace-policy` | リポジトリでの進め方を一度だけ決めて記録する | 初めて PR を作る前、「設定して」 |
| `skill-audit` | 既存スキルを診断する | 「このスキル発動しない」 |
| `skill-sync` | Ciel のスキルを取り込む。差分だけ入れ替える | 「スキルを入れて」「最新にして」 |

依存関係があります。

```
auto-dev ──┬─> solo-pr-flow ──┬─> workspace-policy   方針を読む
           │                  ├─> ci-triage          CI の失敗を見る
           │                  └─> secret-leak-check   差分の秘密情報を見る
           └─> ci-triage
```

`auto-dev` だけ入れても、PR やマージの判断は他のスキルに任せる形になっています。
まとめて入れるのが前提です。

## 設定ファイル

`.claude/policy/<GitHubの利用者名>.json` に、そのリポジトリでの方針を書きます。
`workspace-policy` が作ります。利用者ごとにファイルが分かれるので競合しません。

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
| `auto_merge` | solo-pr-flow | 確認なしでマージしてよいか |
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

凍結済み・fork・書き込み権限の無いリポジトリは対象外です。明示的に外したいものは
Ciel の `.claude/sync-exclude.txt` に書きます。

自動で配るのは Raphael（private）の役目です。毎週土曜 09:00（日本時間）に
Ciel を読んで、差分のあるリポジトリに `ciel-sync` ブランチで PR を出し、
本人しか見ていないリポジトリならマージまで進めます。

各リポジトリに workflow を置く必要はありません。以前はその形でしたが、
同じことをするジョブがリポジトリの数だけ動くため、Raphael の1本に集約しました。

Ciel に鍵は置きません。Ciel は public なので、全リポジトリへ書ける PAT を
置くと被害範囲が最大になります。鍵は private の Raphael にだけあります。
詳しくは [skill-sync の配り方](../.claude/skills/skill-sync/references/distribution.md)。

## トークンと CI の消費を抑える

`auto-dev` を長く回すと、ここが効いてきます。

**ループの間隔を長くする。** `loop_interval` を `"30m"` 以上にします。
変化が無いのに起きるのは枠を捨てるだけです。待つものが無いなら20〜30分、
CI の完了を待つならその所要時間に合わせます。

**push をまとめる。** `push_policy` を `"batch"` にすると、検証済みの変更を
まとめてから push します。CI を起動するためだけの push をしません。
ローカルで通っているものは CI でも通ります。

**会話を長く続けない。** 送信のたびに会話全体を送り直すので、長いほど1回が重く
なります。区切りのいいところで新しいセッションを開くのが、いちばん効きます。
リポジトリにコミットしたものは引き継がれるので、失うものはありません。

**PR の購読を切る。** CI 完了やマージのたびに起こされ、その1回ごとに会話全体を
読み直します。監視が要らないなら購読しない方が安上がりです。
