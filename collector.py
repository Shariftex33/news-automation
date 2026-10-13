import html
import re
import feedparser
import trafilatura
import db


def _clean(t):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t or ""))).strip()


def _fulltext(url):
    try:
        raw = trafilatura.fetch_url(url)
        return (trafilatura.extract(raw, include_comments=False, include_tables=False) or "") if raw else ""
    except Exception:
        return ""


def collect(log=print) -> int:
    s = db.get_settings()
    limit, full = int(s["max_items_per_feed"]), s["fetch_fulltext"] == "1"
    total = 0
    for src in [x for x in db.sources() if x["active"]]:
        feed = feedparser.parse(src["url"], agent="NewsAutomation/1.0")
        if not feed.entries:
            log(f"⚠️ {src['name']}: no entries (feed down or URL wrong)")
            continue
        added = 0
        for e in feed.entries[:limit]:
            url = e.get("link")
            if not url:
                continue
            with db.conn() as c:
                if c.execute("SELECT 1 FROM raw_items WHERE url=?", (url,)).fetchone():
                    continue
            summary = _clean(e.get("summary", ""))
            text = (_fulltext(url) if full else "") or summary
            with db.conn() as c:
                c.execute("INSERT OR IGNORE INTO raw_items(source_id,url,title,summary,text,published,fetched_at) "
                          "VALUES(?,?,?,?,?,?,?)",
                          (src["id"], url, _clean(e.get("title", "")), summary, text[:6000],
                           e.get("published", ""), db.now()))
            added += 1
        total += added
        log(f"✅ {src['name']}: {added} new items")
    return total
