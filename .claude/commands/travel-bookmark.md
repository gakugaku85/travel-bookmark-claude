# Travel Bookmark

行きたい場所や国を指定すると、Google Mapsの保存済みリストに観光スポットを自動追加します。

## 使い方
```
/travel-bookmark <目的地> [リスト名]
```
例: `/travel-bookmark パリ フランス旅行`

## 処理フロー

1. **旅行スタイルのヒアリング**: 旅のイメージや希望を深掘りする質問をする
2. **場所のリストアップ**: ヒアリング結果をもとに最適な観光スポットを10件提案する
3. **ユーザー確認**: 追加するスポットの一覧を表示し、確認を取る
4. **Google Mapsで保存**: Playwrightで各スポットをGoogle Mapsの保存済みリストに追加する

## 詳細手順

### Step 1: 旅行スタイルのヒアリング

スポットを提案する前に、以下の観点で旅のイメージを深掘りする質問をする。
一度に全部聞かず、会話形式で自然に引き出すこと。

**聞くべき観点：**
- **旅のスタイル**: 観光メイン？食べ歩き？ショッピング？自然・公園散策？アート・文化？
- **エリア**: 特定のエリアや街を歩きたい希望はあるか（例：下町、おしゃれエリア、歴史地区）
- **同行者**: 一人旅？カップル？家族連れ？友人グループ？
- **日数・ペース**: 何泊の予定か、ゆっくり派か詰め込み派か
- **こだわり**: 外せない体験や、逆に避けたいもの（混雑スポット、長距離移動など）
- **過去の旅**: 以前に行ったことがあれば、今回は何か違うものを求めているか

ヒアリングが終わったら、得られた情報をもとにスポットをカスタマイズして提案する。

### Step 2: 観光スポットを提案

ヒアリング結果を踏まえて、旅のスタイルに合ったスポットを10件選定する。
以下の情報を含むリストを作成する：
- スポット名（日本語・英語）
- 一言説明（なぜこの旅に合うかを添えると◎）
- カテゴリ（世界遺産・食事・自然・ショッピングなど）

### Step 3: ユーザーに確認

```
以下のスポットを「{リスト名}」に追加します。よろしいですか？
1. エッフェル塔 (Eiffel Tower) - 世界遺産・展望台
2. ルーブル美術館 (Louvre Museum) - 世界最大級の美術館
...
[y/n]
```

### Step 3: Playwrightツールの準備

実行前に必ずToolSearchでPlaywrightツールを読み込む：

```
ToolSearch: select:mcp__playwright__browser_navigate,mcp__playwright__browser_click,mcp__playwright__browser_snapshot,mcp__playwright__browser_wait_for,mcp__playwright__browser_type,mcp__playwright__browser_evaluate
```

スクリーンショット（`browser_take_screenshot`）は使用しない。

### Step 4: Google Mapsで自動保存

#### 4-1. 最初のスポット（新規リスト作成）

1. `https://www.google.com/maps/search/{スポット英語名}` に移動
2. スポット名が表示されるまで待機（`browser_wait_for`）
3. `button[aria-label='保存']` をクリック
4. `リストに保存` ダイアログが表示されるまで待機
5. `button[aria-label='新しいリスト']` または `button:has-text('新しいリスト')` をクリック
6. テキストボックス `input[type='text'][maxlength='40']` にリスト名を入力（デフォルト「無題のリスト」を上書き）
7. `button:has-text('作成')` をクリック
8. 「{リスト名}に保存しました」トーストが表示されることを確認

#### 4-2. 2件目以降のスポット

1. `https://www.google.com/maps/search/{スポット英語名}` に移動
2. スポット名が表示されるまで待機（`browser_wait_for`）
3. `button[aria-label='保存']` をクリック
4. `リストに保存` ダイアログが表示されるまで待機（`browser_wait_for: 'リストに保存'`）
5. JavaScriptでリストを選択（scrollIntoViewで確実に表示してからクリック）:

```javascript
() => {
  const items = document.querySelectorAll('[role="menuitemradio"]');
  const target = Array.from(items).find(el => el.textContent.includes('{リスト名}'));
  if (target) {
    target.scrollIntoView();
    target.click();
    return 'clicked: ' + target.textContent.trim().substring(0, 30);
  }
  return 'not found';
}
```

6. URLが変わり「{リスト名}に保存しました」が表示されることを確認

### 重要な実装ノート

- **メニューが閉じてしまう場合**: `browser_evaluate` でクリックする前に `browser_wait_for: 'リストに保存'` で確実に待機する
- **scrollIntoView必須**: リストが多い場合（10件以上）は「ロンドン旅行」が画面外にあるため、`scrollIntoView()` を呼んでからクリックする
- **保存ボタンのセレクタ**: `button[aria-label='保存']` が確実。`text=保存` は「保存済み」と競合するため使わない
- **リスト名入力欄のセレクタ**: `input[type='text']` は検索欄と競合するため、`input[aria-labelledby='ucc-9']` または `input[maxlength='40']` を使う
- **リストの順序**: 最近使ったリストが最上位に表示される。初回のみ下部にある可能性があるが、2件目以降は先頭に来る

### エラーハンドリング
- ログインが必要な場合: ユーザーにGoogle Mapsを開いてログインするよう案内
- スポットが見つからない場合: スキップしてログに記録
- リストが存在しない場合: 新規作成する（Step 4-1を参照）
- メニューが自動で閉じた場合: 保存ボタンを再クリックして再試行

## 注意事項
- Google Mapsにログイン済みの状態で実行すること
- Playwrightはブラウザを新規起動するため、既存のChromeセッションとは別になる（ログイン状態は引き継がれない場合がある）
- ログインが必要な場合はユーザーに手動でログインを依頼する
