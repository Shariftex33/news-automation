import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from config import DB_PATH, DEFAULT_FEEDS, DEFAULT_SETTINGS

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources(id INTEGER PRIMARY KEY, name TEXT, url TEXT UNIQUE, category TEXT DEFAULT 'General', active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS raw_items(id INTEGER PRIMARY KEY, source_id INTEGER, url TEXT UNIQUE, title TEXT, summary TEXT, text TEXT, published TEXT, fetched_at TEXT, processed INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS articles(id INTEGER PRIMARY KEY, category TEXT, status TEXT DEFAULT 'pending', created_at TEXT, published_at TEXT);
CREATE TABLE IF NOT EXISTS article_texts(article_id INTEGER, lang TEXT, title TEXT, summary TEXT, body TEXT, PRIMARY KEY(article_id, lang));
CREATE TABLE IF NOT EXISTS article_sources(article_id INTEGER, name TEXT, url TEXT, title TEXT);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
"""


def now(hours_ago=0):
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat(timespec="seconds")


@contextmanager
def conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    with conn() as c:
        c.executescript(SCHEMA)
        if not c.execute("SELECT 1 FROM sources LIMIT 1").fetchone():
            c.executemany("INSERT INTO sources(name,url,category) VALUES(?,?,?)", DEFAULT_FEEDS)


# ---- settings
def get_settings():
    s = dict(DEFAULT_SETTINGS)
    with conn() as c:
        s.update({r["key"]: r["value"] for r in c.execute("SELECT key,value FROM settings")})
    return s


def set_settings(d):
    with conn() as c:
        c.executemany("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                      [(k, str(v)) for k, v in d.items()])


# ---- sources
def sources():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM sources ORDER BY id")]


# ---- raw items
def unprocessed_items(hours):
    with conn() as c:
        return c.execute(
            "SELECT r.*, s.name AS source_name, s.category AS category FROM raw_items r "
            "JOIN sources s ON s.id=r.source_id WHERE r.processed=0 AND r.fetched_at>=? ORDER BY r.id DESC",
            (now(hours),)).fetchall()


def mark_processed(ids):
    with conn() as c:
        c.executemany("UPDATE raw_items SET processed=1 WHERE id=?", [(i,) for i in ids])


# ---- articles
def create_article(category, en, items):
    with conn() as c:
        aid = c.execute("INSERT INTO articles(category,status,created_at) VALUES(?,?,?)",
                        (category, "pending", now())).lastrowid
        c.execute("INSERT INTO article_texts VALUES(?,?,?,?,?)", (aid, "en", en["title"], en["summary"], en["body"]))
        c.executemany("INSERT INTO article_sources VALUES(?,?,?,?)",
                      [(aid, i["source_name"], i["url"], i["title"]) for i in items])
    return aid


def save_text(aid, lang, title, summary, body):
    with conn() as c:
        c.execute("INSERT INTO article_texts VALUES(?,?,?,?,?) ON CONFLICT(article_id,lang) DO UPDATE SET "
                  "title=excluded.title, summary=excluded.summary, body=excluded.body",
                  (aid, lang, title, summary, body))


def get_texts(aid):
    with conn() as c:
        return {r["lang"]: dict(r) for r in c.execute("SELECT * FROM article_texts WHERE article_id=?", (aid,))}


def get_sources(aid):
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM article_sources WHERE article_id=?", (aid,))]


def articles(status, lang="en"):
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT a.*, t.title, t.summary FROM articles a LEFT JOIN article_texts t "
            "ON t.article_id=a.id AND t.lang=? WHERE a.status=? ORDER BY COALESCE(a.published_at,a.created_at) DESC",
            (lang, status))]


def get_article(aid, lang):
    with conn() as c:
        r = c.execute("SELECT a.*, t.title, t.summary, t.body FROM articles a JOIN article_texts t "
                      "ON t.article_id=a.id AND t.lang=? WHERE a.id=? AND a.status='published'", (lang, aid)).fetchone()
        return dict(r) if r else None


def set_status(aid, status):
    with conn() as c:
        c.execute("UPDATE articles SET status=?, published_at=? WHERE id=?",
                  (status, now() if status == "published" else None, aid))


def recent_titles(hours):
    with conn() as c:
        return [r["title"] for r in c.execute(
            "SELECT t.title FROM articles a JOIN article_texts t ON t.article_id=a.id AND t.lang='en' "
            "WHERE a.created_at>=? AND a.status!='rejected'", (now(hours),))]


def counts():
    with conn() as c:
        out = {r["status"]: r["n"] for r in c.execute("SELECT status, COUNT(*) n FROM articles GROUP BY status")}
        out["raw_24h"] = c.execute("SELECT COUNT(*) FROM raw_items WHERE fetched_at>=?", (now(24),)).fetchone()[0]
        out["unprocessed"] = c.execute("SELECT COUNT(*) FROM raw_items WHERE processed=0").fetchone()[0]
    return out
