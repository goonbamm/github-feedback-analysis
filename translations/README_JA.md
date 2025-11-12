# 🚀 GitHub フィードバック分析

GitHubリポジトリのアクティビティを分析し、インサイトに富んだレポートを自動生成するCLIツールです。GitHub.comとGitHub Enterpriseの両方をサポートし、LLMベースの自動レビュー機能を提供します。

日本語 | [한국어](../README.md) | [English](README_EN.md) | [简体中文](README_ZH.md) | [Español](README_ES.md)

## ✨ 主な機能

- 📊 **リポジトリ分析**：コミット、イシュー、レビューアクティビティを期間別に集計・分析
- 🤖 **LLMベースのフィードバック**：コミットメッセージ、PRタイトル、レビュートーン、イシュー品質の詳細分析
- 🎯 **自動PRレビュー**：認証ユーザーのPRを自動レビューし、統合振り返りレポートを生成
- 🏆 **アチーブメント可視化**：貢献度に応じてアワードとハイライトを自動生成
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
   - `gfainit` 実行時にコピーしたトークンを入力してください

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
   ```bash
   gfainit --enterprise-host https://github.your-company.com
   ```

4. **管理者に問い合わせ**
   - 一部のEnterprise環境ではPAT生成が制限されている場合があります
   - 問題が発生した場合は、GitHub管理者にお問い合わせください

### 参考資料

