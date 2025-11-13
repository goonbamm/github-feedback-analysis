# 🚀 GitHub フィードバック分析

開発者としてフィードバックが欲しいのに、年末の振り返りをしたいのに、どこから始めればいいかわからない？GitHubで**あなたの活動**を分析し、インサイトに富んだレポートを自動生成するCLIツールです。GitHub.comとGitHub Enterpriseの両方をサポートし、LLMベースの自動レビュー機能を提供します。

日本語 | [한국어](../README.md) | [English](README_EN.md) | [简体中文](README_ZH.md) | [Español](README_ES.md)

## ✨ 主な機能

- 📊 **個人活動分析**：特定のリポジトリで**あなたの**コミット、イシュー、レビューアクティビティを期間別に集計・分析
- 🤖 **LLMベースのフィードバック**：あなたのコミットメッセージ、PRタイトル、レビュートーン、イシュー品質の詳細分析
- 🎯 **統合振り返りレポート**：個人活動指標と共に総合的なインサイトを提供
- 🏆 **アチーブメント可視化**：あなたの貢献度に応じてアワードとハイライトを自動生成
- 💡 **リポジトリ探索**：アクセス可能なリポジトリのリスト表示とアクティブなリポジトリの推奨
- 🎨 **インタラクティブモード**：リポジトリを直接選択できるユーザーフレンドリーなインターフェース

## 📋 前提条件

