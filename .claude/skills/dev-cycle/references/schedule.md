# 定期実行の設定

## Routine で起こす

Claude Code のセッションから Routine を作る。cron は UTC で、分は 0。

```
名前: dev-cycle daily
cron: 0 0 * * *        # 毎日 09:00 JST
プロンプト: dev-cycle daily を実行する。auto-dev の原則に従い、変更不要なら変更不要と報告する。

名前: dev-cycle weekly
cron: 0 0 * * 1        # 月曜 09:00 JST
プロンプト: dev-cycle weekly を実行する。

名前: dev-cycle monthly
cron: 0 0 1 * *        # 毎月1日 09:00 JST
プロンプト: dev-cycle monthly を実行する。
```

毎回新しいセッションで起こす形（create_new_session_on_fire）にする。
同じセッションに積むと、会話が長くなって1回ごとのトークンが増える。

## 権限

Routine のセッションは、作ったときのセッションと同じリポジトリと権限で動く。
push とマージをさせるなら、そのリポジトリが書き込み可能な状態で Routine を作る。

## 止め方

Routine を無効にする。消さなくてよい。再開するときは有効に戻す。

## 費用

1回の起動が1セッション分。daily を毎日回すと月に約30セッション。
変更不要の日は調査だけで終わるので軽いが、ゼロではない。
Actions は PR を作った日だけ走る。
