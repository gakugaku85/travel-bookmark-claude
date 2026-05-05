# travel-bookmark-claude

旅行先を伝えるだけで、Google Maps の保存済みリストに観光スポットを自動登録してくれる Claude Code プロジェクトです。

## 概要

`/travel-bookmark` コマンドを使うと、Claude が旅のスタイルをヒアリングしたうえで最適な観光スポットを提案し、Playwright 経由で Google Maps に自動ブックマークします。

## 使い方

Claude Code 上で以下のスラッシュコマンドを実行します：

```
/travel-bookmark <目的地> [リスト名]
```

**例：**
```
/travel-bookmark ロンドン イギリス旅行2025
/travel-bookmark パリ
```

## 機能

1. **旅行スタイルのヒアリング** — 旅のスタイル・同行者・日数・こだわりを会話形式で確認
2. **スポット提案** — ヒアリング結果をもとに観光スポットを 10 件カスタム提案
3. **ユーザー確認** — 追加するスポット一覧を表示して承認を取得
4. **Google Maps への自動保存** — Playwright で各スポットを保存済みリストに追加

## 必要な環境

- [Claude Code](https://claude.ai/code) がインストール済みであること
- Google Maps にログイン済みの状態で実行すること（初回はログインを求められる場合あり）

## セットアップ

```bash
git clone <this-repo>
cd travel-bookmark-claude
```

Claude Code でリポジトリを開けば、すぐに `/travel-bookmark` コマンドが使えます。

## 注意事項

- Playwright はブラウザを新規起動するため、既存の Chrome セッションとは別のログイン状態になります
- ログインが必要な場合は Claude が案内するので、手動でログインしてください
