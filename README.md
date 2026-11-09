# travel-bookmark-claude

行き先を伝えるだけで、旅のスタイルに合った観光スポットを提案し、Google マップで使える形にまとめてくれる Claude Code プロジェクトです。
**Claude Code on the web（claude.ai/code）やスマホアプリのクラウドセッションでもそのまま動きます。**

## 使い方

```
/travel-bookmark <目的地> [リスト名]
```

例:

```
/travel-bookmark ロンドン イギリス旅行2026
/travel-bookmark 台南
```

「来月パリに行くから観光スポットまとめて」のように話しかけるだけでも、スキルが自動で呼ばれます。

## 流れ

1. **ヒアリング** — 旅のスタイル・同行者・日数・避けたいものを選択式で確認
2. **スポット提案** — Web 検索で最新情報（閉館・予約制・新スポット）を確認しつつ 10 件提案
3. **確認** — 一覧を見て入れ替え・確定
4. **Google マップ用に出力** — `trips/<リスト名>/` に以下を生成
   - `spots.csv` / `spots.kml` … [Google マイマップ](https://www.google.com/mymaps) にインポートして地図化（Google マップアプリの「保存済み → マップ」で見られる）
   - `README.md` … 各スポットのワンタップ Google マップリンク
   - `spots.json` … 構造化データ
5. **旅程ページ** — スマホで開ける Artifact ページを公開（タップで Google マップへ）
6. **（任意）保存済みリストへ直接保存** — 希望すれば Claude in Chrome でログイン済みの自分の Chrome を操作し、☆保存済みリストに追加

## 以前の方式からの変更点

| | 旧 | 新 |
|---|---|---|
| 形式 | `.claude/commands/`（スラッシュコマンド） | `.claude/skills/`（Skill。自然文でも起動） |
| 保存方法 | Playwright MCP で新規ブラウザを起動し Google マップ UI を操作 | ファイル出力 + マイマップ取り込み（ブラウザ不要）。直接保存は Claude in Chrome でユーザー自身のブラウザを使用 |
| ログイン | 毎回新しいブラウザで手動ログインが必要 | 不要（直接保存時もユーザーのログイン済み Chrome を使う） |
| 実行場所 | ローカルのみ | クラウド・ローカルどちらでも |
| スポット情報 | モデルの知識のみ | Web 検索で最新情報を確認 |
| 座標 | なし | 任意で Google Places API (New) から place_id・座標を取得 |

## オプション: Google Places API で座標を付ける

座標と place_id があると、リンクがピンポイントで開き、KML も出力されます。

- ローカル: 環境変数 `GOOGLE_MAPS_API_KEY` を設定
- クラウドセッション: Claude がキー入力フォームを出すので、そこに入力（`places.googleapis.com` 宛てのネットワークシークレットとして保存され、チャットには残りません）

キーがなくても CSV の住所列でマイマップ側が位置を解決するので、取り込みは可能です。

## 手動でファイルだけ作る

```bash
python3 .claude/skills/travel-bookmark/scripts/build_exports.py \
  .claude/skills/travel-bookmark/examples/paris.json --out trips/sample
```

Python 3.9+（標準ライブラリのみ）。