- Python 3.11以上
- [uv](https://docs.astral.sh/uv/)またはお好みのパッケージマネージャー
- GitHub Personal Access Token
  - プライベートリポジトリ：`repo`権限
  - パブリックリポジトリ：`public_repo`権限
- LLM APIエンドポイント（OpenAI互換形式）

## 🔑 GitHub Personal Access Token の発行

<details>
<summary><b>🔑 GitHub Personal Access Token の発行方法</b></summary>

このツールを使用するには、GitHub Personal Access Token（PAT）が必要です。

### 発行手順

1. **GitHub設定にアクセス**
   - [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens) にアクセス
   - または：GitHubプロフィール → Settings → Developer settings → Personal access tokens

2. **新しいトークンを生成**
   - "Generate new token" → "Generate new token (classic)" をクリック
   - Note：トークンの用途を入力（例：「GitHub Feedback Analysis」）
   - Expiration：有効期限を設定（推奨：90日またはカスタム）

3. **権限を選択**
   - **パブリックリポジトリのみ**：`public_repo` をチェック
   - **プライベートリポジトリを含む**：`repo` 全体をチェック
   - その他の権限は不要です

4. **トークンを生成してコピー**
   - "Generate token" をクリック
   - 生成されたトークン（ghp_ で始まる）をコピーして安全に保管
   - ⚠️ **重要**：このページを離れると、トークンを再度確認できません

5. **トークンを使用**
   - `gfa init` 実行時にコピーしたトークンを入力してください

### Fine-grained Personal Access Token の使用（オプション）

新しい細粒度トークンを使用する場合：
1. [Personal access tokens → Fine-grained tokens](https://github.com/settings/personal-access-tokens/new) にアクセス
2. Repository access：分析するリポジトリを選択
3. 権限を設定：
   - **Contents**：Read-only（必須）
   - **Metadata**：Read-only（自動選択）
   - **Pull requests**：Read-only（必須）
   - **Issues**：Read-only（必須）

### GitHub Enterprise ユーザー向けガイド

組織でGitHub Enterpriseを使用している場合：
1. **Enterpriseサーバーのトークンページにアクセス**
   - `https://github.your-company.com/settings/tokens`（会社のドメインに置き換え）
   - または：プロフィール → Settings → Developer settings → Personal access tokens

2. **権限設定は同じ**
   - プライベートリポジトリ：`repo`権限
   - パブリックリポジトリ：`public_repo`権限

3. **初期設定時にEnterpriseホストを指定**

   **対話モード（推奨）：**
   ```bash
   gfa init
   ```
   初期化時にEnterpriseホスト選択メニューが表示されます：
   - デフォルトの github.com を選択
   - サンプルEnterpriseホストリストから選択
   - 保存されたカスタムホストから選択
   - カスタムURLを直接入力（将来使用するために保存するかどうか確認されます）

   **CLIオプションを使用：**
   ```bash
   gfa init --enterprise-host https://github.your-company.com
   ```

4. **保存されたEnterpriseホストの管理**
   ```bash
   # 保存されたホストのリスト表示
   gfa config hosts list

   # 新しいホストを追加
   gfa config hosts add https://github.your-company.com

   # ホストを削除
   gfa config hosts remove https://github.your-company.com
   ```

5. **管理者に問い合わせ**
   - 一部のEnterprise環境ではPAT生成が制限されている場合があります
   - 問題が発生した場合は、GitHub管理者にお問い合わせください

### 参考資料

- [GitHub公式ドキュメント：Personal Access Token の管理](https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [GitHub公式ドキュメント：Fine-grained PAT](https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens)
- [GitHub Enterprise Server ドキュメント](https://docs.github.com/en/enterprise-server@latest/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

</details>

## 🔧 インストール

```bash
# リポジトリをコピー
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis

# 仮想環境の作成と有効化
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# パッケージのインストール
uv pip install -e .
```

## 🚀 クイックスタート

### 1️⃣ 設定の初期化

```bash
gfa init
```

プロンプトが表示されたら、以下の情報を入力してください：
- GitHub Personal Access Token（システムキーリングに安全に保存されます）
- LLMエンドポイント（例：`http://localhost:8000/v1/chat/completions`）
- LLMモデル（例：`gpt-4`）
- GitHub Enterpriseホスト（オプション）
  - 番号で選択するか、カスタムURLを直接入力
  - 新しいホストは将来使用するために保存するか確認されます

### 2️⃣ リポジトリを分析

```bash
gfa feedback
```

推奨リポジトリのリストから選択するか、直接入力して**あなたの活動**を分析することができます。

分析完了後、`reports/`ディレクトリに以下のファイルが生成されます：
- `metrics.json` - 分析データ
- `report.md` - Markdownレポート
- `report.html` - HTMLレポート（可視化チャート付き）
- `charts/` - SVGチャートファイル
- `prompts/` - LLMプロンプトファイル

### 3️⃣ 結果を確認

```bash
cat reports/report.md
```

## 📚 コマンドリファレンス

<details>
<summary><b>🎯 `gfa init` - 初期設定</b></summary>

GitHubアクセス情報とLLM設定を保存します。

#### 基本的な使い方（インタラクティブ）

```bash
gfa init
```

#### 例：GitHub.com + ローカルLLM

```bash
gfa init \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4 \
  --months 12
```

#### 例：GitHub Enterprise

```bash
gfa init \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --enterprise-host https://github.company.com \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4
```

#### オプション説明

| オプション | 説明 | 必須 | デフォルト |
|-----------|------|------|-----------|
| `--pat` | GitHub Personal Access Token | ✅ | - |
| `--llm-endpoint` | LLM APIエンドポイント | ✅ | - |
| `--llm-model` | LLMモデル識別子 | ✅ | - |
| `--months` | デフォルト分析期間（月） | ❌ | 12 |
| `--enterprise-host` | GitHub Enterpriseホスト | ❌ | github.com |

</details>

<details>
<summary><b>📊 gfa feedback - 個人活動分析</b></summary>

特定のリポジトリで**あなたの活動**を分析し、詳細なフィードバックレポートを生成します。

> **重要**：このコマンドは認証されたユーザー（PAT所有者）の個人活動のみを分析します。リポジトリ全体ではなく、**あなたの**コミット、PR、レビュー、イシューのみを収集して分析します。

#### 基本的な使い方

```bash
gfa feedback --repo owner/repo-name
```

#### インタラクティブモード

リポジトリを直接指定せず、推奨リストから選択できます。

```bash
gfa feedback --interactive
```

または

```bash
gfa feedback  # --repoオプションなしで実行
```

#### 例

```bash
# あなたが貢献した公開リポジトリを分析
gfa feedback --repo torvalds/linux

# あなたが貢献した個人リポジトリを分析
gfa feedback --repo myusername/my-private-repo

# あなたが貢献した組織リポジトリを分析
gfa feedback --repo microsoft/vscode

# インタラクティブモードでリポジトリ選択
gfa feedback --interactive
```

#### オプション説明

| オプション | 説明 | 必須 | デフォルト |
|-----------|------|------|-----------|
| `--repo`, `-r` | リポジトリ（owner/name） | ❌ | - |
| `--output`, `-o` | 出力ディレクトリ | ❌ | reports |
| `--interactive`, `-i` | インタラクティブなリポジトリ選択 | ❌ | false |

#### 生成されるレポート

分析完了後、`reports/`ディレクトリに以下のファイルが作成されます：

```
reports/
├── metrics.json              # 原本データ（JSON）
├── report.md                 # 分析レポート（Markdown）
├── report.html               # 分析レポート（HTML、チャート付き）
├── charts/                   # 可視化チャート
│   ├── quality.svg          # 品質指標チャート
│   ├── activity.svg         # アクティビティ指標チャート
│   └── ...                  # その他のドメイン固有チャート
└── prompts/
    ├── commit_feedback.txt   # コミットメッセージフィードバック
    ├── pr_feedback.txt       # PRタイトルフィードバック
    ├── review_feedback.txt   # レビュートーンフィードバック
    └── issue_feedback.txt    # イシュー品質フィードバック
```

#### 分析内容

- ✅ **アクティビティ集計**：あなたのコミット、PR、レビュー、イシュー数をカウント
- 🎯 **品質分析**：あなたのコミットメッセージ、PRタイトル、レビュートーン、イシュー説明の品質
- 🏆 **アワード**：あなたの貢献度に基づく自動アワード
- 📈 **トレンド**：あなたの月次アクティビティトレンドと速度分析
- 🤝 **協業分析**：あなたと一緒に作業した協業者ネットワーク
- 💻 **技術スタック**：あなたが作業したファイルの言語と技術分析

</details>

<details>
<summary><b>⚙️ `gfa config` - 設定管理</b></summary>

設定を確認または変更します。

#### `gfa config show` - 設定を表示

現在保存されている設定を表示します。

```bash
gfa config show
```

**出力例：**

```
┌─────────────────────────────────────┐
│ GitHub Feedback Configuration       │
├─────────────┬───────────────────────┤
│ Section     │ Values                │
├─────────────┼───────────────────────┤
│ auth        │ pat = <set>           │
├─────────────┼───────────────────────┤
│ server      │ api_url = https://... │
│             │ web_url = https://... │
├─────────────┼───────────────────────┤
│ llm         │ endpoint = http://... │
│             │ model = gpt-4         │
└─────────────┴───────────────────────┘
```

> **注：**`gfa show-config`コマンドは非推奨となり、`gfa config show`に置き換えられました。

#### `gfa config set` - 設定値を変更

個別の設定値を変更します。

```bash
gfa config set <key> <value>
```

**例：**

```bash
# LLMモデルを変更
gfa config set llm.model gpt-4

# LLMエンドポイントを変更
gfa config set llm.endpoint http://localhost:8000/v1/chat/completions

# デフォルト分析期間を変更
gfa config set defaults.months 6
```

#### `gfa config get` - 設定値を取得

特定の設定値を取得します。

```bash
gfa config get <key>
```

**例：**

```bash
# LLMモデルを確認
gfa config get llm.model

# デフォルト分析期間を確認
gfa config get defaults.months
```

</details>

<details>
<summary><b>🔍 `gfa list-repos` - リポジトリ一覧</b></summary>

アクセス可能なリポジトリをリストします。

```bash
gfa list-repos
```

#### 例

```bash
# リポジトリをリスト（デフォルト：最近更新された20件）
gfa list-repos

# ソート基準を変更
gfa list-repos --sort stars --limit 10

# 特定の組織でフィルタ
gfa list-repos --org myorganization

# 作成日順にソート
gfa list-repos --sort created --limit 50
```

#### オプション説明

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--sort`, `-s` | ソート基準（updated、created、pushed、full_name） | updated |
| `--limit`, `-l` | 最大表示数 | 20 |
| `--org`, `-o` | 組織名でフィルタ | - |

</details>

<details>
<summary><b>💡 `gfa suggest-repos` - リポジトリ推奨</b></summary>

分析に適したアクティブなリポジトリを推奨します。

```bash
gfa suggest-repos
```

最近のアクティビティがあるリポジトリを自動選択します。スター、フォーク、イシュー、最近の更新を総合的に考慮します。

#### 例

```bash
# デフォルト推奨（過去90日以内、10リポジトリ）
gfa suggest-repos

# 過去30日以内にアクティブな5リポジトリを推奨
gfa suggest-repos --limit 5 --days 30

# スター順でソート
gfa suggest-repos --sort stars

# アクティビティスコア順でソート（総合評価）
gfa suggest-repos --sort activity
```

#### オプション説明

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--limit`, `-l` | 最大推奨数 | 10 |
| `--days`, `-d` | 最近のアクティビティ期間（日） | 90 |
| `--sort`, `-s` | ソート基準（updated、stars、activity） | activity |

</details>

## 📁 設定ファイル

<details>
<summary><b>📁 設定ファイル</b></summary>

設定は`~/.config/github_feedback/config.toml`に保存され、`gfa init`実行時に自動作成されます。

### 設定ファイル例

```toml
[version]
version = "1.0.0"

[auth]
# PAT はシステムキーリングに安全に保存されます（このファイルには保存されません）

[server]
api_url = "https://api.github.com"
graphql_url = "https://api.github.com/graphql"
web_url = "https://github.com"

[llm]
endpoint = "http://localhost:8000/v1/chat/completions"
model = "gpt-4"
timeout = 60
max_files_in_prompt = 10
max_retries = 3

[defaults]
months = 12
```

### 手動設定編集

必要に応じて、設定ファイルを直接編集するか、`gfa config`コマンドを使用できます：

```bash
# 方法1：configコマンドを使用（推奨）
gfa config set llm.model gpt-4
gfa config show

# 方法2：直接編集
nano ~/.config/github_feedback/config.toml
```

</details>

## 📊 生成されるファイル構造

<details>
<summary><b>📊 生成されるファイル構造</b></summary>

### `gfa feedback`の出力

```
reports/
├── metrics.json              # 📈 個人活動分析データ（JSON）
├── report.md                 # 📄 Markdownレポート
├── report.html               # 🎨 HTMLレポート（可視化チャート付き）
├── charts/                   # 📊 可視化チャート（SVG）
│   ├── quality.svg          # 品質指標チャート
│   ├── activity.svg         # アクティビティ指標チャート
│   ├── engagement.svg       # エンゲージメントチャート
│   └── ...                  # その他のドメイン固有チャート
└── prompts/
    ├── commit_feedback.txt   # 💬 コミットメッセージ品質分析
    ├── pr_feedback.txt       # 🔀 PRタイトル分析
    ├── review_feedback.txt   # 👀 レビュートーン分析
    └── issue_feedback.txt    # 🐛 イシュー品質分析
```

</details>

## 💡 使用例

<details>
<summary><b>💡 使用例</b></summary>

### 例1：クイックスタート - インタラクティブモード

```bash
# 1. 設定（初回のみ）
gfa init

# 2. リポジトリ推奨を取得
gfa suggest-repos

# 3. インタラクティブモードであなたの活動を分析
gfa feedback --interactive

# 4. レポートを表示
cat reports/report.md
```

### 例2：オープンソース貢献活動の分析

```bash
# 1. 設定（初回のみ）
gfa init

# 2. あなたが貢献したオープンソースプロジェクトの活動を分析
gfa feedback --repo facebook/react

# 3. レポートを表示（あなたの貢献活動のみ表示されます）
cat reports/report.md
```

### 例3：個人プロジェクトの振り返り

```bash
# 自分のリポジトリリストを確認
gfa list-repos --sort updated --limit 10

# 自分のプロジェクトであなたの活動を分析
gfa feedback --repo myname/my-awesome-project

# レポートを表示
cat reports/report.md
```

### 例4：チームプロジェクトでのあなたの成果レビュー

```bash
# 組織のリポジトリリストを確認
gfa list-repos --org mycompany --limit 20

# 分析期間を設定（過去6ヶ月）
gfa config set defaults.months 6

# 組織のリポジトリであなたの活動を分析
gfa feedback --repo mycompany/product-service

# レポートを表示（あなたの活動のみ表示されます）
cat reports/report.md
```

</details>

## 🎯 アワードシステム

<details>
<summary><b>🎯 アワードシステム</b></summary>

リポジトリアクティビティに基づいてアワードが自動授与されます：

### コミットベースのアワード
- 💎 **コードレジェンド**（1000+コミット）
- 🏆 **コードマスター**（500+コミット）
- 🥇 **コード鍛冶師**（200+コミット）
- 🥈 **コード職人**（100+コミット）
- 🥉 **コード見習い**（50+コミット）

### PRベースのアワード
- 💎 **リリースレジェンド**（200+ PR）
- 🏆 **デプロイメント提督**（100+ PR）
- 🥇 **リリースキャプテン**（50+ PR）
- 🥈 **リリースナビゲーター**（25+ PR）
- 🥉 **デプロイメントセーラー**（10+ PR）

### レビューベースのアワード
- 💎 **知識伝播者**（200+レビュー）
- 🏆 **メンタリングマスター**（100+レビュー）
- 🥇 **レビューエキスパート**（50+レビュー）
- 🥈 **成長メンター**（20+レビュー）
- 🥉 **コードサポーター**（10+レビュー）

### 特別アワード
- ⚡ **ライトニング開発者**（月50+コミット）
- 🤝 **コラボレーションマスター**（月20+ PR+レビュー）
- 🏗️ **大規模アーキテクト**（5000+行変更）
- 📅 **一貫性マスター**（6ヶ月以上の継続的アクティビティ）
- 🌟 **マルチタレント**（すべての領域でバランスの取れた貢献）

</details>

## 🐛 トラブルシューティング

<details>
<summary><b>🐛 トラブルシューティング</b></summary>

### PAT権限エラー

```
Error: GitHub API rejected the provided PAT
```

**解決方法**：PATに適切な権限があることを確認
- プライベートリポジトリ：`repo`権限が必要
- パブリックリポジトリ：`public_repo`権限が必要
- [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)で確認

### LLMエンドポイント接続失敗

```
Warning: Detailed feedback analysis failed: Connection refused
```

**解決方法**：
1. LLMサーバーが実行中であることを確認
2. エンドポイントURLが正しいことを確認（`gfa config show`）
3. 必要に応じて設定を再初期化：`gfa init`

### リポジトリが見つからない

```
Error: Repository not found
```

**解決方法**：
- リポジトリ名の形式を確認：`owner/repo`（例：`torvalds/linux`）
- プライベートリポジトリの場合、PAT権限を確認
- GitHub Enterpriseの場合、`--enterprise-host`設定を確認

### 分析期間内にデータなし

```
No activity detected during analysis period.
```

**解決方法**：
- 分析期間を増やしてみる：`gfa init --months 24`
- リポジトリがアクティブであることを確認

</details>

## 👩‍💻 開発者ガイド

<details>
<summary><b>👩‍💻 開発者ガイド</b></summary>

### 開発環境セットアップ

```bash
# リポジトリをコピー
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis

# 開発モードでインストール（テスト依存関係を含む）
uv pip install -e .[test]

# テストを実行
pytest

# 特定のテストを実行
pytest tests/test_analyzer.py -v

# カバレッジを確認
pytest --cov=github_feedback --cov-report=html
```

### 主要な依存関係

**コアランタイム依存関係：**
- **typer >= 0.9** - CLIフレームワーク
- **rich >= 13.0** - ターミナルUI、プログレスバー
- **pydantic >= 2.5** - データ検証とシリアライゼーション
- **requests >= 2.31** - HTTPクライアント
- **requests-cache >= 1.0** - SQLiteベースのレスポンスキャッシュ
- **keyring >= 24.0** - システム認証情報ストレージ
- **keyrings.alt >= 5.0** - フォールバック暗号化ファイルキーリング
- **tomli >= 2.0** - TOMLファイル解析（Python < 3.11）
- **tomli-w >= 1.0** - TOMLファイル書き込み

**開発/テスト依存関係：**
- **pytest >= 7.4** - テストフレームワーク

**システム要件：**
- Python 3.11+（async/型ヒントが必要）
- システムキーリングまたはアクセス可能なファイルシステム
- GitHub Personal Access Token（クラシックまたはファイングレイン）
- OpenAI API形式と互換性のあるLLMエンドポイント

### コード構造

```
github_feedback/
├── cli.py              # 🖥️  CLIエントリーポイントとコマンド（1,791行）
├── llm.py             # 🤖 LLM APIクライアント（1,409行、リトライロジック付き）
├── reporter.py         # 📄 レポート生成（1,358行、brief形式）
├── retrospective.py    # 📅 年末回顧分析（1,021行）
├── analyzer.py         # 📊 メトリクス分析と計算（959行）
├── review_reporter.py  # 📝 統合レビューレポート（749行）
├── config.py          # ⚙️  設定管理（529行、キーリング統合）
├── models.py          # 📦 Pydanticデータモデル（525行）
├── pr_collector.py     # 🔍 PRデータ収集（439行）
├── award_strategies.py # 🏆 アワード計算戦略（419行、100+アワード）
├── api_client.py      # 🌐 GitHub REST APIクライアント（416行）
├── reviewer.py         # 🎯 PRレビューロジック（416行）
├── collector.py        # 📡 データ収集ファサード（397行）
├── commit_collector.py # 📝 コミットデータ収集（263行）
├── review_collector.py # 👀 レビューデータ収集（256行）
├── repository_manager.py # 📂 リポジトリ管理（250行）
├── filters.py         # 🔍 言語検出とフィルタリング（234行）
├── exceptions.py      # ⚠️  例外階層構造（235行、24+例外タイプ）
└── utils.py           # 🔧 ユーティリティ関数
```

### アーキテクチャとデザインパターン

- **ファサードパターン**：`Collector`クラスが専門的なコレクターを調整
- **ストラテジーパターン**：アワード計算で100+戦略を使用
- **リポジトリパターン**：`GitHubApiClient`がAPIアクセスを抽象化
- **ビルダーパターン**：レポートとメトリクスの構築
- **スレッドプールパターン**：並列データ収集（4倍の速度向上）

### パフォーマンス最適化

- **リクエストキャッシング**：SQLiteベースのキャッシュ（`~/.cache/github_feedback/api_cache.sqlite`）
  - デフォルトの有効期限：1時間
  - GET/HEADリクエストのみキャッシュ
  - 繰り返し実行時に60-70%の速度向上
- **並列収集**：ThreadPoolExecutorを使用した並行データ収集
- **リトライロジック**：LLMリクエストに指数バックオフを適用（最大3回試行）

</details>

## 🔒 セキュリティ

- **PAT ストレージ**：GitHub トークンはシステムキーリングに安全に保存されます（プレーンテキストファイルには保存されません）
  - システムキーリングサポート：gnome-keyring、macOS Keychain、Windows Credential Manager
  - Linuxフォールバック：暗号化ファイルキーリング（`keyrings.alt`）
  - スレッドセーフなキーリング初期化（競合状態を防止）
- **設定バックアップ**：設定を上書きする前に自動的にバックアップを作成します
- **入力検証**：すべてのユーザー入力を検証します（PAT 形式、URL 形式、リポジトリ形式）
- **キャッシュセキュリティ**：SQLiteキャッシュファイルはユーザーのみの読み取り/書き込み権限
- **APIセキュリティ**：Bearerトークン認証、HTTPS専用通信

## 📄 ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。

## 🤝 貢献

バグレポート、機能提案、PRはいつでも歓迎します！

1. リポジトリをフォーク
2. 機能ブランチを作成（`git checkout -b feature/amazing-feature`）
3. 変更をコミット（`git commit -m 'Add amazing feature'`）
4. ブランチにプッシュ（`git push origin feature/amazing-feature`）
5. Pull Requestを開く

## 💬 フィードバック

問題や提案がある場合は、[Issues](https://github.com/goonbamm/github-feedback-analysis/issues)に登録してください！
