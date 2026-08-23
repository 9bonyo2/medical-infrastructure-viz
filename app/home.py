#  해당 페이지는 엔드리 포인트가 되는 파일이기도 하지만 대쉬보드 페이지 코드라고 생각해주시면 됩니다.
import streamlit as st

from utils.style import inject_base_style
from utils.nav import render_sidebar
from utils.components import (
    kpi_card,
    region_panel,
    top5_ranking_panel,
    quicklink_card,
    process_flow,
)
from utils.sample_data import (
    get_overview_kpis,
    get_region_vulnerability_df,
    get_top5_vulnerable_df,
)

# ── 페이지 설정 ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="지역 의료 인프라 균형 대시보드",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_base_style()
render_sidebar(active_key="overview")

# ── Custom CSS ────────────────────────────────────────────────────────
st.markdown("""
    <style>
    /* 전체 배경 회색톤 적용 */
    .stApp {
        background-color: #F8FAFC;
    }

    /* 최상단 타이틀 헤더 스타일 */
    .main-header {
        text-align: center;
        padding: 20px 0 10px 0;
        margin-bottom: -30px;
    }
    .main-header h1 {
        font-size: 36px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .main-header p {
        font-size: 15px;
        color: #64748B;
        margin-top: 8px;
        font-weight: 500;
    }

    /* 1. 상단 슬라이드 배너 (Carousel) 컨테이너 */
    .slider-wrapper {
        position: relative;
        width: 100%;
        height: 60vh;
        min-height: 520px;
        margin-top: 50px;
        margin-bottom: 35px;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
    }

    .slides-container {
        display: flex;
        width: 400%; /* 4개 슬라이드 (100% * 4) */
        height: 100%;
        animation: slideAnimation 20s infinite ease-in-out;
    }

    /* 슬라이드 별 배경 이미지 및 레이아웃 */
    .slide {
        width: 25%;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 0 50px;
        text-align: center;
        box-sizing: border-box;
    }

    .slide-1 {
        background: linear-gradient(rgba(15, 23, 42, 0.65), rgba(15, 23, 42, 0.65)), 
                    url('https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?q=80&w=1600&auto=format&fit=crop') center/cover no-repeat;
    }
    .slide-2 {
        background: linear-gradient(rgba(15, 23, 42, 0.65), rgba(15, 23, 42, 0.65)), 
                    url('https://images.unsplash.com/photo-1581594693702-fbdc51b2763b?q=80&w=1600&auto=format&fit=crop') center/cover no-repeat;
    }
    .slide-3 {
        background: linear-gradient(rgba(15, 23, 42, 0.65), rgba(15, 23, 42, 0.65)), 
                    url('https://images.unsplash.com/photo-1516549655169-df83a0774514?q=80&w=1600&auto=format&fit=crop') center/cover no-repeat;
    }
    .slide-4 {
        background: linear-gradient(rgba(15, 23, 42, 0.65), rgba(15, 23, 42, 0.65)), 
                    url('https://images.unsplash.com/photo-1504813184591-01572f98c85f?q=80&w=1600&auto=format&fit=crop') center/cover no-repeat;
    }

    /* 슬라이드 텍스트 스타일링 */
    .hero-title {
        font-size: 38px;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 12px;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .hero-subtitle {
        font-size: 16px;
        color: #E2E8F0;
        max-width: 850px;
        margin: 0 auto;
        line-height: 1.7;
        font-weight: 400;
    }

# ── 상세 분석 영역 바로가기 ──────────────────────────────────────────────
# TODO: 추후에 각 카드 클릭 시 해당 페이지로 이동하도록 기능 추가 필요
st.markdown("##### 상세 분석 영역 바로가기")
q1, q2 = st.columns(2, gap="medium")
with q1:
    quicklink_card("🩺", "응급의료 균형", "인구 대비 권역별 응급의료기관의 위치와 병상 수용 능력 정보 확인",
                    border_color="#2F6FED")
with q2:
    quicklink_card("👥", "고령화와 노인의료", "급증하는 고령인구와 시니어 맞춤 요양·복지·의료시설의 수급 미스매치 비교",
                    border_color="#12B886")

    /* 자동 전환 CSS 애니메이션 Keyframes (4개 슬라이드 루프) */
    @keyframes slideAnimation {
        0%, 20%   { transform: translateX(0%); }
        25%, 45%  { transform: translateX(-25%); }
        50%, 70%  { transform: translateX(-50%); }
        75%, 95%  { transform: translateX(-75%); }
        100%      { transform: translateX(0%); }
    }


    /* Streamlit 기본 세로 간격 조정 */
    div[data-testid="stVerticalBlock"] {
        gap: 0rem !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
    }

    /* 2. CONTENTS 타이틀 및 섹션 헤더 */
    .contents-title {
        text-align: center;
        font-size: 35px;
        font-weight: 800;
        color: #1E293B;
        margin-top: 30px;
        margin-bottom: 30px;
        letter-spacing: 1.2px;
        line-height: 1.0;
        position: relative;
        z-index: 10;
    }

# ── 프로젝트 분석 흐름 ───────────────────────────────────────────────────
# TODO: 해당 항목은 논의 후 구체화가 필요해 보임.
with st.container(border=True):
    st.markdown("##### 프로젝트 분석 흐름")
    process_flow(["데이터 수집", "데이터 정제 및 표준화", "지역별 지표 분석", "의료 취약점수 산출", "시각화 및 결과 해석"])
    .section-header {
        font-size: 22px;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: -60px;
        padding-bottom: 8px;
        border-bottom: 2px solid #E2E8F0;
        text-align: center;
    }

    /* 3. 카드 래퍼 및 버튼 스타일 */
    .card-wrapper {
        position: relative;
        width: 100%;
        height: 96px;
        margin-top: -20px;
        margin-bottom: 10px;
    }

    .card-box {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 96px;
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 0 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        display: flex;
        align-items: center;
        justify-content: center; /* 카드 내부 전체 가운데 정렬 */
        transition: all 0.2s ease-in-out;
        pointer-events: none;
        z-index: 1;
        box-sizing: border-box;
    }
    
    .card-wrapper:hover .card-box {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.06);
        border-color: #38BDF8;
    }

    .card-inner {
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center; /* 텍스트 가운데 정렬 */
        width: 100%;
    }

    .card-text-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center; /* 텍스트 박스 요소들 중앙 배치 */
        width: 100%;
    }
    .card-subtext {
        font-size: 12px;
        font-weight: 600;
        color: #666666;
        margin-top: 2px;
    }
    .card-maintext {
        font-size: 21px;
        font-weight: 700;
        color: #1E293B;
    }

    .card-wrapper [data-testid="stElementContainer"]:has(div[data-testid="stButton"]) {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 96px !important;
        margin: 0 !important;
        padding: 0 !important;
        z-index: 2 !important;
    }

    .card-wrapper div[data-testid="stButton"] {
        width: 100% !important;
        height: 96px !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .card-wrapper div[data-testid="stButton"] > button {
        width: 100% !important;
        height: 96px !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: transparent !important;
        cursor: pointer !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .card-wrapper div[data-testid="stButton"] > button:hover,
    .card-wrapper div[data-testid="stButton"] > button:focus,
    .card-wrapper div[data-testid="stButton"] > button:active {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: transparent !important;
    }
    </style>
""", 
unsafe_allow_html=True)

