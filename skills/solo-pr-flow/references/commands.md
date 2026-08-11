# コマンド対応表

環境によって使える道具が違う。手元にある方を使う。

## 状態の取得

| 欲しい情報 | GitHub CLI | MCP (github) |
|---|---|---|
| PR 詳細 | `gh pr view <n> --json state,isDraft,mergeable,mergeStateStatus,baseRefName` | `pull_request_read` method=`get` |
| チェック状況 | `gh pr checks <n>` | `pull_request_read` method=`get_check_runs` |
| レビュー | `gh pr view <n> --json reviews` | `pull_request_read` method=`get_reviews` |
| 変更ファイル | `gh pr diff <n> --name-only` | `pull_request_read` method=`get_files` |

一度に必要な分をまとめて取る。1項目ずつ往復しない。

## マージ

```bash
gh pr merge <n> --squash --delete-branch
gh pr merge <n> --merge  --delete-branch
gh pr merge <n> --rebase --delete-branch
```

MCP なら `merge_pull_request`（`merge_method`: `squash` / `merge` / `rebase`）。
ブランチ削除は別途 `delete_file` ではなく git 側で行う:

```bash
git push origin --delete <branch>
```

## 後片付け

```bash
git checkout <default-branch>
git pull origin <default-branch>
git branch -d <branch>          # -D は使わない（未マージを消してしまう）
```

既定ブランチ名の取得:

```bash
git symbolic-ref --short refs/remotes/origin/HEAD | sed 's#^origin/##'
```

## 判定に使う値

### mergeable_state / mergeStateStatus

| 値 | 意味 | 自動マージ |
|---|---|---|
| `clean` | 問題なし | ✅ |
| `blocked` | 必須チェック未完了、レビュー未承認など | ❌ 原因を特定する |
| `behind` | base に遅れている | base を取り込んで push |
| `dirty` | コンフリクト | 解決してから |
| `unstable` | 非必須チェックが失敗 | 内容を見て判断 |
| `unknown` | GitHub が計算中 | 少し置いて取り直す |

### チェックランの status / conclusion

`status` が `completed` になって初めて `conclusion` を見る。
`queued` / `in_progress` の間は判定を保留し、**完了通知を待つ**。

`conclusion` の扱い:

| 値 | 扱い |
|---|---|
| `success` | 合格 |
| `skipped` / `neutral` | 合格扱いでよい |
| `failure` / `timed_out` | 不合格。直す |
| `cancelled` | 再実行するか、原因を確認 |
| `action_required` | 人の操作が必要。尋ねる |

## 自動マージ機能を使う場合

CI 完了を待たずに予約したいときは GitHub 側の auto-merge を使う手もある。

```bash
gh pr merge <n> --squash --auto --delete-branch
```

ただし**リポジトリ設定で auto-merge が有効**かつ**ブランチ保護ルールが必要**。
個人リポジトリでは無効なことが多いので、使えなければ通常のマージに切り替える。
