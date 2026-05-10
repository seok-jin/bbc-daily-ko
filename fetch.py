"""BBC RSS feeds → article metadata.

토픽 8개 + 지역 8개 = 16카테고리.
"""
from __future__ import annotations
import feedparser
from dataclasses import dataclass, asdict

# (name, group, label, url)
FEEDS_META: list[tuple[str, str, str, str]] = [
    # ── 토픽 ──
    ("Top Stories",   "topic",  "📰 톱스토리",     "https://feeds.bbci.co.uk/news/rss.xml"),
    ("World",         "topic",  "🌍 세계",         "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Business",      "topic",  "💼 비즈니스",     "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("Technology",    "topic",  "💻 테크",         "https://feeds.bbci.co.uk/news/technology/rss.xml"),
    ("Science",       "topic",  "🔬 과학·환경",    "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"),
    ("Health",        "topic",  "🏥 헬스",         "https://feeds.bbci.co.uk/news/health/rss.xml"),
    ("Politics",      "topic",  "🗳️ 정치",         "https://feeds.bbci.co.uk/news/politics/rss.xml"),
    ("Entertainment", "topic",  "🎭 엔터·문화",    "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml"),
    # ── 지역 ──
    ("US & Canada",   "region", "🇺🇸 미주",         "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml"),
    ("UK",            "region", "🇬🇧 영국",         "https://feeds.bbci.co.uk/news/uk/rss.xml"),
    ("Europe",        "region", "🇪🇺 유럽",         "https://feeds.bbci.co.uk/news/world/europe/rss.xml"),
    ("Asia",          "region", "🌏 아시아",        "https://feeds.bbci.co.uk/news/world/asia/rss.xml"),
    ("Australia",     "region", "🇦🇺 호주",         "https://feeds.bbci.co.uk/news/world/australia/rss.xml"),
    ("Africa",        "region", "🌍 아프리카",      "https://feeds.bbci.co.uk/news/world/africa/rss.xml"),
    ("Latin America", "region", "🌎 라틴아메리카",  "https://feeds.bbci.co.uk/news/world/latin_america/rss.xml"),
    ("Middle East",   "region", "🕌 중동",          "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml"),
]

CATEGORIES: dict[str, dict] = {
    name: {"group": g, "label": l, "url": u} for name, g, l, u in FEEDS_META
}

@dataclass
class Article:
    category: str
    title: str
    summary: str
    link: str
    published: str

def fetch_all(per_category: int = 6) -> list[Article]:
    out: list[Article] = []
    for name, _grp, _lbl, url in FEEDS_META:
        try:
            d = feedparser.parse(url)
        except Exception as e:
            print(f"  · RSS 실패 {name}: {e}", flush=True)
            continue
        for e in d.entries[:per_category]:
            out.append(Article(
                category=name,
                title=getattr(e, "title", "").strip(),
                summary=getattr(e, "summary", "").strip(),
                link=getattr(e, "link", ""),
                published=getattr(e, "published", ""),
            ))
    return out

if __name__ == "__main__":
    import json
    arts = fetch_all(per_category=2)
    print(f"fetched {len(arts)} articles from {len(FEEDS_META)} feeds")
    by_cat: dict[str, int] = {}
    for a in arts:
        by_cat[a.category] = by_cat.get(a.category, 0) + 1
    for cat, n in by_cat.items():
        print(f"  {cat:18s} {n}")
