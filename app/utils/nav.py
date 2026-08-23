"""
사이드바 내비게이션
--------------------
streamlit-option-menu 를 사용해 디자인 시안과 동일한 다크 네이비 사이드바 메뉴를 구성합니다.
페이지 전환은 st.switch_page 로 처리합니다 (Streamlit >= 1.27 필요).

새 분석 페이지를 추가할 때는 PAGES 리스트에 항목만 추가하면
사이드바 메뉴에 자동으로 반영됩니다.
"""

import streamlit as st
from streamlit_option_menu import option_menu

from utils.style import COLORS

# key: 내부 식별자 / label: 화면 표시 텍스트 / icon: bootstrap-icons 이름 / target: 실제 파일 경로
PAGES = [
    {
        "key": "overview",
        "label": "메인 홈 (Home)",
        "icon": "activity",
        "target": "home.py",
    },
    {
        "key": "emergency_jh",
        "label": "응급의료 균형 분석",
        "icon": "heart-pulse",
        "target": "pages/1_응급의료_균형_JH.py",
    },
    {
        "key": "emergency_by",
        "label": "응급의료 고령화 분석",
        "icon": "heart-pulse-fill",
        "target": "pages/2_응급의료_균형_BY.py",
    },
    {
        "key": "aging_sj",
        "label": "고령화율 분석",
        "icon": "people",
        "target": "pages/3_고령화_의료시설_SJ.py",
    },
    {
        "key": "aging_jy",
        "label": "고령 인프라 수급 균형 추이",
        "icon": "building",
        "target": "pages/5_고령화_의료시설_JY.py",
    },
    {
        "key": "aging_sy",
        "label": "고령 인구 대비 인프라 추이",
        "icon": "person-gear",
        "target": "pages/4_고령화_의료시설_SY.py",
    },
    {
        "key": "birth_jh",
        "label": "아동 수 대비 소아과 현황",
        "icon": "emoji-smile",
        "target": "pages/6_출산율과_소아과_JH.py",
    },
    {
        "key": "pediatric_dy",
        "label": "출산율 대비 소아과 현황",
        "icon": "emoji-smile-fill",
        "target": "pages/7_출산율_소아과_DY.py",
    },
]
def render_sidebar(active_key: str):
    """공통 사이드바를 렌더링하고, 메뉴 선택 시 해당 페이지로 전환합니다."""
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-logo">
                <div class="sidebar-logo-icon">🏥</div>
                <div>
                    <div class="sidebar-logo-title">지역 의료 인프라</div>
                    <div class="sidebar-logo-sub">균형 분석 시스템</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        labels = [p["label"] for p in PAGES]
        icons = [p["icon"] for p in PAGES]
        default_index = next((i for i, p in enumerate(PAGES) if p["key"] == active_key), 0)

        selected_label = option_menu(
            menu_title=None,
            options=labels,
            icons=icons,
            default_index=default_index,
            styles={
                "container": {"padding": "0!important", "background-color": COLORS["sidebar_bg"], "border-radius": "none"},
                "icon": {"color": "#FFFFFF", "font-size": "15px", "opacity": "0.85"},
                "nav-link": {
                    "font-size": "14px",
                    "font-weight": "500",
                    "text-align": "left",
                    "margin": "2px 0",
                    "padding": "10px 12px",
                    "color": "#FFFFFF",
                    "background-color": "transparent",
                    "--hover-color": "rgba(255,255,255,0.08)",
                },
                "nav-link-selected": {
                    "background-color": "rgba(255,255,255,0.12)",
                    "color": "#FFFFFF",
                    "font-weight": "700",
                    "box-shadow": "none",
                },
                "icon-selected": {"color": "#FFFFFF"},
            },
        )

        selected_page = next(p for p in PAGES if p["label"] == selected_label)
        if selected_page["key"] != active_key:
            st.switch_page(selected_page["target"])

        st.markdown(
            """
            <div class="sidebar-footer">
                분석 기간: 2015 ~ 2024<br/>
                분석 단위: 전국 17개 시도<br/>
                데이터 출처: 공공데이터포털, 건강보험심사평가원
            </div>
            """,
            unsafe_allow_html=True,
        )