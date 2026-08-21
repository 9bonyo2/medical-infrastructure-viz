"""
공통 CSS 스타일
-----------------
디자인 시안(다크 네이비 사이드바 + 화이트 라운드 카드)을 Streamlit 기본 테마 위에
오버라이드하기 위한 CSS 모음입니다. 색상/간격 등은 팀 협의 후 여기서만 수정하면
전체 페이지에 일괄 반영됩니다.
"""

import streamlit as st

# ── 디자인 토큰 (여기 값만 바꾸면 전체 톤이 바뀝니다) ─────────────────────
COLORS = {
    "sidebar_bg": "#101A33",
    "sidebar_bg_hover": "#1B2A4D",
    "accent_blue": "#2F6FED",
    "accent_red": "#E5484D",
    "accent_teal": "#12B886",
    "text_dark": "#1A1F2B",
    "text_muted": "#6B7280",
    "border": "#E7E9EE",
    "page_bg": "#F5F6F9",
    "card_bg": "#FFFFFF",
}


def inject_base_style():
    st.markdown(
        f"""
        <style>
        /* ── 전체 배경 ───────────────────────────────────────────── */
        .stApp {{
            background-color: {COLORS['page_bg']};
        }}
        [data-testid="stHeader"] {{
            background: transparent;
        }}
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }}

        /* ── Streamlit 기본 사이드바 내비게이션(파일 목록) 숨김 ─────── */
        [data-testid="stSidebarNav"] {{
            display: none;
        }}
        section[data-testid="stSidebar"] {{
            background-color: {COLORS['sidebar_bg']};
            width: 260px !important;
        }}
        section[data-testid="stSidebar"] > div {{
            padding-top: 1.2rem;
        }}
        section[data-testid="stSidebar"] * {{
            color: #E7ECF7;
        }}

        /* ── 사이드바 로고 영역 ─────────────────────────────────────── */
        .sidebar-logo {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 0 4px 18px 4px;
            margin-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
        .sidebar-logo-icon {{
            width: 38px; height: 38px;
            border-radius: 10px;
            background: {COLORS['accent_blue']};
            display: flex; align-items: center; justify-content: center;
            font-size: 20px;
        }}
        .sidebar-logo-title {{
            font-weight: 700; font-size: 15px; line-height: 1.2; color: #fff;
        }}
        .sidebar-logo-sub {{
            font-size: 11.5px; color: #9AA6C2;
        }}
        .sidebar-footer {{
            font-size: 11px; color: #7C88A8; line-height: 1.6;
            padding: 14px 4px 4px 4px; border-top: 1px solid rgba(255,255,255,0.08);
            margin-top: 20px;
        }}

        /* ── KPI 카드 ───────────────────────────────────────────── */
        .kpi-card {{
            background: {COLORS['card_bg']};
            border: 1px solid {COLORS['border']};
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04);
            height: 100%;
        }}
        .kpi-card-header {{
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 10px;
        }}
        .kpi-label {{
            font-size: 13px; color: {COLORS['text_muted']}; font-weight: 500;
        }}
        .kpi-icon {{
            font-size: 16px; opacity: 0.7;
        }}
        .kpi-value {{
            font-size: 26px; font-weight: 700; color: {COLORS['text_dark']};
        }}
        .kpi-unit {{
            font-size: 14px; font-weight: 500; color: {COLORS['text_muted']}; margin-left: 3px;
        }}
        .kpi-delta {{
            font-size: 12.5px; margin-top: 6px; font-weight: 500;
        }}

        /* ── 일반 패널 카드 ─────────────────────────────────────── */
        .panel-card {{
            background: {COLORS['card_bg']};
            border: 1px solid {COLORS['border']};
            border-radius: 14px;
            padding: 20px 22px;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04);
        }}
        .panel-title {{
            font-size: 15.5px; font-weight: 700; color: {COLORS['text_dark']};
            display: flex; align-items: center; gap: 8px;
        }}
        .panel-tag {{
            font-size: 11px; color: {COLORS['text_muted']};
            background: #F0F1F5; border-radius: 6px; padding: 2px 8px;
            font-weight: 500;
        }}

        /* ── TOP5 랭킹 리스트 ───────────────────────────────────── */
        .rank-item {{ margin-bottom: 16px; }}
        .rank-row {{
            display: flex; justify-content: space-between; align-items: center;
            font-size: 14px; margin-bottom: 6px;
        }}
        .rank-badge {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 20px; height: 20px; border-radius: 50%;
            background: {COLORS['accent_red']}; color: #fff;
            font-size: 11.5px; font-weight: 700; margin-right: 8px;
        }}
        .rank-badge-muted {{ background: #C9CDD6; }}
        .rank-name {{ font-weight: 600; color: {COLORS['text_dark']}; }}
        .rank-score {{ font-weight: 700; color: {COLORS['accent_red']}; }}
        .rank-bar-bg {{
            width: 100%; height: 6px; background: #F0F1F5; border-radius: 4px; overflow: hidden;
        }}
        .rank-bar-fill {{
            height: 100%; background: {COLORS['accent_red']}; border-radius: 4px;
        }}

        /* ── 바로가기 카드 ──────────────────────────────────────── */
        .quicklink-card {{
            background: {COLORS['card_bg']};
            border: 1px solid {COLORS['border']};
            border-left: 4px solid {COLORS['accent_blue']};
            border-radius: 12px;
            padding: 18px 20px;
            display: flex; align-items: center; gap: 14px;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04);
        }}
        .quicklink-icon {{ font-size: 22px; }}
        .quicklink-title {{ font-weight: 700; font-size: 14.5px; color: {COLORS['text_dark']}; }}
        .quicklink-desc {{ font-size: 12.5px; color: {COLORS['text_muted']}; margin-top: 2px; }}

        /* ── 프로세스 흐름 ──────────────────────────────────────── */
        .flow-step {{
            display: flex; align-items: center; gap: 10px;
            background: #F8F9FB; border: 1px solid {COLORS['border']};
            border-radius: 10px; padding: 10px 16px; font-size: 13.5px; font-weight: 600;
            color: {COLORS['text_dark']};
        }}
        .flow-num {{
            width: 22px; height: 22px; border-radius: 50%;
            background: {COLORS['text_dark']}; color: #fff;
            display: flex; align-items: center; justify-content: center;
            font-size: 12px; font-weight: 700;
        }}

        /* ── 페이지 타이틀 ──────────────────────────────────────── */
        .page-title {{ font-size: 26px; font-weight: 800; color: {COLORS['text_dark']}; margin-bottom: 2px; }}
        .page-subtitle {{ font-size: 14px; color: {COLORS['text_muted']}; margin-bottom: 22px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
