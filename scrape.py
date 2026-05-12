"""기사 URL → 본문 텍스트 추출 (다중 매체 대응).

전략:
  1. trafilatura — BBC/Guardian/TechCrunch/Verge/Ars/Al Jazeera 등 폭넓게 지원
  2. fallback: requests + BeautifulSoup으로 <article>/<main>/<p> 추출
"""
from __future__ import annotations
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import trafilatura

UA = "Mozilla/5.0 (compatible; WorldDailyKO/1.0; personal use)"
TIMEOUT = 15
MAX_WORKERS = 8

def _bs_fallback(html: str) -> str | None:
    """trafilatura가 빈 결과면 휴리스틱 fallback."""
    soup = BeautifulSoup(html, "lxml")
    # 1) <article> > 모든 <p>
    for art in soup.find_all("article"):
        paras = [p.get_text(strip=True) for p in art.find_all("p")]
        text = "\n\n".join(p for p in paras if len(p) > 30)
        if len(text) > 200:
            return text
    # 2) <main> > 모든 <p>
    main = soup.find("main")
    if main:
        paras = [p.get_text(strip=True) for p in main.find_all("p")]
        text = "\n\n".join(p for p in paras if len(p) > 30)
        if len(text) > 200:
            return text
    # 3) 마지막: body의 모든 <p> 중 30자 이상
    paras = [p.get_text(strip=True) for p in soup.find_all("p")]
    text = "\n\n".join(p for p in paras if len(p) > 50)
    if len(text) > 300:
        return text
    return None

def scrape_one(url: str) -> str:
    # 1차: trafilatura (HTML 자체 fetch 포함)
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                favor_precision=True,
                no_fallback=False,
            )
            if text and len(text) > 200:
                return text[:8000]
    except Exception as e:
        print(f"  · trafilatura 오류 ({url[:60]}): {e}", flush=True)

    # 2차: requests + BS4 휴리스틱
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
        r.raise_for_status()
        text = _bs_fallback(r.text)
        if text:
            return text[:8000]
    except Exception as e:
        return f"(본문 조회 실패: {e})"

    return "(본문 영역을 찾지 못함)"

def scrape_many(urls: list[str]) -> list[str]:
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        return list(ex.map(scrape_one, urls))

if __name__ == "__main__":
    import sys
    urls = sys.argv[1:] or [
        "https://www.bbc.com/news/articles/c626xjq0q0vo",
        "https://techcrunch.com/2026/05/11/riding-an-ai-rally-robinhood-preps-second-retail-venture-ipo/",
        "https://www.theverge.com/2026/05/10/openai-mythos",
    ]
    for u in urls:
        print(f"\n=== {u} ===")
        print(scrape_one(u)[:600])
