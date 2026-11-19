# Google GitHub リポジトリ調査

Google が管理する GitHub の公開リポジトリ一覧を、GitHub APIを使わずWebページからスクレイピングしてSQLiteに保存する課題です。対象は `https://github.com/google?tab=repositories` です。

## 取得項目

- リポジトリ名
- 主要な言語
- スター数
- 取得日時（再取得時の更新管理用）

## 実行方法

Python 3.9以上を用意し、プロジェクト内で次を実行します。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --max-pages 1
```

`--max-pages 1` は最初のページだけを取得します。すべてのページを取得する場合は `python main.py` を実行してください。ページ間には `time.sleep(1)` を入れ、アクセス間隔を空けています。結果は `google_repositories.db` に保存されます。同じリポジトリを再取得した場合は最新値で更新します。

## SELECTで確認

SQLite CLIを使う場合:

```bash
sqlite3 google_repositories.db "SELECT repository_name, primary_language, star_count FROM repositories ORDER BY star_count DESC;"
```

またはPythonから:

```python
import sqlite3

with sqlite3.connect("google_repositories.db") as db:
    for row in db.execute(
        "SELECT repository_name, primary_language, star_count FROM repositories ORDER BY star_count DESC"
    ):
        print(row)
```

## 注意

GitHubの画面構造が変更されると、HTMLからの抽出部分の修正が必要になる場合があります。公開ページへのアクセスにのみ使用し、GitHub APIは使用していません。
