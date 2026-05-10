"""BBC Daily KO — Streamlit 뷰어 (on-demand 본문 번역 포함)."""
from __future__ import annotations
import json
import re
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from translate import translate_article

REPORTS_DIR = Path(__file__).parent / "reports"

st.set_page_config(page_title="BBC Daily KO", page_icon="📰", layout="wide")

CAT_LABEL = {
    "World": "🌍 세계",
    "Business": "💼 비즈니스",
    "Technology": "💻 테크",
    "Science": "🔬 과학·환경",
    "Health": "🏥 헬스",
}

# ── 데이터 로드 ────────────────────────────────────────────
def list_dates() -> list[str]:
    if not REPORTS_DIR.exists():
        return []
    files = sorted(REPORTS_DIR.glob("*.json"), reverse=True)
    return [f.stem for f in files if re.fullmatch(r"\d{4}-\d{2}-\d{2}", f.stem)]

@st.cache_data(ttl=60, show_spinner=False)
def load_items(date: str) -> list[dict]:
    p = REPORTS_DIR / f"{date}.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))

# ── 사이드바 ───────────────────────────────────────────────
dates = list_dates()
qp = st.query_params
default_date = qp.get("date", dates[0] if dates else None)

with st.sidebar:
    st.title("📰 BBC Daily KO")
    st.caption("BBC 뉴스 한국어 다이제스트")
    if not dates:
        st.warning("아직 리포트 없음.\n`python main.py` 실행 후 새로고침.")
        st.stop()

    selected = st.selectbox(
        "📅 날짜",
        dates,
        index=dates.index(default_date) if default_date in dates else 0,
    )
    st.query_params["date"] = selected

    st.divider()
    items_for_count = load_items(selected)
    st.markdown(f"**선택일 기사**: {len(items_for_count)}건")
    st.markdown(f"**전체 리포트**: {len(dates)}일치")
    st.markdown(f"**최신**: `{dates[0]}`")

    st.divider()
    st.markdown("**기사 카드의 `📖 한글 본문 번역` 버튼**을 누르면 gemini가 BBC 원문을 한국어로 번역합니다 (캐시됨).")
    st.markdown("**소스**: [BBC News](https://www.bbc.com/news)")

# ── 메인 ───────────────────────────────────────────────────
items = load_items(selected)
if not items:
    st.error(f"`{selected}.json` 데이터가 없습니다.")
    st.stop()

st.title(f"BBC 데일리 리포트 — {selected}")
st.caption(f"📊 총 {len(items)}건  ·  출처: BBC News")

# 카테고리별 그룹핑
by_cat: dict[str, list[dict]] = {}
for it in items:
    by_cat.setdefault(it["category"], []).append(it)

cat_order = [c for c in CAT_LABEL if c in by_cat]
tabs = st.tabs([f"{CAT_LABEL[c]} ({len(by_cat[c])})" for c in cat_order])

for tab, cat in zip(tabs, cat_order):
    with tab:
        for idx, it in enumerate(by_cat[cat], 1):
            st.subheader(f"{idx}. {it['ko_title']}")
            for line in it["ko_summary"].split("\n"):
                line = line.strip().lstrip("-•·").strip()
                if line:
                    st.markdown(f"- {line}")
            st.caption(f"_원문 제목: {it['title']}_")

            cols = st.columns([1, 1, 4])
            cols[0].link_button("🔗 원문 보기", it["link"], use_container_width=True)

            url = it["link"]
            btn_key = f"trans_{cat}_{idx}_{hash(url) & 0xffffff}"
            state_key = f"shown_{btn_key}"
            if cols[1].button("📖 한글 본문 번역", key=btn_key, use_container_width=True):
                st.session_state[state_key] = True

            if st.session_state.get(state_key):
                with st.spinner("gemini가 본문을 번역 중... (최초 1회만, 다음부터는 캐시)"):
                    try:
                        text, cached = translate_article(url, it["title"])
                        with st.container(border=True):
                            if cached:
                                st.caption("💾 캐시에서 즉시 로드")
                            else:
                                st.caption("✨ 새로 번역됨 (다음부터는 캐시)")
                            st.markdown(text)
                    except Exception as e:
                        st.error(f"번역 실패: {e}")

            st.divider()

st.caption(f"리포트 생성: {selected}  ·  매일 KST 08:00 (cron on EC2)")
