"""Reader-facing site:  streamlit run public_site.py --server.port 8502"""
import html
import streamlit as st

import db
from config import LANGUAGES, NATIVE_NAMES, RTL, UI, CATEGORY_I18N

st.set_page_config(page_title="The Daily", page_icon="🗞️", layout="centered")
db.init()
st.markdown("<style>#MainMenu,footer,header{visibility:hidden}</style>", unsafe_allow_html=True)

qp = st.query_params
lang = st.sidebar.selectbox("🌐", list(LANGUAGES), format_func=NATIVE_NAMES.get,
                            index=list(LANGUAGES).index(qp.get("lang", "en")) if qp.get("lang", "en") in LANGUAGES else 0)
qp["lang"] = lang
ui, rtl = UI[lang], lang in RTL
direction = "rtl" if rtl else "ltr"
align = "right" if rtl else "left"


def cat_name(c):
    return c if lang == "en" else CATEGORY_I18N.get(c, {}).get(lang, c)


def wrap(inner):
    st.markdown(f'<div dir="{direction}" style="text-align:{align}">{inner}</div>', unsafe_allow_html=True)


def paragraphs(body):
    text = (body or "").replace("\r\n", "\n").strip()
    if not text:
        return []
    chunks = text.split("\n\n") if "\n\n" in text else text.split("\n")
    return [part.strip() for part in chunks if part.strip()]


st.markdown(f"<h1 style='text-align:center'>🗞️ The Daily</h1>", unsafe_allow_html=True)

aid = qp.get("id")
if aid and aid.isdigit():
    art = db.get_article(int(aid), lang)
    if st.button(ui["back"]):
        del qp["id"]
        st.rerun()
    if art:
        paras = "".join(f"<p style='font-size:1.1rem;line-height:1.8'>{html.escape(p)}</p>"
                        for p in paragraphs(art["body"]))
        wrap(f"<small>{html.escape(cat_name(art['category']))} · {art['published_at'][:10]}</small>"
             f"<h2>{html.escape(art['title'])}</h2><p><i>{html.escape(art['summary'])}</i></p>{paras}")
        srcs = "".join(f"<li><a href='{html.escape(s['url'])}' target='_blank'>{html.escape(s['name'])}</a></li>"
                       for s in db.get_sources(int(aid)))
        wrap(f"<hr><b>{ui['sources']}</b><ul>{srcs}</ul><small>{ui['note']}</small>")
    else:
        st.warning("Article not available in this language.")
else:
    arts = [a for a in db.articles("published", lang) if a["title"]]
    cats = sorted({a["category"] for a in arts})
    chosen = st.sidebar.radio("📂", [ui["all"]] + cats, format_func=lambda c: c if c == ui["all"] else cat_name(c))
    wrap(f"<h3>{ui['latest']}</h3>")
    if not arts:
        st.info(ui["empty"])
    for a in arts:
        if chosen not in (ui["all"], a["category"]):
            continue
        with st.container(border=True):
            wrap(f"<small>{html.escape(cat_name(a['category']))} · {a['published_at'][:10]}</small>"
                 f"<h4>{html.escape(a['title'])}</h4><p>{html.escape(a['summary'] or '')}</p>")
            if st.button(ui["read"], key=f"r{a['id']}"):
                qp["id"] = str(a["id"])
                st.rerun()
