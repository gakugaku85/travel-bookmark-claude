# Google マップの「保存済みリスト」に直接保存する（Claude in Chrome）

Google マップの保存済みリストには書き込み用の公開 API がありません。どうしても
「保存済み」タブのリストに入れたいときだけ、ユーザー自身の Chrome（ログイン済み）を
**Claude in Chrome** 拡張経由で操作します。クラウドのコンテナ内ブラウザ（Playwright）は
Google にログインしていないので使いません。

## 前提

- `anthropic-skills:chrome-browser` スキルを先に読み込み、その手順で `mcp__claude-in-chrome__*` ツールを有効化する
- ユーザーの既存タブは触らず、新しいタブで作業する
- 1 件ごとに結果（保存できた / スキップ）を記録し、最後にまとめて報告する
- ツールが使えない（拡張が未接続など）場合はこの手順をやめ、SKILL.md の
  マイマップ取り込み手順を案内する

## 手順

各スポットについて `spots.json` の `maps_url`（`place_id` 付きならピンポイントで開く）に移動する。

### 最初の 1 件（リストを新規作成）

1. 場所のパネルが表示されるまで待つ
2. `button[aria-label='保存']` をクリック（`text=保存` は「保存済み」と衝突するので使わない）
3. 「リストに保存」ダイアログを待つ
4. 「新しいリスト」をクリック
5. リスト名入力欄 `input[maxlength='40']` に `list_name` を入力（検索欄と衝突するので `input[type='text']` は使わない）
6. 「作成」をクリックし、「{リスト名}に保存しました」を確認

既に同名リストがある場合は 2 件目以降の手順で選ぶ。

### 2 件目以降

1. 保存ボタンをクリックし、「リストに保存」ダイアログを待つ
2. 次の JavaScript でリストを選ぶ（リストが多いと画面外にあるため `scrollIntoView` 必須）

```javascript
() => {
  const items = document.querySelectorAll('[role="menuitemradio"]');
  const target = Array.from(items).find(el => el.textContent.includes('{リスト名}'));
  if (!target) return 'not found';
  target.scrollIntoView();
  target.click();
  return 'clicked: ' + target.textContent.trim().substring(0, 30);
}
```

3. 「{リスト名}に保存しました」を確認

## うまくいかないとき

- ダイアログがすぐ閉じる → ダイアログ表示を待ってから再度クリック
- スポットが見つからない → スキップして記録
- ログインを求められた → ユーザーにそのタブでログインしてもらい、完了を待って再開
- Google の UI は頻繁に変わる。セレクタが合わなければページのテキスト／アクセシビリティツリーを読み直して要素を探す
