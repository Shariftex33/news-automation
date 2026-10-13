
"""Editor dashboard: streamlit run app.py"""

import html
import os
import pandas as pd
import streamlit as st

import db
import llm
import pipeline
from config import LANGUAGES, NATIVE_NAMES, RTL, CATEGORIES

st.set_page_config(
    page_title="Newsroom Admin",
    page_icon="📰",
    layout="wide",
)

db.init()

page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Review queue", "Published", "Sources", "Settings"],
)

st.sidebar.caption(
    "Reader site: `streamlit run public_site.py --server.port 8502`"
)

FIELDS = ("title", "summary", "body")


def key(f, aid, code):
    return f"{f}_{aid}_{code}"


def _paragraphs(body):
    text = (body or "").replace("\r\n", "\n").strip()
    if not text:
        return []
    chunks = text.split("\n\n") if "\n\n" in text else text.split("\n")
    return [part.strip() for part in chunks if part.strip()]


def clear_keys(aid):
    for code in LANGUAGES:
        for f in FIELDS:
            st.session_state.pop(key(f, aid, code), None)


def save_form(aid):
    for code in LANGUAGES:
        values = {
            f: st.session_state.get(key(f, aid, code), "")
            for f in FIELDS
        }
        db.save_text(
            aid,
            code,
            values["title"],
            values["summary"],
            values["body"],
        )


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------

if page == "Dashboard":
    st.title("📰 Newsroom Dashboard")

    counts = db.counts()

    a, b, c, d = st.columns(4)
    a.metric("Waiting for review", counts.get("pending", 0))
    b.metric("Published", counts.get("published", 0))
    c.metric("Items collected (24h)", counts["raw_24h"])
    d.metric("Unprocessed items", counts["unprocessed"])

    settings = db.get_settings()

    st.caption(
        f"AI provider: **{settings['provider']}** · "
        "English sources → article written in English → "
        "translated into Turkish, Arabic and Spanish"
    )

    topic = st.text_input(
        "Topic (optional)",
        value=settings.get("topic", ""),
        placeholder="e.g. migration, elections, climate",
        help="Filled in: only stories about this topic are written. Empty: all news, as usual.",
    )

    def remember_topic():
        current = db.get_settings()
        current["topic"] = topic.strip()
        db.set_settings(current)

    c1, c2 = st.columns(2)

    if c1.button(
        "▶️ Run full pipeline (collect + write + translate)",
        type="primary",
    ):
        remember_topic()
        with st.status("Running pipeline...", expanded=True) as status:
            pipeline.run_all(st.write, topic.strip())
            status.update(label="Finished", state="complete")

    if c2.button("📡 Collect only"):
        remember_topic()
        with st.status("Collecting...", expanded=True) as status:
            import collector

            collector.collect(st.write)
            status.update(label="Finished", state="complete")

    st.info(
        "Leave the topic empty to process every story. "
        "A saved topic is also used by `python worker.py`. "
        "Nothing goes public until you approve it in the Review queue."
    )


# ------------------------------------------------------------------
# Review queue
# ------------------------------------------------------------------

elif page == "Review queue":
    st.title("📝 Review queue")

    articles = db.articles("pending")

    if not articles:
        st.info("Nothing waiting. Run the pipeline from the Dashboard.")
        st.stop()

    titles = {
        article["id"]: article["title"] or "(no title)"
        for article in articles
    }

    aid = st.selectbox(
        "Article",
        list(titles),
        format_func=lambda i: f"#{i} · {titles[i]}",
    )

    meta = next(article for article in articles if article["id"] == aid)
    texts = db.get_texts(aid)

    st.caption(
        f"Category: **{meta['category']}** · created {meta['created_at']}"
    )

    with st.expander("Sources used"):
        for src in db.get_sources(aid):
            st.markdown(
                f"- **{src['name']}** — "
                f"[{src['title']}]({src['url']})"
            )

    tabs = st.tabs([
        NATIVE_NAMES[code]
        + ("" if code in texts else " ⚠️")
        for code in LANGUAGES
    ])

    for tab, code in zip(tabs, LANGUAGES):
        with tab:
            article_text = texts.get(
                code,
                {"title": "", "summary": "", "body": ""},
            )

            if code not in texts:
                st.warning(
                    "Translation missing. Use 'Re-translate from English'."
                )

            for field in FIELDS:
                widget_key = key(field, aid, code)
                stored = article_text.get(field) or ""
                if stored.strip() and not str(st.session_state.get(widget_key, "")).strip():
                    st.session_state[widget_key] = stored

            st.text_input(
                "Title",
                article_text["title"],
                key=key("title", aid, code),
            )

            st.text_area(
                "Summary",
                article_text["summary"],
                height=80,
                key=key("summary", aid, code),
            )

            st.text_area(
                "Body",
                article_text["body"],
                height=380,
                key=key("body", aid, code),
            )

    b1, b2, b3, b4 = st.columns(4)

    if b1.button("💾 Save edits"):
        save_form(aid)
        st.toast("Saved")

    if b2.button("🔄 Re-translate from English"):
        save_form(aid)

        english_text = db.get_texts(aid).get("en")

        if not english_text:
            st.error("English text is missing. Add the English article first.")
        else:
            with st.spinner("Translating..."):
                pipeline.translate_all(
                    aid,
                    english_text,
                    db.get_settings(),
                )

            clear_keys(aid)
            st.rerun()

    if b3.button("✅ Approve & publish", type="primary"):
        missing = [
            LANGUAGES[code]
            for code in LANGUAGES
            if not st.session_state.get(
                key("title", aid, code), ""
            ).strip()
            or not st.session_state.get(
                key("body", aid, code), ""
            ).strip()
        ]

        if missing:
            st.error(
                "Fill in title and body for: " + ", ".join(missing)
            )
        else:
            save_form(aid)
            db.set_status(aid, "published")
            clear_keys(aid)
            st.rerun()

    if b4.button("🗑️ Reject"):
        db.set_status(aid, "rejected")
        clear_keys(aid)
        st.rerun()


