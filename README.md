# Ciel — Skill Creator / Skill Collector

> 「解。……スキルを、創ります」

**Ciel（シエル）** は Claude 向けの **Skill** を作り、集め、鍛え直し、管理するための公開リポジトリです。
名前は『転生したらスライムだった件』の *智慧之王* から借りています。
解析（Collect）→ 創造（Create）→ 進化（Evolve）。それがこのリポジトリの役割です。

---

## ⚠️ このリポジトリは PUBLIC です

誰でも中身を見られます。更新するときは必ず以下を守ってください。

- **秘密情報を絶対に入れない** — APIキー / トークン / パスワード / 個人情報 / 社内URL・ホスト名
- 実在の人物・組織の内部資料をそのまま貼らない
- コミット前に `scripts/validate.sh` を実行する
- 一度 push した秘密情報は「消しても漏れたまま」。必ず鍵をローテートする

---

## 構成

```
.claude/skills/  スキル本体（1スキル = 1ディレクトリ）。ここに置くと Ciel でも有効になる
templates/       新規スキル用のひな形、個人設定のひな形
scripts/         検証・コーパス収集/解析スクリプト
docs/            設計方針・運用ルール
```

## スキルの形

各スキルは `.claude/skills/<skill-name>/SKILL.md` を持ちます。冒頭は YAML frontmatter：

```markdown
---
name: skill-name
description: いつこのスキルを使うか。トリガー条件を具体的に書く。
---

# Skill Name
本文（手順・原則・例）
```

- `name` はディレクトリ名と一致（小文字・ハイフン区切り）
- `description` は **発動条件** を書く場所。「何ができるか」より「いつ使うか」
- 補助ファイルは `references/` `scripts/` `assets/` に置き、SKILL.md から参照する

詳しくは [docs/GUIDELINES.md](docs/GUIDELINES.md)。
使い方とスキル一覧は [docs/USAGE.md](docs/USAGE.md)。
公開スキル271本を実測した観察記録は [docs/OBSERVATIONS.md](docs/OBSERVATIONS.md)。

## 使い方

```bash
git clone https://github.com/Maguro-JP/Ciel.git
./Ciel/scripts/install.sh <skill-name> ~/               # 自分の PC の全プロジェクトで使う
./Ciel/scripts/install.sh <skill-name> /path/to/repo    # そのリポジトリで使う（要コミット）
```

スマホや Web のセッションで使うなら、リポジトリの `.claude/skills/` に入れてコミットします。
`~/.claude/` に置いたものはその機械の中だけで、リモートのセッションには引き継がれません。

## 新しいスキルを作る

```bash
cp -r templates/skill-template .claude/skills/my-new-skill
$EDITOR .claude/skills/my-new-skill/SKILL.md
./scripts/validate.sh
```

## 収録スキル

| スキル | 用途 |
|---|---|
| [`skill-sync`](.claude/skills/skill-sync/) | Ciel のスキルをリポジトリに取り込む。差分があるものだけ入れ替える |
| [`skill-audit`](.claude/skills/skill-audit/) | 既存スキルを「発動しない / 誤爆する / 肥大化」の3観点で診断する |
| [`workspace-policy`](.claude/skills/workspace-policy/) | リポジトリでの進め方を一度だけ決めて記録する。規約を読んで選択肢を絞る |
| [`solo-pr-flow`](.claude/skills/solo-pr-flow/) | 個人開発の PR をCI確認からマージ・後片付けまで通す。停止条件つき |
| [`secret-leak-check`](.claude/skills/secret-leak-check/) | 機密情報の混入を走査し、漏洩時の対応順序まで案内する |
| [`auto-dev`](.claude/skills/auto-dev/) | 自律的に開発を進める。時間制限と優先指示を受け取り、止まる条件を持つ |
| [`ci-triage`](.claude/skills/ci-triage/) | GitHub のチェックを読み、落ちたステップまで特定して対処する |

## 個人設定

言語や応答の書き方のような、常に効いてほしい好みはスキルではなく
`~/.claude/CLAUDE.md` に置きます。ひな形は
[templates/personal-CLAUDE.md](templates/personal-CLAUDE.md)。

```bash
cat templates/personal-CLAUDE.md >> ~/.claude/CLAUDE.md
```

`~/.claude/` に置いたものはリポジトリに入らないので、共同開発者に影響しません。

## 貢献

[CONTRIBUTING.md](CONTRIBUTING.md) を読んでから PR を送ってください。

## ライセンス

[MIT](LICENSE)
