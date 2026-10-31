# Ciel

Claude Code のスキルを作り、集め、直し、配るための公開リポジトリです。
名前は『転生したらスライムだった件』の智慧之王から借りています。

## このリポジトリは public です

誰でも中身を見られます。更新するときは次を守ります。

- 機密情報（API キー、トークン、パスワード、個人情報、社内の URL やホスト名）を入れない
- 非公開のリポジトリの名前、メールアドレス、セッションやルーティンの ID、費用の数字を書かない。コミットメッセージと PR の本文にも書かない
- コミットの前に `scripts/validate.sh` を通す
- 一度 push した機密情報は、消しても漏れたまま。鍵はローテートする

## 構成

```
.claude/skills/        スキル本体（1 スキル = 1 ディレクトリ）。Ciel 自身でも効く
.claude/hooks/         全リポジトリに配るフック（言語の決まり、場面の案内、失敗の記録の差し込み）
.claude/settings.json  フックの登録
templates/             新しいスキルのひな形と、個人設定のひな形
scripts/               validate.sh（検証）、install.sh（取り込み）、hooks-smoke.py（フックの煙テスト）、コーパスの収集と解析
docs/                  設計方針、使い方、権限の層、振る舞いの対応表、出典、報告
```

## スキルの形

各スキルは `.claude/skills/<skill-name>/SKILL.md` を持ちます。冒頭は YAML の frontmatter です。

```markdown
---
name: skill-name
description: いつこのスキルを使うか。発動の条件を具体的に書く。
---

# Skill Name
本文（手順、原則、例）
```

- `name` はディレクトリ名と一致させる（小文字とハイフン）
- `description` には発動の条件を書く。「何ができるか」より「いつ使うか」
- 補助ファイルは `references/` `scripts/` `hooks/` に置き、SKILL.md から参照する

## 使い方

```bash
git clone https://github.com/Maguro-JP/Ciel.git
./Ciel/scripts/install.sh <skill-name> ~/               # 自分の PC の全プロジェクトで使う
./Ciel/scripts/install.sh <skill-name> /path/to/repo    # そのリポジトリで使う（コミットが要る）
```

スマホや Web のセッションで使うには、リポジトリの `.claude/skills/` に入れてコミットします。
`~/.claude/` に置いたものはその機械の中だけで、リモートのセッションには引き継がれません。
取り込みと更新の詳しい手順は [docs/USAGE.md](docs/USAGE.md) にあります。

## 新しいスキルを作る

```bash
cp -r templates/skill-template .claude/skills/my-new-skill
$EDITOR .claude/skills/my-new-skill/SKILL.md
./scripts/validate.sh
```

作る前に公開されているスキルを探し、使えるなら取り込んで直します。出典は [docs/SOURCES.md](docs/SOURCES.md) に書きます。

## 収録スキル

姿勢と指示

| スキル | 用途 |
|---|---|
| [`work-style`](.claude/skills/work-style/) | 仕事の進め方。確認してから動く、1 つずつ、動かしてから完了と言う、確かめていないことは言わない |
| [`follow-instructions`](.claude/skills/follow-instructions/) | 指示に従う。ユーザーの一言をスキルやチェックより上に置き、訂正は 1 文で認めて言われた通りに直す。AI は自分に権限を付与しない |
| [`prompt-from-context`](.claude/skills/prompt-from-context/) | 短い一言を、前の文脈から全文のプロンプトにしてから動く。聞き返さない |
| [`finish-first`](.claude/skills/finish-first/) | 成果物を 1 つずつ完成させる。完成条件を先に書き、戻せる判断はデフォルトで進める |
| [`lessons`](.claude/skills/lessons/) | 失敗の記録。場面・起きたこと・判定の誤り・次から の 4 行で残し、開始時にフックが差し込む |
| [`token-efficiency`](.claude/skills/token-efficiency/) | トークンと文脈を節約する。フックの差し込み量を測る |

出す前の検証

| スキル | 用途 |
|---|---|
| [`verify-before-done`](.claude/skills/verify-before-done/) | 完了の語をツールの出力と照合する Stop フック。PR・マージ・main への push の前の precheck と確認ゲート |
| [`secret-leak-check`](.claude/skills/secret-leak-check/) | 機密情報の混入を調べ、漏れたときの順序を案内する |
| [`content-audit`](.claude/skills/content-audit/) | 人に見られる前に中身を精査する。名前、ID、費用、履歴、GitHub 側、不快な表現 |
| [`ja-proofread`](.claude/skills/ja-proofread/) | 日本語の精度を上げる。文字の混入、翻訳調、訳語、表記ゆれ |
| [`user-terms`](.claude/skills/user-terms/) | 略語・訳語・造語を、ユーザーが使った語に直す。Stop フックが会話を止め、precheck が文書を注意として出す |
| [`docs-upkeep`](.claude/skills/docs-upkeep/) | README と docs を今のリポジトリに合わせる。壊れたリンク、無いファイル、一覧の抜け、辿れない文書を止める |

