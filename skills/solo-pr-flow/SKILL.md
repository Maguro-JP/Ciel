---
name: solo-pr-flow
description: 個人開発リポジトリで PR を作成してからマージ・後片付けまでを、毎回の確認なしに最後まで進めるとき。PR を作った直後、「マージして」「CIが通ったらマージ」「PRの後片付け」「ブランチ消して」といった依頼、CI 完了の通知を受けたときに使う。opt-in マーカー（.claude/solo-pr.json）がある、または利用者がそのリポジトリを個人開発だと明言したリポジトリでのみ自動マージを行い、複数人が関わるリポジトリや保護されたブランチでは使わない。
---

# Solo PR Flow

個人開発では「PR を作る → CI を待つ → マージ → ブランチを消す」が毎回同じ。
このスキルは、**opt-in したリポジトリに限って**その一連を確認なしで完走させる。

## 発動の前提: opt-in の確認（省略不可）

自動マージは取り消しにくい操作なので、**必ず最初に確認する**。

1. リポジトリ直下の `.claude/solo-pr.json` を読む。あれば opt-in 済み
2. 無い場合、利用者がこのセッションで「個人開発だから自動でマージしていい」と
   明言していればその宣言を根拠にしてよい
3. どちらも無ければ**自動マージしない**。代わりに 1 回だけこう尋ねる:

   > このリポジトリを自動マージ対象にしますか? `.claude/solo-pr.json` を作れば以後は確認なしで進めます。

`assets/solo-pr.json` がテンプレート。作成したらそのまま使う。

## 設定

```json
{
  "auto_merge": true,
  "merge_method": "squash",
  "delete_branch": true,
  "require_ci": true,
  "require_ci_when_no_checks": "proceed",
  "protected_paths": [".github/workflows/", "scripts/"]
}
```

| キー | 意味 |
|---|---|
| `auto_merge` | false なら診断だけして止まる |
| `merge_method` | `squash` / `merge` / `rebase` |
| `delete_branch` | マージ後にリモートブランチを削除 |
| `require_ci` | CI 全緑を必須にする |
| `require_ci_when_no_checks` | チェックが1つも無いとき `proceed` か `ask` |
| `protected_paths` | ここに触れる差分があるときは自動マージせず必ず確認する |

未設定のキーは上の値を既定とする。

## 手順

### 1. PR の状態を1回で集める

- PR の state / draft / base ブランチ
- `mergeable_state`（コンフリクトの有無）
- チェックラン全件の status と conclusion
- レビューの状態（CHANGES_REQUESTED があるか）
- 変更ファイル一覧（`protected_paths` 判定用）

### 2. 判定する

**全部 満たせば即マージする。利用者に尋ねない。**

- [ ] opt-in 済み（上の前提を満たす）
- [ ] `auto_merge: true`
- [ ] PR が open かつ **draft でない**
- [ ] base がそのリポジトリの既定ブランチ
- [ ] `mergeable_state` がコンフリクトなし
- [ ] チェックが全て completed かつ success（`require_ci: true` のとき）
- [ ] CHANGES_REQUESTED のレビューが無い
- [ ] 変更が `protected_paths` に触れていない

**1つでも欠けたら、下の分岐に従う。**

### 3. 満たさないときの分岐

| 状況 | 動作 |
|---|---|
| CI が実行中 / queued | **待つ。ポーリングしない。** 完了通知で起こされてから再判定する |
| CI が失敗 | 原因を調べて直し、push する。直せないなら理由を1〜2行で報告して止まる |
| コンフリクト | base を取り込んで解決し、push。解決が一意でないときだけ尋ねる |
| draft のまま | draft を外してよいか尋ねる。勝手に外さない |
| CHANGES_REQUESTED | 自動マージしない。指摘へ対応する |
| `protected_paths` に該当 | 該当ファイル名を挙げてマージ可否を尋ねる |
| チェックが1つも無い | `require_ci_when_no_checks` に従う |

### 4. マージする

`merge_method` でマージする。コミットメッセージは PR タイトルを使い、本文は要点のみに絞る。

### 5. 後片付け

1. `delete_branch: true` ならリモートブランチを削除
2. ローカルを既定ブランチに切り替えて pull
3. マージ済みのローカルブランチを削除
4. **PR の監視を購読していれば解除する**

### 6. 報告

1〜3行。マージ済みなら PR 番号・マージ方式・後片付けの結果。それだけ。
長い要約は書かない。差分が記録なので。

## 原則

- **opt-in の確認を飛ばさない。** これが唯一の安全装置
- **CI 待ちで sleep やポーリングをしない。** 完了通知で起きて再判定する
- **main へ force push しない。** どんな状況でもしない
- **他人の PR には使わない。** 自分（または利用者）が作った PR のみ
- 判定を満たしたら**尋ねずにマージする**。それがこのスキルの存在理由
- 判定を満たさないのに「たぶん大丈夫」で進めない

## 参考

GitHub CLI / MCP それぞれでの具体的なコマンド対応は `references/commands.md` を読む。
