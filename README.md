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
skills/          公開スキル本体（1スキル = 1ディレクトリ）
templates/       新規スキル用のひな形
scripts/         検証スクリプト
docs/            設計方針・運用ルール
```

## スキルの形

各スキルは `skills/<skill-name>/SKILL.md` を持ちます。冒頭は YAML frontmatter：

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

## 使い方

```bash
git clone https://github.com/Maguro-JP/Ciel.git
cp -r Ciel/skills/<skill-name> ~/.claude/skills/
```

プロジェクト単位で使うなら `.claude/skills/` へ。

## 新しいスキルを作る

```bash
cp -r templates/skill-template skills/my-new-skill
$EDITOR skills/my-new-skill/SKILL.md
./scripts/validate.sh
```

## 貢献

[CONTRIBUTING.md](CONTRIBUTING.md) を読んでから PR を送ってください。

## ライセンス

[MIT](LICENSE)