- [GitHub公式ドキュメント：Personal Access Token の管理](https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [GitHub公式ドキュメント：Fine-grained PAT](https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens)
- [GitHub Enterprise Server ドキュメント](https://docs.github.com/en/enterprise-server@latest/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

</details>

## 🔧 インストール

```bash
# リポジトリをクローン
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
gfainit
```

プロンプトが表示されたら、以下の情報を入力してください：
- GitHub Personal Access Token（システムキーリングに安全に保存されます）
- LLMエンドポイント（例：`http://localhost:8000/v1/chat/completions`）
- LLMモデル（例：`gpt-4`）
- GitHub Enterpriseホスト（オプション、github.comを使用しない場合のみ）

### 2️⃣ リポジトリを分析

```bash
gfa feedback --repo goonbamm/github-feedback-analysis
```

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
<summary><b>🎯 `gfainit` - 初期設定</b></summary>

GitHubアクセス情報とLLM設定を保存します。

#### 基本的な使い方（インタラクティブ）

```bash
gfainit
```

#### 例：GitHub.com + ローカルLLM

```bash
gfainit \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4 \
  --months 12
```

#### 例：GitHub Enterprise

```bash
gfainit \
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
<summary><b>📊 `gfa feedback` - リポジトリ分析</b></summary>

リポジトリを分析し、詳細なフィードバックレポートを生成します。

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
# パブリックリポジトリを分析
gfa feedback --repo torvalds/linux

# 個人リポジトリを分析
gfa feedback --repo myusername/my-private-repo

# 組織リポジトリを分析
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
├── metrics.json              # 📈 生の分析データ
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

#### 分析内容

- ✅ **アクティビティ集計**：コミット、PR、レビュー、イシュー数をカウント
- 🎯 **品質分析**：コミットメッセージ、PRタイトル、レビュートーン、イシュー説明の品質
- 🏆 **アワード**：貢献度に基づく自動アワード
- 📈 **トレンド**：月次アクティビティトレンドと速度分析

</details>

<details>
<summary><b>🎯 `gfafeedback` - 自動PRレビュー</b></summary>

認証ユーザー（PATオーナー）のPRを自動レビューし、統合振り返りレポートを生成します。

#### 基本的な使い方

```bash
gfafeedback --repo owner/repo-name
```

#### 例

```bash
# あなたが作成したすべてのPRをレビュー
gfafeedback --repo myusername/my-project
```

#### オプション説明

| オプション | 説明 | 必須 | デフォルト |
|-----------|------|------|-----------|
| `--repo` | リポジトリ（owner/name） | ✅ | - |

#### 実行プロセス

1. **PR検索** 🔍
   - PAT認証ユーザーが作成したPRリストを取得

2. **個別レビュー生成** 📝
   - 各PRのコード変更とレビューコメントを収集
   - LLMを使用して詳細レビューを生成
   - `reviews/owner_repo/pr-{番号}/`ディレクトリに保存

3. **統合振り返りレポート** 📊
   - すべてのPRを統合したインサイトを生成
   - `reviews/owner_repo/integrated_report.md`に保存

#### 生成されるファイル

```
reviews/
└── owner_repo/
    ├── pr-123/
    │   ├── artefacts.json          # PR生データ
    │   ├── review_summary.json     # LLM分析結果
    │   └── review.md               # Markdownレビュー
    ├── pr-456/
    │   └── ...
    └── integrated_report.md        # 統合振り返りレポート
```

</details>

<details>
<summary><b>⚙️ `gfaconfig` - 設定管理</b></summary>

設定を確認または変更します。

#### `gfaconfig show` - 設定を表示

現在保存されている設定を表示します。

```bash
gfaconfig show
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

> **注：**`gfashow-config`コマンドは非推奨となり、`gfaconfig show`に置き換えられました。

#### `gfaconfig set` - 設定値を変更

個別の設定値を変更します。

```bash
gfaconfig set <key> <value>
```

**例：**

```bash
# LLMモデルを変更
gfaconfig set llm.model gpt-4

# LLMエンドポイントを変更
gfaconfig set llm.endpoint http://localhost:8000/v1/chat/completions

# デフォルト分析期間を変更
gfaconfig set defaults.months 6
```

#### `gfaconfig get` - 設定値を取得

特定の設定値を取得します。

```bash
gfaconfig get <key>
```

**例：**

```bash
# LLMモデルを確認
gfaconfig get llm.model

# デフォルト分析期間を確認
gfaconfig get defaults.months
```

</details>

<details>
<summary><b>🔍 `gfalist-repos` - リポジトリ一覧</b></summary>

アクセス可能なリポジトリをリストします。

```bash
gfalist-repos
```

#### 例

```bash
# リポジトリをリスト（デフォルト：最近更新された20件）
gfalist-repos

# ソート基準を変更
gfalist-repos --sort stars --limit 10

# 特定の組織でフィルタ
gfalist-repos --org myorganization

# 作成日順にソート
gfalist-repos --sort created --limit 50
```

#### オプション説明

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--sort`, `-s` | ソート基準（updated、created、pushed、full_name） | updated |
| `--limit`, `-l` | 最大表示数 | 20 |
| `--org`, `-o` | 組織名でフィルタ | - |

</details>

<details>
<summary><b>💡 `gfasuggest-repos` - リポジトリ推奨</b></summary>

分析に適したアクティブなリポジトリを推奨します。

```bash
gfasuggest-repos
```

最近のアクティビティがあるリポジトリを自動選択します。スター、フォーク、イシュー、最近の更新を総合的に考慮します。

#### 例

```bash
# デフォルト推奨（過去90日以内、10リポジトリ）
gfasuggest-repos

# 過去30日以内にアクティブな5リポジトリを推奨
gfasuggest-repos --limit 5 --days 30

# スター順でソート
gfasuggest-repos --sort stars

# アクティビティスコア順でソート（総合評価）
gfasuggest-repos --sort activity
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

設定は`~/.config/github_feedback/config.toml`に保存され、`gfainit`実行時に自動作成されます。

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

必要に応じて、設定ファイルを直接編集するか、`gfaconfig`コマンドを使用できます：

```bash
# 方法1：configコマンドを使用（推奨）
gfaconfig set llm.model gpt-4
gfaconfig show

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
├── metrics.json              # 📈 生の分析データ
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

### `gfafeedback`の出力

```
reviews/
└── owner_repo/
    ├── pr-123/
    │   ├── artefacts.json          # 📦 PR生データ（コード、レビューなど）
    │   ├── review_summary.json     # 🤖 LLM分析結果（構造化データ）
    │   └── review.md               # 📝 Markdownレビューレポート
    ├── pr-456/
    │   └── ...
    └── integrated_report.md        # 🎯 統合振り返りレポート（すべてのPR統合）
```

</details>

## 💡 使用例

<details>
<summary><b>💡 使用例</b></summary>

### 例1：クイックスタート - インタラクティブモード

```bash
# 1. 設定（初回のみ）
gfainit

# 2. リポジトリ推奨を取得
gfasuggest-repos

# 3. インタラクティブモードで分析
gfa feedback --interactive

# 4. レポートを表示
cat reports/report.md
```

### 例2：オープンソースプロジェクト分析

```bash
# 1. 設定（初回のみ）
gfainit

# 2. 人気のオープンソースプロジェクトを分析
gfa feedback --repo facebook/react

# 3. レポートを表示
cat reports/report.md
```

### 例3：個人プロジェクト振り返り

```bash
# 自分のリポジトリリストを確認
gfalist-repos --sort updated --limit 10

# 自分のプロジェクトを分析
gfa feedback --repo myname/my-awesome-project

# 自分のPRを自動レビュー
gfafeedback --repo myname/my-awesome-project

# 統合振り返りレポートを表示
cat reviews/myname_my-awesome-project/integrated_report.md
```

### 例4：チームプロジェクトパフォーマンスレビュー

```bash
# 組織のリポジトリリストを確認
gfalist-repos --org mycompany --limit 20

# 分析期間を設定（過去6ヶ月）
gfaconfig set defaults.months 6

# 組織のリポジトリを分析
gfa feedback --repo mycompany/product-service

# チームメンバーのPRをレビュー（各自のPATで実行）
gfafeedback --repo mycompany/product-service
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
2. エンドポイントURLが正しいことを確認（`gfaconfig show`）
3. 必要に応じて設定を再初期化：`gfainit`

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
- 分析期間を増やしてみる：`gfainit --months 24`
- リポジトリがアクティブであることを確認

</details>

## 👩‍💻 開発者ガイド

<details>
<summary><b>👩‍💻 開発者ガイド</b></summary>

### 開発環境セットアップ

```bash
# リポジトリをクローン
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

### コード構造

```
github_feedback/
├── cli.py              # 🖥️  CLIエントリーポイントとコマンド
├── collector.py        # 📡 GitHub APIデータ収集
├── analyzer.py         # 📊 メトリクス分析と計算
├── reporter.py         # 📄 レポート生成（brief）
├── reviewer.py         # 🎯 PRレビューロジック
├── review_reporter.py  # 📝 統合レビューレポート
├── llm.py             # 🤖 LLM APIクライアント
├── config.py          # ⚙️  設定管理
├── models.py          # 📦 データモデル
└── utils.py           # 🔧 ユーティリティ関数
```

</details>

## 🔒 セキュリティ

- **PAT ストレージ**：GitHub トークンはシステムキーリングに安全に保存されます（プレーンテキストファイルには保存されません）
- **設定バックアップ**：設定を上書きする前に自動的にバックアップを作成します
- **入力検証**：すべてのユーザー入力を検証します（PAT 形式、URL 形式、リポジトリ形式）

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