PR と CI

| スキル | 用途 |
|---|---|
| [`solo-pr-flow`](.claude/skills/solo-pr-flow/) | 出す前の確認（precheck と ❔ への返事）を取ってから、PR の作成・マージ・後片付けまで通す |
| [`ci-triage`](.claude/skills/ci-triage/) | GitHub のチェックを読み、落ちたステップまで特定して対処する |
| [`workspace-policy`](.claude/skills/workspace-policy/) | リポジトリでの進め方を一度だけ決めて記録する |
| [`tidy`](.claude/skills/tidy/) | 散らかさない決まり、月に 1 回の整理整頓、使い終えたブランチやルーティンの整理整頓 |

自律開発と定期実行

| スキル | 用途 |
|---|---|
| [`auto-dev`](.claude/skills/auto-dev/) | 自律的に開発を進める。時間制限と優先の指示を受け取り、止まる条件を持つ |
| [`long-dev`](.claude/skills/long-dev/) | 終わりのない自律開発。auto-dev をルーティンで回し続ける |
| [`dev-report`](.claude/skills/dev-report/) | 日報・週報・月報 |
| [`scheduler`](.claude/skills/scheduler/) | ルーティンの作成・一覧・停止と cron の決まり |
| [`patrol`](.claude/skills/patrol/) | 自律開発を回しているリポジトリ全部の状態を 1 つの表で見る |
| [`pending`](.claude/skills/pending/) | 自律開発が脇に置いた判断待ちを、リポジトリを横断して見る・答える |
| [`feedback-session`](.claude/skills/feedback-session/) | セッションをフィードバック専用に整える。1 トピック 1 セッション 1 ブランチ |
| [`self-learn`](.claude/skills/self-learn/) | 知らないことを調べて身につけ、次から使える形で残す |

アプリと模型

| スキル | 用途 |
|---|---|
| [`desktop-app`](.claude/skills/desktop-app/) | アプリはウィンドウで開き、機能は画面に置く。CLI ではなく GUI、ブラウザではなくアプリケーション |
| [`shared-models`](.claude/skills/shared-models/) | AI の模型の置き場を 1 か所にそろえる |

スキルの管理

| スキル | 用途 |
|---|---|
| [`skill-sync`](.claude/skills/skill-sync/) | Ciel のスキルをリポジトリに取り込む。差分があるものだけ入れ替える |
| [`skill-audit`](.claude/skills/skill-audit/) | 既存スキルを「発動しない / 誤爆する / 肥大化 / 干渉」で診断する |
| [`skill-upkeep`](.claude/skills/skill-upkeep/) | セッションを観察してスキルを直し、新しく作る。Ciel 自身の自律開発 |
| [`repo-bootstrap`](.claude/skills/repo-bootstrap/) | リポジトリに CLAUDE.md、フック、スキル、最小の CI を一度で置く |

## 文書

| 文書 | 何 |
|---|---|
| [docs/USAGE.md](docs/USAGE.md) | 取り込み方、呼び出し方、スキル一覧と発動の条件、方針のファイル、更新の仕方 |
| [docs/GUIDELINES.md](docs/GUIDELINES.md) | スキルの設計方針と、スキルどうしの干渉と優先 |
| [docs/PERMISSIONS.md](docs/PERMISSIONS.md) | 権限と許可の層。何が止めるか、どう直すか |
| [docs/BEHAVIOR.md](docs/BEHAVIOR.md) | 指摘された振る舞いと、それを止める仕組みの対応 |
| [docs/SOURCES.md](docs/SOURCES.md) | 取り込んだ公開スキルの出典とライセンス |
| [docs/OBSERVATIONS.md](docs/OBSERVATIONS.md) | 公開スキルを実測した観察記録 |
| [docs/reports/](docs/reports/) | 成果物の表と週報 |

## 個人設定

言語や応答の書き方のような、常に効いてほしい好みは `~/.claude/CLAUDE.md` に置きます。
ひな形は [templates/personal-CLAUDE.md](templates/personal-CLAUDE.md) です。

```bash
cat templates/personal-CLAUDE.md >> ~/.claude/CLAUDE.md
```

## 貢献とライセンス

[CONTRIBUTING.md](CONTRIBUTING.md) を読んでから PR を送ってください。ライセンスは [MIT](LICENSE) です。
