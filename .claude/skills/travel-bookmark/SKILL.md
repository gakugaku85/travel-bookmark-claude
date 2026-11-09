---
name: travel-bookmark
description: 行きたい場所を聞いて旅のスタイルをヒアリングし、最新情報で観光スポットを提案、Google マップで使える形（マイマップ用 CSV/KML・ワンタップリンク・旅程ページ）にまとめる。必要なら Claude in Chrome でユーザーの Google マップ保存済みリストにも直接保存する。「旅行」「観光スポット」「Google マップに保存」「ブックマーク」などの依頼で使う。
argument-hint: <目的地> [リスト名]
---

# Travel Bookmark

目的地（`$ARGUMENTS` の 1 語目）とリスト名（2 語目以降。なければ「{目的地}旅行」）を受け取り、
旅のスタイルに合ったスポットを Google マップで使える形にして届ける。

クラウドセッション（claude.ai/code・スマホアプリ）でもローカルでも同じ手順で動くように、
**ブラウザ操作に頼らないことを基本**とする。

## 1. ヒアリング（AskUserQuestion）

自由記述の往復ではなく `AskUserQuestion` で選択式にまとめて聞く（1 回の呼び出しで最大 4 問）。

- **旅のスタイル**（multiSelect）: 定番観光 / 食べ歩き / アート・文化 / 自然・公園 / ショッピング
- **同行者**: 一人旅 / カップル / 家族（子連れ） / 友人グループ
- **日数・ペース**: 日帰り〜1泊 / 2〜3泊 / 4泊以上 ・ ゆっくり派か詰め込み派か
- **避けたいもの・外せないもの**（multiSelect）: 混雑スポット / 長距離移動 / 高額な入場料 / 夜の外出

エリアの希望や過去の訪問歴など、選択肢にしにくいことは「Other」の自由入力で拾う。
目的地が曖昧（「ヨーロッパ」など）なら最初に都市を絞る質問を入れる。

## 2. スポット調査と提案

- `WebSearch` で最新情報を確認する（閉館・改装・予約制への変更・新スポット）。学習知識だけで決めない
- ヒアリング結果に合わせて **10 件** 選ぶ。エリアが偏りすぎないよう、移動の動線も考える
- 各スポットに: 日本語名・英語名（Google マップで引ける正式名）・カテゴリ・「なぜこの旅に合うか」の一言

一覧を表で見せ、`AskUserQuestion` で「この 10 件で作成 / 入れ替えたいものがある」を確認する。

## 3. スポットデータを書き出す

確定したら `trips/<リスト名のスラッグ>/input.json` に次の形式で保存する:

```json
{
  "destination": "パリ",
  "list_name": "フランス旅行",
  "spots": [
    {"name_ja": "エッフェル塔", "name_en": "Eiffel Tower", "category": "展望台", "note": "夜のライトアップが◎"}
  ]
}
```

（例: `.claude/skills/travel-bookmark/examples/paris.json`）

複数の都市を回る旅では、スポットごとに `"destination": "Zurich, Switzerland"` のように都市を指定する（トップレベルの `destination` より優先される）。既存のリストに都市を足すときは同じ `input.json` に追記して作り直す。

## 4. Google マップ用ファイルを生成

```bash
python3 .claude/skills/travel-bookmark/scripts/build_exports.py trips/<slug>/input.json --out trips/<slug>
```

- 出力: `spots.csv`（マイマップ取り込み用）、`README.md`（各スポットのワンタップ Google マップリンク）、`spots.json`、座標があれば `spots.kml`
- **座標と place_id を付けたい場合**は `--resolve` を付ける（Google Places API (New) を使用）
  - キーは環境変数 `GOOGLE_MAPS_API_KEY`、またはクラウドセッションなら `request_credential` で
    host `places.googleapis.com`・header `X-Goog-Api-Key` のネットワークシークレットとして保存してもらう（チャットに貼らせない）
  - キーがない・無効な場合はスクリプトが終了コード 2 で止まるので、`--resolve` なしで実行し直す。CSV の住所列でマイマップ側がジオコーディングするので、なくても取り込める

## 5. 届ける

1. **旅程ページ（推奨）**: 生成した内容から、スポットのカード・カテゴリ・Google マップリンク（`maps_url`）を並べた
   Artifact ページを公開する。スマホでそのまま開いてタップで地図に飛べる。座標があれば地図表示も付ける
2. **マイマップ取り込み**: `trips/<slug>/README.md` の手順（マイマップで新規作成 → `spots.csv` をインポート）を案内する
3. リポジトリで使っている場合は `trips/<slug>/` をコミット・プッシュする（クラウドのコンテナは消えるため）

## 6. （任意）保存済みリストに直接保存

ユーザーが「Google マップの保存済みリスト（☆）に入れたい」と言った場合のみ、
`references/save-with-chrome.md` の手順で **Claude in Chrome**（ユーザー自身のログイン済み Chrome）を使う。
コンテナ内のヘッドレスブラウザは Google にログインしていないので使わない。

## 最後の報告

- 作成したリスト名・件数、見つからなかった／スキップしたスポット
- 旅程ページのリンク、生成ファイルのパス、マイマップ取り込み方法
