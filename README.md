# News Automation (Streamlit)

Collects news from RSS sources → groups reports of the same story → writes an original article →
translates to **English, Turkish, Arabic, Spanish** → **an editor approves** → published on the reader site.

```
RSS feeds ─► collector ─► SQLite ─► cluster same story ─► LLM writes (EN) ─► LLM translates (TR/AR/ES)
                                                                   │
                         reader site  ◄── publish ◄── editor review (Streamlit admin)
```

## Setup

```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # add ANTHROPIC_API_KEY if using Claude
```

## Run

```bash
streamlit run app.py                          # editor dashboard  -> http://localhost:8501
streamlit run public_site.py --server.port 8502   # reader site       -> http://localhost:8502
python worker.py                              # optional: auto-run pipeline on a schedule
```

Typical flow: Dashboard → **Run full pipeline** → Review queue → edit/approve → check the reader site.

## Choosing the AI engine (Settings page, switch any time)

| Provider            | Setup                                                                                                   |
| ------------------- | ------------------------------------------------------------------------------------------------------- |
| Claude              | `ANTHROPIC_API_KEY` in `.env`                                                                       |
| Free local (Ollama) | Install Ollama,`ollama pull qwen2.5:7b` (use `qwen2.5:14b`/`gemma2:9b` for better Arabic/Turkish) |
| OpenAI-compatible   | `OPENAI_API_KEY` in `.env` + base URL/model (OpenAI, Groq, OpenRouter, LM Studio)                   |

Local models are free but translation quality (especially Arabic) is noticeably lower, and small models
sometimes return broken JSON. The pipeline retries once; failed translations are flagged ⚠️ in the review tab
and can be redone with **Re-translate from English**.

## Files

`config.py` languages, categories, default feeds · `db.py` SQLite · `collector.py` RSS + full text ·
`pipeline.py` cluster/write/translate · `llm.py` provider switch · `app.py` admin · `public_site.py` readers · `worker.py` scheduler

## Important before going public

- **Copyright/ToS:** RSS feeds are for headlines/summaries. Check each source's terms before pulling full text;
  the pipeline rewrites rather than copies and links every source, but you remain responsible.
- **AI errors:** models can mis-state facts, so keep the human approval step; the reader site labels articles as AI-assisted.
- **Production:** Streamlit is fine for the editor tool and a prototype reader site. For a real public site with SEO,
  serve the same SQLite/Postgres data through FastAPI/Next.js/WordPress. The admin and pipeline stay as they are.
- The admin has no login; don't expose it to the internet as is.
