import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE = Path(__file__).parent
DB_PATH = BASE / "data" / "news.db"

# code -> English name (used in prompts). The FIRST one is the "master" language the article is written in.
LANGUAGES = {"en": "English", "tr": "Turkish", "ar": "Arabic", "es": "Spanish"}
NATIVE_NAMES = {"en": "English", "tr": "Türkçe", "ar": "العربية", "es": "Español"}
RTL = {"ar"}

CATEGORIES = ["World", "Politics", "Business", "Technology", "Science", "Sports", "Health", "Culture", "General"]
CATEGORY_I18N = {
    "World": {"tr": "Dünya", "ar": "العالم", "es": "Mundo"},
    "Politics": {"tr": "Siyaset", "ar": "سياسة", "es": "Política"},
    "Business": {"tr": "Ekonomi", "ar": "أعمال", "es": "Economía"},
    "Technology": {"tr": "Teknoloji", "ar": "تكنولوجيا", "es": "Tecnología"},
    "Science": {"tr": "Bilim", "ar": "علوم", "es": "Ciencia"},
    "Sports": {"tr": "Spor", "ar": "رياضة", "es": "Deportes"},
    "Health": {"tr": "Sağlık", "ar": "صحة", "es": "Salud"},
    "Culture": {"tr": "Kültür", "ar": "ثقافة", "es": "Cultura"},
    "General": {"tr": "Genel", "ar": "عام", "es": "General"},
}
UI = {
    "en": {"latest": "Latest news", "read": "Read more", "back": "← Back", "sources": "Sources", "all": "All",
           "empty": "No articles published yet.", "note": "Written with AI assistance and reviewed by our editors."},
    "tr": {"latest": "Son haberler", "read": "Devamını oku", "back": "← Geri", "sources": "Kaynaklar", "all": "Tümü",
           "empty": "Henüz yayımlanmış haber yok.", "note": "Yapay zekâ desteğiyle hazırlanmış, editörlerimiz tarafından onaylanmıştır."},
    "ar": {"latest": "آخر الأخبار", "read": "اقرأ المزيد", "back": "→ رجوع", "sources": "المصادر", "all": "الكل",
           "empty": "لا توجد مقالات منشورة بعد.", "note": "كُتب بمساعدة الذكاء الاصطناعي وراجعه محررونا."},
    "es": {"latest": "Últimas noticias", "read": "Leer más", "back": "← Volver", "sources": "Fuentes", "all": "Todas",
           "empty": "Aún no hay artículos publicados.", "note": "Redactado con ayuda de IA y revisado por nuestros editores."},
}

# (name, rss url, category) -- editable later from the Sources page
DEFAULT_FEEDS = [
    ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml", "World"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", "World"),
    ("The Guardian World", "https://www.theguardian.com/world/rss", "World"),
    ("DW", "https://rss.dw.com/rdf/rss-en-all", "World"),
    ("NPR News", "https://feeds.npr.org/1001/rss.xml", "General"),
    ("BBC Business", "http://feeds.bbci.co.uk/news/business/rss.xml", "Business"),
    ("BBC Technology", "http://feeds.bbci.co.uk/news/technology/rss.xml", "Technology"),
    ("BBC Science", "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "Science"),
]

DEFAULT_SETTINGS = {
    "provider": "anthropic",                 # anthropic | ollama | openai_compatible
    "anthropic_model": "claude-sonnet-5-5",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "qwen2.5:7b",
    "openai_base_url": "https://api.openai.com/v1",
    "openai_model": "gpt-4o-mini",
    "max_items_per_feed": "15",
    "fetch_fulltext": "1",
    "max_articles_per_run": "5",
    "similarity": "0.3",
    "lookback_hours": "24",
    "min_sources": "1",
    "run_every_minutes": "60",
    "topic": "",
}
