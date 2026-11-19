# Google GitHub リポジトリ調査

`https://github.com/orgs/google/repositories?type=all` 

## 取得項目

- リポジトリ名
- 主要な言語
- スター数
- 取得日時

## 実行方法

Python 3.9以上を用意し、プロジェクト内で次を実行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --max-pages 1
```

`--max-pages 1` は最初のページだけを取得。ページ間には `time.sleep(1)` を入れアクセス間隔を空ける。結果は `google_repositories.db` 。途中から再開する場合は `--start-page 41` のようにページ番号を指定。GitHub側がアクセス頻度を制限した場合、レスポンスの `Retry-After` 秒数を待ってから再試行

GitHubの一覧画面ではスター数が `54k` のように省略表示される。`k` を1000として換算して保存するため、省略表示の範囲内での値

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

