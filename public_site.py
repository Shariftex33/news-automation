"""Reader-facing site:  streamlit run public_site.py --server.port 8502"""
import html
from urllib.parse import urlencode

import streamlit as st

import db
from config import CATEGORY_I18N, LANGUAGES, NATIVE_NAMES, RTL, UI

st.set_page_config(
    page_title="The Daily",
    page_icon="🗞️",
    layout="centered",
    initial_sidebar_state="collapsed",
)
db.init()

st.html(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,560;7..72,700&family=Noto+Naskh+Arabic:wght@500;700&family=Noto+Sans+Bengali:wght@420;600;700&family=Noto+Sans:wght@420;600;700&display=swap');
html, body, [class*="css"] {
  font-family: "Noto Sans", "Noto Sans Bengali", "Nirmala UI", "Noto Naskh Arabic", "Segoe UI", sans-serif;
  -webkit-text-size-adjust: 100%;
}
#MainMenu, [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stAppViewContainer"] footer { display: none !important; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
  background: #f3efe6 !important;
  color: #1c1917;
}
.block-container {
  max-width: 720px;
  padding: 0.35rem max(0.85rem, env(safe-area-inset-right)) calc(3.5rem + env(safe-area-inset-bottom)) max(0.85rem, env(safe-area-inset-left)) !important;
}
.stMarkdown { margin: 0; }
.stMarkdown p { margin: 0; }
.page { color: #1c1917; }
.mast { padding: 0.35rem 0 0.85rem; text-align: center; }
.brand {
  font-family: Literata, "Noto Sans Bengali", "Noto Naskh Arabic", Georgia, serif;
  font-size: 1.85rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin: 0;
}
.kicker { margin: 0.2rem 0 0; color: #78716c; font-size: 0.95rem; }
.pills, .chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.45rem;
  padding: 0.15rem 0 0.7rem;
}
.top {
  position: sticky;
  top: 0;
  z-index: 5;
  background: #f3efe6;
  margin: 0 0 0.35rem;
  padding-top: 0.15rem;
}
.pill, .chip, .back, .card {
  text-decoration: none;
  color: inherit;
}
.pill, .chip, .back { white-space: nowrap; }
.card, .card h2, .story, .story h1, .deck, .story p { white-space: normal; overflow-wrap: anywhere; }
.pill:focus-visible, .chip:focus-visible, .back:focus-visible, .card:focus-visible {
  outline: 3px solid #9f1239;
  outline-offset: 2px;
}
.pill, .chip {
  flex: 0 0 auto;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  padding: 0.45rem 0.9rem;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #e7e0d4;
  font-weight: 600;
  font-size: 0.95rem;
}
.pill.active, .chip.active {
  background: #1c1917;
  color: #faf7f2;
  border-color: #1c1917;
}
.list { display: flex; flex-direction: column; gap: 0.75rem; }
.card {
  display: block;
  background: #fff;
  border: 1px solid #e7e0d4;
  border-radius: 18px;
  padding: 1rem 1.05rem 0.95rem;
  box-shadow: 0 1px 0 rgba(28, 25, 23, 0.04);
}
.card:active, .pill:active, .chip:active, .back:active { transform: scale(0.99); }
.meta { color: #78716c; font-size: 0.82rem; font-weight: 600; letter-spacing: 0.01em; }
.card h2, .story h1 {
  font-family: Literata, "Noto Sans Bengali", "Noto Naskh Arabic", Georgia, serif;
  letter-spacing: -0.02em;
  margin: 0.35rem 0 0.4rem;
}
.card h2 { font-size: 1.22rem; line-height: 1.35; }
.card p {
  margin: 0;
  color: #44403c;
  line-height: 1.55;
  font-size: 0.98rem;
  white-space: normal;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.more {
  display: inline-block;
  margin-top: 0.75rem;
  color: #9f1239;
  font-weight: 700;
  font-size: 0.92rem;
}
.back {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  margin-bottom: 0.75rem;
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #e7e0d4;
  font-weight: 700;
}
.story h1 { font-size: clamp(1.55rem, 5vw, 2.15rem); line-height: 1.25; }
.deck { font-size: 1.08rem; line-height: 1.6; color: #44403c; margin: 0 0 1rem; }
.story p { font-size: 1.05rem; line-height: 1.8; margin: 0 0 1rem; }
.sources { margin-top: 0.5rem; padding-top: 0.85rem; border-top: 1px solid #e7e0d4; }
.sources h2 { font-size: 1rem; margin: 0 0 0.45rem; }
.sources ul { margin: 0; padding-inline-start: 1.15rem; }
.sources li { margin: 0.35rem 0; line-height: 1.45; }
.sources a {
  color: #9f1239;
  word-break: break-word;
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  white-space: normal;
}
.note { color: #78716c; font-size: 0.85rem; }
.empty {
  background: #fff;
  border: 1px dashed #d6d3d1;
  border-radius: 18px;
  padding: 1.25rem 1rem;
  color: #57534e;
}
@media (min-width: 720px) {
  .block-container { padding-top: 1.6rem !important; }
  .card h2 { font-size: 1.35rem; }
}
</style>
"""
)

qp = st.query_params
lang = qp.get("lang", "en")
if lang not in LANGUAGES:
    lang = "en"
ui = UI[lang]
direction = "rtl" if lang in RTL else "ltr"


def page_link(**changes):
    params = {}
    for key in ("lang", "cat", "id"):
        value = qp.get(key)
        if value:
            params[key] = value
    params["lang"] = lang
    for key, value in changes.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = str(value)
    return "?" + urlencode(params)


def cat_name(category):
    if lang == "en":
        return category
    return CATEGORY_I18N.get(category, {}).get(lang, category)


def paragraphs(body):
    text = (body or "").replace("\r\n", "\n").strip()
    if not text:
        return []
    chunks = text.split("\n\n") if "\n\n" in text else text.split("\n")
    return [part.strip() for part in chunks if part.strip()]


def when(value):
    return (value or "")[:10]


def language_bar():
    pills = []
    for code in LANGUAGES:
        active = " active" if code == lang else ""
        label = html.escape(NATIVE_NAMES[code])
        href = html.escape(page_link(lang=code))
        pills.append(f'<a class="pill{active}" href="{href}">{label}</a>')
    return f'<nav class="pills" aria-label="Language">{"".join(pills)}</nav>'


def masthead(kicker):
    return (
        f'<header class="mast"><p class="brand" dir="ltr">The Daily</p>'
        f'<p class="kicker">{html.escape(kicker)}</p></header>'
        f"{language_bar()}"
    )


aid = qp.get("id")
if aid and str(aid).isdigit():
    art = db.get_article(int(aid), lang)
    back = html.escape(page_link(id=None))
    back_link = f"<a class='back' href='{back}'>{html.escape(ui['back'])}</a>"
    if art:
        body = "".join(f"<p>{html.escape(part)}</p>" for part in paragraphs(art["body"]))
        sources = "".join(
            f"<li><a href='{html.escape(src['url'])}' target='_blank' rel='noopener'>"
            f"{html.escape(src['name'])}</a></li>"
            for src in db.get_sources(int(aid))
        )
        story = (
            f"<article class='story'>"
            f"<div class='meta'>{html.escape(cat_name(art['category']))} · <span dir='ltr'>{html.escape(when(art['published_at']))}</span></div>"
            f"<h1>{html.escape(art['title'])}</h1>"
            f"<p class='deck'><i>{html.escape(art['summary'] or '')}</i></p>"
            f"{body}"
            f"<section class='sources'><h2>{html.escape(ui['sources'])}</h2><ul>{sources}</ul></section>"
            f"<p class='note'>{html.escape(ui['note'])}</p>"
            f"</article>"
        )
    else:
        story = f"<div class='empty'>{html.escape(ui['unavailable'])}</div>"
    st.html(
        f'<div class="page" lang="{html.escape(lang)}" dir="{direction}">'
        f'<div class="top">{masthead(ui["latest"])}{back_link}</div>{story}</div>'
    )
else:
    arts = [a for a in db.articles("published", lang) if a["title"]]
    cats = sorted({a["category"] for a in arts})
    chosen = qp.get("cat")
    if chosen not in cats:
        chosen = None
    chips = [
        f'<a class="chip{" active" if chosen is None else ""}" href="{html.escape(page_link(cat=None, id=None))}">{html.escape(ui["all"])}</a>'
    ]
    for category in cats:
        active = " active" if category == chosen else ""
        chips.append(
            f'<a class="chip{active}" href="{html.escape(page_link(cat=category, id=None))}">'
            f"{html.escape(cat_name(category))}</a>"
        )
    cards = []
    visible = [a for a in arts if chosen in (None, a["category"])]
    if not visible:
        cards.append(f'<div class="empty">{html.escape(ui["empty"])}</div>')
    for article in visible:
        href = html.escape(page_link(id=article["id"], cat=chosen))
        cards.append(
            f'<a class="card" href="{href}">'
            f'<div class="meta">{html.escape(cat_name(article["category"]))} · <span dir="ltr">{html.escape(when(article["published_at"]))}</span></div>'
            f'<h2>{html.escape(article["title"])}</h2>'
            f'<p>{html.escape(article["summary"] or "")}</p>'
            f'<span class="more">{html.escape(ui["read"])}</span>'
            f"</a>"
        )
    st.html(
        f'<div class="page" lang="{html.escape(lang)}" dir="{direction}">'
        f'<div class="top">{masthead(ui["latest"])}</div>'
        f'<nav class="chips" aria-label="Category">{"".join(chips)}</nav>'
        f'<div class="list">{"".join(cards)}</div>'
        f"</div>"
    )