# ------------------------------------------------------------------
# Published
# ------------------------------------------------------------------

elif page == "Published":
    st.title("✅ Published")
    st.caption(
        "Each story is written in English, then translated into "
        "Turkish, Arabic and Spanish. Open an article to read the full text."
    )

    articles = db.articles("published")

    if not articles:
        st.info("Nothing published yet.")
        st.stop()

    titles = {
        article["id"]: article["title"] or "(no title)"
        for article in articles
    }

    aid = st.selectbox(
        "Article",
        list(titles),
        format_func=lambda i: f"#{i} · {titles[i]}",
    )

    meta = next(article for article in articles if article["id"] == aid)
    texts = db.get_texts(aid)

    head, action = st.columns([5, 1])
    head.caption(
        f"Category: **{meta['category']}** · published {meta['published_at']}"
    )

    if action.button("Unpublish", key=f"unpublish_{aid}"):
        db.set_status(aid, "pending")
        st.rerun()

    tabs = st.tabs([
        NATIVE_NAMES[code] + ("" if code in texts else " ⚠️")
        for code in LANGUAGES
    ])

    for tab, code in zip(tabs, LANGUAGES):
        with tab:
            article_text = texts.get(code)

            body = (article_text.get("body") or "").strip() if article_text else ""
            title = (article_text.get("title") or "").strip() if article_text else ""

            if not body:
                st.warning(
                    "This language is missing. "
                    "Send the article back to the review queue and re-translate from English."
                    if code != "en"
                    else "English text is missing."
                )
                continue

            if code != "en" and (len(body) < 80 or len(title) < 8):
                st.warning(
                    "This translation is only a fragment. "
                    "Unpublish the article, then use Re-translate from English in the review queue."
                )

            direction = "rtl" if code in RTL else "ltr"
            align = "right" if code in RTL else "left"
            summary = (article_text.get("summary") or "").strip()
            body_html = "".join(
                f"<p style='font-size:1.05rem;line-height:1.75;margin:0 0 1rem 0'>"
                f"{html.escape(part)}</p>"
                for part in _paragraphs(article_text.get("body") or "")
            )
            summary_html = (
                f"<p style='font-size:1.05rem'><i>{html.escape(summary)}</i></p>"
                if summary
                else ""
            )

            st.markdown(
                f'<div dir="{direction}" style="text-align:{align}">'
                f"<h2>{html.escape(article_text.get('title') or '')}</h2>"
                f"{summary_html}{body_html}</div>",
                unsafe_allow_html=True,
            )

    with st.expander("Sources used"):
        for src in db.get_sources(aid):
            st.markdown(
                f"- **{src['name']}** — [{src['title']}]({src['url']})"
            )


# ------------------------------------------------------------------
# Sources
# ------------------------------------------------------------------

