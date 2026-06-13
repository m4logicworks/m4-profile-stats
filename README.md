# GitHub Profile Stats Generator

GitHubのパブリック・プライベートリポジトリ双方から統計情報を収集し、美麗なSVGカードを生成・自動更新するツールです。

## 📊 生成イメージ

リポジトリ直下に `github-stats.svg` として出力されます。以下のようにREADMEに埋め込んで使用します。

```markdown
![GitHub Stats](https://raw.githubusercontent.com/m4logicworks/m4-profile-stats/main/github-stats.svg)
```

## ✨ 特徴

- **プライベートリポジトリ対応**: 非公開リポジトリのコントリビューション数や言語データも集計に反映。
- **モダンで美麗なデザイン**: ダークテーマ、グラデーション、マイクロインタラクション（ホバーでのアイコン変化やアニメーション）、進捗バー付き言語統計。
- **自動更新**: GitHub Actions で毎週月曜日の朝（日本時間 9:00）に定期実行され、差分がある場合のみ自動コミット・プッシュされます（無駄な履歴を作りません）。
- **uv による高速管理**: Pythonの次世代パッケージマネージャー `uv` を採用し、Actionsの実行時間を最小限に抑えています。

## 🚀 セットアップ手順

1. **GitHub Personal Access Token (PAT) の作成**
   プライベートリポジトリの情報を取得するために、以下のいずれかの権限を持つトークンを作成します。
   - **Fine-grained Personal Access Token (推奨)**:
     - Repository access: `All repositories`
     - Permissions: `Metadata` (Read-only), `Contents` (Read-only)
   - **Classic Personal Access Token**:
     - スコープ: `repo`

2. **Actions Secrets の設定**
   本リポジトリの **Settings** > **Secrets and variables** > **Actions** にて、新しい Repository Secret を作成します。
   - **Name**: `PERSONAL_ACCESS_TOKEN`
   - **Value**: 作成したトークン

3. **リポジトリの書き込み権限の確認**
   GitHub Actions からコミットをプッシュできるようにするため、**Settings** > **Actions** > **General** 内の **Workflow permissions** が `Read and write permissions` に設定されていることを確認してください（`update-stats.yml` 内でも `contents: write` を明示的に指定しています）。

4. **手動実行による動作確認**
   リポジトリの **Actions** タブから `Update GitHub Profile Stats` ワークフローを選択し、**Run workflow** から手動で実行して `github-stats.svg` が生成されることを確認してください。

## 🛠️ ローカルでの開発

本プロジェクトは `uv` を使用して依存関係を管理しています。

```bash
# 仮想環境の作成と依存関係のインストール
uv sync

# ローカルでの実行 (GitHub CLIの認証トークンを利用する場合)
PERSONAL_ACCESS_TOKEN=$(gh auth token) uv run generate_stats.py
```