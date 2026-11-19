"""Scrape public Google GitHub repositories and store them in SQLite."""

from __future__ import annotations

import argparse
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ORG = "google"
BASE_URL = f"https://github.com/orgs/{ORG}/repositories?type=all"
DB_PATH = Path(__file__).with_name("google_repositories.db")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; classroom-repository-scraper/1.0)"}


def create_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS repositories (
            repository_name TEXT PRIMARY KEY,
            primary_language TEXT,
            star_count INTEGER NOT NULL,
            scraped_at TEXT NOT NULL
        )"""
    )
    connection.commit()


def parse_count(text: str) -> int:
    value = text.strip().replace(",", "").replace(" ", "")
    if value.lower().endswith("k"):
        return int(float(value[:-1]) * 1000)
    if value.lower().endswith("m"):
        return int(float(value[:-1]) * 1_000_000)
    return int(value)


def scrape_page(url: str) -> list[dict]:
    response = requests.get(url, headers=HEADERS, timeout=20)
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", "60"))
        print(f"アクセス頻度制限のため {retry_after} 秒待って再試行します。", flush=True)
        time.sleep(retry_after)
        response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    repos = []

    for star_link in soup.select(f'a[href^="/{ORG}/"][href$="/stargazers"]'):
        item = star_link.find_parent("li")
        if item is None:
            continue
        repo_link = next(
            (a for a in item.select(f'a[href^="/{ORG}/"]') if a.get("href", "").count("/") == 2
             and not a.get("href", "").endswith("/stargazers")),
            None,
        )
        if repo_link is None:
            continue
        name = repo_link["href"].strip("/").split("/")[1]
        language_tag = item.select_one('[itemprop="programmingLanguage"], [class*="PrimaryLanguageName"]')
        language = language_tag.get_text(" ", strip=True) if language_tag else None
        try:
            stars = parse_count(star_link.get_text(" ", strip=True))
        except ValueError:
            continue
        repos.append({"repository_name": name, "primary_language": language, "star_count": stars})

    return repos


def scrape_and_save(connection: sqlite3.Connection, max_pages: int | None = None, start_page: int = 1) -> int:
    saved = 0
    page = start_page
    pages_done = 0
    while max_pages is None or pages_done < max_pages:
        url = f"{BASE_URL}&page={page}"
        records = scrape_page(url)
        if not records:
            break
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        connection.executemany(
            """INSERT INTO repositories(repository_name, primary_language, star_count, scraped_at)
               VALUES (:repository_name, :primary_language, :star_count, :scraped_at)
               ON CONFLICT(repository_name) DO UPDATE SET
                 primary_language=excluded.primary_language,
                 star_count=excluded.star_count,
                 scraped_at=excluded.scraped_at""",
            [dict(record, scraped_at=now) for record in records],
        )
        connection.commit()
        saved += len(records)
        pages_done += 1
        print(f"ページ {page}: {len(records)}件を保存しました。", flush=True)
        page += 1
        if max_pages is None or pages_done < max_pages:
            time.sleep(1)
    return saved


def display_rows(connection: sqlite3.Connection) -> None:
    rows = connection.execute(
        "SELECT repository_name, primary_language, star_count FROM repositories ORDER BY star_count DESC"
    ).fetchall()
    print("repository_name | primary_language | star_count")
    for name, language, stars in rows:
        print(f"{name} | {language or '不明'} | {stars:,}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Googleの公開GitHubリポジトリをスクレイピングしてSQLiteに保存します")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="SQLiteデータベースのパス")
    parser.add_argument("--max-pages", type=int, default=None, help="取得ページ数の上限（省略時は全ページ）")
    parser.add_argument("--start-page", type=int, default=1, help="取得開始ページ（途中から再開する場合）")
    args = parser.parse_args()

    with sqlite3.connect(args.db) as connection:
        create_table(connection)
        count = scrape_and_save(connection, args.max_pages, args.start_page)
        print(f"{count}件を保存しました: {args.db}")
        display_rows(connection)


if __name__ == "__main__":
    main()