elif page == "Sources":
    st.title("📡 News sources (RSS)")
    st.caption(
        "Use English-language feeds. The pipeline writes each story in English, "
        "then translates it into Turkish, Arabic and Spanish."
    )

    cols = ["id", "name", "url", "category", "active"]
    df = pd.DataFrame(db.sources(), columns=cols)

    df["active"] = df["active"].astype(bool)

    edited = st.data_editor(
        df,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn(disabled=True),
            "category": st.column_config.SelectboxColumn(
                options=CATEGORIES
            ),
            "active": st.column_config.CheckboxColumn(),
        },
    )

    if st.button("💾 Save sources", type="primary"):
        keep = set()

        with db.conn() as conn:
            for _, row in edited.iterrows():
                if pd.isna(row["url"]) or not str(row["url"]).strip():
                    continue

                name = "" if pd.isna(row["name"]) else str(row["name"])
                category = (
                    "General"
                    if pd.isna(row["category"])
                    else str(row["category"])
                )
                active = (
                    1
                    if pd.isna(row["active"]) or row["active"]
                    else 0
                )
                url = str(row["url"]).strip()

                if pd.notna(row["id"]):
                    source_id = int(row["id"])

                    conn.execute(
                        """
                        UPDATE sources
                        SET name=?, url=?, category=?, active=?
                        WHERE id=?
                        """,
                        (name, url, category, active, source_id),
                    )

                    keep.add(source_id)

                else:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO sources
                        (name, url, category, active)
                        VALUES (?, ?, ?, ?)
                        """,
                        (name, url, category, active),
                    )

            old_ids = set(df["id"].dropna().astype(int)) - keep

            for source_id in old_ids:
                conn.execute(
                    "DELETE FROM sources WHERE id=?",
                    (source_id,),
                )

        st.success("Saved")
        st.rerun()


# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------

elif page == "Settings":
    st.title("⚙️ Settings")

    s = db.get_settings()

    providers = {
        "anthropic": "Claude (Anthropic API)",
        "ollama": "Free local model (Ollama)",
        "openai_compatible": (
            "OpenAI-compatible API "
            "(OpenAI, Groq, OpenRouter, LM Studio...)"
        ),
    }

    current_provider = s.get("provider", "ollama")

    if current_provider not in providers:
        current_provider = "ollama"

    s["provider"] = st.radio(
        "AI provider",
        options=list(providers),
        format_func=providers.get,
        index=list(providers).index(current_provider),
    )

    if s["provider"] == "anthropic":
        s["anthropic_model"] = st.text_input(
            "Claude model",
            s.get("anthropic_model", ""),
        )

        st.caption(
            "API key found ✅"
            if os.getenv("ANTHROPIC_API_KEY")
            else "⚠️ Put ANTHROPIC_API_KEY in your .env file"
        )

    elif s["provider"] == "ollama":
        s["ollama_url"] = st.text_input(
            "Ollama URL",
            s.get("ollama_url", "http://localhost:11434"),
        )

        s["ollama_model"] = st.text_input(
            "Model",
            s.get("ollama_model", "qwen2.5:3b"),
            help=(
                "Run `ollama pull <model>` first. "
                "For Arabic/Turkish, consider a suitable Qwen model."
            ),
        )

    else:
        s["openai_base_url"] = st.text_input(
            "Base URL",
            s.get(
                "openai_base_url",
                "https://api.groq.com/openai/v1",
            ),
            help=(
                "Enter the base URL. The application should append "
                "/chat/completions when making the API request."
            ),
        )

        s["openai_model"] = st.text_input(
            "Model",
            s.get("openai_model", "llama-3.3-70b-versatile"),
        )

        st.caption(
            "API key found ✅"
            if os.getenv("OPENAI_API_KEY")
            else "⚠️ Put OPENAI_API_KEY in your .env file"
        )

    st.subheader("Pipeline")

    s["topic"] = st.text_input(
        "Topic (optional)",
        s.get("topic", ""),
        placeholder="Leave empty for all news",
        help="Filled in: worker.py and the pipeline write only this topic. Empty: all news.",
    )

    c1, c2, c3 = st.columns(3)

    s["max_items_per_feed"] = str(
        c1.number_input(
            "Items per feed",
            min_value=1,
            max_value=100,
            value=int(s["max_items_per_feed"]),
        )
    )

    s["max_articles_per_run"] = str(
        c2.number_input(
            "Max new articles per run",
            min_value=1,
            max_value=50,
            value=int(s["max_articles_per_run"]),
        )
    )

    s["min_sources"] = str(
        c3.number_input(
            "Min. sources per story",
            min_value=1,
            max_value=5,
            value=int(s["min_sources"]),
            help="2+ = only write stories reported by several outlets",
        )
    )

    s["lookback_hours"] = str(
        c1.number_input(
            "Look-back (hours)",
            min_value=1,
            max_value=168,
            value=int(s["lookback_hours"]),
        )
    )

    s["similarity"] = str(
        c2.slider(
            "Same-story similarity",
            min_value=0.1,
            max_value=0.9,
            value=float(s["similarity"]),
            step=0.05,
        )
    )

    s["run_every_minutes"] = str(
        c3.number_input(
            "worker.py interval (min)",
            min_value=5,
            max_value=1440,
            value=int(s["run_every_minutes"]),
        )
    )

    s["fetch_fulltext"] = (
        "1"
        if st.checkbox(
            "Download full article text (better quality, slower)",
            value=s["fetch_fulltext"] == "1",
        )
        else "0"
    )

    b1, b2 = st.columns(2)

    if b1.button("💾 Save settings", type="primary"):
        db.set_settings(s)
        st.success("Saved")

    if b2.button("🧪 Test AI connection"):
        try:
            db.set_settings(s)

            reply = llm.complete(
                "You are a test.",
                "Reply with the single word: OK",
                s,
                20,
            )

            st.success("Reply: " + reply)

        except Exception as e:
            st.error(f"Failed: {e}")
