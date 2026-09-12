# Zwift Climb Portal Schedule Sync 🚵‍♂️📅

[Zwift Insider](https://zwiftinsider.com/climb-portal-schedule/) から Zwift Climb Portal の月間・週間・デイリースケジュールを自動スクレイピングし、Googleカレンダーなどに自動登録・定期同期するためのツールです。

---

## 🌟 主な特徴

- **完全自動スクレイピング**: ZwiftInsiderの公式カレンダーから最新のクライム予定（当月＋翌月）を自動抽出。
- **2種類のGoogleカレンダー連携方式**:
  1. **【推奨】iCalendar (.ics) URL自動購読**: 面倒なAPI設定不要。GitHub Actionsで毎日自動更新されるURLを一度Googleカレンダーに登録するだけで、常に最新の予定が自動反映されます（AppleカレンダーやOutlookでも使えます）。
  2. **Google Calendar API 直接同期**: 既存のGoogleカレンダーに直接イベントを差し込み・重複防止同期。
- **柔軟な表示モード**:
  - `individual`（推奨）: 1日3件の個別終日イベント（月替わり・週替わり・日替わり）。カレンダー上で一目で登る山が分かり、検索も簡単です。
  - `consolidated`: 1日1件のまとめ終日イベント。カレンダーのマスをすっきり保ちたい方向け。
- **ボーナスXPや詳細リンク付き**: 週替わりクライムの獲得XP（例: `500 XP`）やZwiftInsiderの山岳攻略記事リンクを自動付与。

---

## 🚀 Googleカレンダーへの登録手順

### 【方法A】 URL購読方式（一番おすすめ・設定3分）

GitHub Actionsによってリポジトリ内の `.ics` ファイルが毎日自動更新されます。

1. **カレンダーURLを取得**:
   本リポジトリを自分のGitHubアカウントにプッシュすると、以下のURLでカレンダーが参照可能になります（RawファイルURL）：
   ```text
   https://raw.githubusercontent.com/kurousa/zwift-climbportal-schedule-sync/main/dist/zwift_climb_portal.ics
   ```
   ※1日1件のまとめ表示が良い場合は `dist/zwift_climb_portal_consolidated.ics` を指定してください。

2. **Googleカレンダーに登録**:
   - PCのブラウザで [Googleカレンダー](https://calendar.google.com/) を開きます。
   - 左サイドバーの「**他のカレンダー**」の横にある「**＋**」をクリックします。
   - 「**URLから追加**」を選択します。
   - 上記の `.ics` のURLを貼り付け、「**カレンダーを追加**」をクリックします。

これだけで登録完了です！以後はGoogleカレンダーが自動的に定期同期（1日数回〜1日1回）してくれます。

---

### 【方法B】 Google Calendar API による直接同期

自分の特定のカレンダー（プライマリカレンダーや専用カレンダー）にAPI経由で直接イベントを書き込みたい場合の方法です。

#### 1. Google Cloud のセットアップ
1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成します。
2. **Google Calendar API** を有効化します。
3. 「認証情報」から **サービスアカウント** を作成し、JSONキーを発行・ダウンロードします（ファイル名を `service_account.json` として本プロジェクトのルートに配置）。
4. 登録先カレンダーの共有設定で、作成したサービスアカウントのメールアドレス（`xxx@xxx.iam.gserviceaccount.com`）に「予定の変更権限」を付与します。

#### 2. 同期コマンドを実行
```bash
python main.py --sync-gcal \
  --calendar-id "your_calendar_id@group.calendar.google.com" \
  --service-account service_account.json
```

---

## 💻 ローカル環境での使い方

### 1. セットアップ
Python 3.10以上が必要です。

```bash
# 仮想環境の作成
python3 -m venv .venv
source .venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 2. スクラップ＆.icsファイルの生成
```bash
# 個別イベント形式で出力（デフォルト: dist/zwift_climb_portal.ics）
python main.py

# まとめイベント形式で出力
python main.py -m consolidated -o dist/zwift_climb_portal_consolidated.ics

# 当月のみ（0ヶ月先まで）取得する場合
python main.py -n 0

# 詳細なログを表示
python main.py -v
```

### コマンドラインオプション一覧
| オプション | 説明 | デフォルト |
|---|---|---|
| `-o`, `--output` | `.ics` ファイルの出力先パス | `dist/zwift_climb_portal.ics` |
| `-m`, `--mode` | イベント形式 (`individual` または `consolidated`) | `individual` |
| `-n`, `--months-ahead` | 先読みする月数（`0`=当月のみ, `1`=当月+翌月） | `1` |
| `--calendar-name` | カレンダーの名称 | `Zwift Climb Portal` |
| `--sync-gcal` | Google Calendar APIに直接同期するフラグ | 無効 |
| `--calendar-id` | 同期先のGoogleカレンダーID | - |
| `--service-account` | サービスアカウントJSONのパス | - |
| `--dry-run` | 実際の書き込みを行わずテスト実行 | 無効 |
| `-v`, `--verbose` | デバッグログを表示 | 無効 |

---

## 🤖 GitHub Actions による自動定期同期

`.github/workflows/update-schedule.yml` により、毎日日本時間 午前3時（UTC 18:00）に自動でスクレイピングが実行され、最新のスケジュールがリポジトリの `dist/` ディレクトリにプッシュされます。

### Google Calendar API 同期を GitHub Actions で行う場合
リポジトリの **Settings** > **Secrets and variables** > **Actions** に以下を登録してください：
- `GOOGLE_SERVICE_ACCOUNT_KEY`: サービスアカウントの JSON キー全文
- `GOOGLE_CALENDAR_ID`: 対象のカレンダーID

---

## 🧪 テストの実行

```bash
.venv/bin/python3 -m unittest discover tests
```

---

## 📄 ライセンス
MIT License