# ── 1. 상단: 좌우 슬라이드 배너 (4개 배경) ────────────────
st.markdown("""
    <div class="slider-wrapper">
        <div class="slides-container">
            <!-- Slide 1 -->
            <div class="slide slide-1">
                <div class="hero-title">의료정착 및 지역 균형 분석 시스템</div>
                <div class="hero-subtitle">
                    우리는 국민과 지역사회를 위한 보건의료복지 지표를 분석하고 선도합니다.<br>
                    대한민국 시·도별 인구 구조 변화와 필수 의료 시설 공급 수준을 정밀 분석하여 의료 인프라 불균형 해소를 위한 인사이트를 제공합니다.
                </div>
            </div>
            <!-- Slide 2 -->
            <div class="slide slide-2">
                <div class="hero-title">의료정착 및 지역 균형 분석 시스템</div>
                <div class="hero-subtitle">
                    우리는 국민과 지역사회를 위한 보건의료복지 지표를 분석하고 선도합니다.<br>
                    대한민국 시·도별 인구 구조 변화와 필수 의료 시설 공급 수준을 정밀 분석하여 의료 인프라 불균형 해소를 위한 인사이트를 제공합니다.
                </div>
            </div>
            <!-- Slide 3 -->
            <div class="slide slide-3">
                <div class="hero-title">의료정착 및 지역 균형 분석 시스템</div>
                <div class="hero-subtitle">
                    우리는 국민과 지역사회를 위한 보건의료복지 지표를 분석하고 선도합니다.<br>
                    대한민국 시·도별 인구 구조 변화와 필수 의료 시설 공급 수준을 정밀 분석하여 의료 인프라 불균형 해소를 위한 인사이트를 제공합니다.
                </div>
            </div>
            <!-- Slide 4 -->
            <div class="slide slide-4">
                <div class="hero-title">의료정착 및 지역 균형 분석 시스템</div>
                <div class="hero-subtitle">
                    우리는 국민과 지역사회를 위한 보건의료복지 지표를 분석하고 선도합니다.<br>
                    대한민국 시·도별 인구 구조 변화와 필수 의료 시설 공급 수준을 정밀 분석하여 의료 인프라 불균형 해소를 위한 인사이트를 제공합니다.
                </div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── 2. 하단: CONTENTS (섹션별 컬럼 구분) ─────────────────────────
st.markdown('<div class="contents-title">CONTENTS</div>', unsafe_allow_html=True)

# 카테고리별 데이터 정의
sections = [
    {
        "title": "응급의료",
        "cards": [
            {
                "sub": "시도별 응급의료 접근성 격차와 전원율 상관관계를 시각화",
                "title": "응급의료 균형 분석",
                "target": "pages/1_응급의료_균형_JH.py",
            },
            {
                "sub": "10개년 데이터의 상관계수 변동 패턴을 분석",
                "title": "응급의료 고령화 분석",
                "target": "pages/2_응급의료_균형_BY.py",
            },
        ]
    },
    {
        "title": "고령 의료/복지",
        "cards": [
            {
                "sub": "지역별 고령화율 정도를 분석",
                "title": "고령화율 분석",
                "target": "pages/3_고령화_의료시설_SJ.py",
            },
            {
                "sub": "복지시설과 의료시설의 수급 균형 정도를 분석",
                "title": "고령 인프라 수급 균형 추이",
                "target": "pages/5_고령화_의료시설_JY.py",
            },
            {
                "sub": "10개년 데이터의 상관계수 변동 패턴을 분석",
                "title": "고령 인구대비 인프라 추이",
                "target": "pages/4_고령화_의료시설_SY.py",
            },
        ]
    },
    {
        "title": "소아의료",
        "cards": [
            {
                "sub": "소아청소년과 인프라의 위축 경향성을 파악",
                "title": "아동 수 대비 소아과 현황",
                "target": "pages/6_출산율과_소아과_JH.py",
            },
            {
                "sub": "저출산 추세 속에서 소아청소년과 인프라의 위축 경향성을 파악",
                "title": "출산율 대비 소아과 현황",
                "target": "pages/7_출산율_소아과_DY.py",
            },
        ]
    }
]

cols = st.columns(3, gap="large")

# 카드 렌더링 헬퍼 함수
def render_card(card, key_suffix):
    st.markdown('<div class="card-wrapper">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="card-box">
            <div class="card-inner">
                <div class="card-text-container">
                    <div class="card-maintext">{card['title']}</div>
                    <div class="card-subtext">{card['sub']}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("", key=f"btn_{key_suffix}", use_container_width=True):
        st.switch_page(card["target"])
    st.markdown('</div>', unsafe_allow_html=True)

# 컬럼별 섹션 타이틀 및 카드 배치
for idx, section in enumerate(sections):
    with cols[idx]:
        st.markdown(f'<div class="section-header">{section["title"]}</div>', unsafe_allow_html=True)
        for card_idx, card in enumerate(section["cards"]):
            render_card(card, f"{idx}_{card_idx}")

st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
