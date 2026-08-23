import streamlit as st
from utils.style import inject_base_style
from utils.nav import render_sidebar

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
        animation: slideAnimation 12s infinite ease-in-out;
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
        /* 주제: 데이터 기반 공공 인프라 진단 (데이터 분석 및 대시보드 느낌) */
        background: linear-gradient(rgba(15, 23, 42, 0.65), rgba(15, 23, 42, 0.65)), 
                    url('https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=1600&auto=format&fit=crop') center/cover no-repeat;
    }
    .slide-2 {
        /* 주제: 응급의료 및 필수 진료 접근성 (병원 응급실, 의료 현장 느낌) */
        background: linear-gradient(rgba(15, 23, 42, 0.65), rgba(15, 23, 42, 0.65)), 
                    url('https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?q=80&w=1600&auto=format&fit=crop') center/cover no-repeat;
    }
    .slide-3 {
        /* 주제: 초고령사회 대비 복지 인프라 (시니어 케어, 요양 및 복지 느낌) */
        background: linear-gradient(rgba(15, 23, 42, 0.65), rgba(15, 23, 42, 0.65)), 
                    url('https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?q=80&w=1600&auto=format&fit=crop') center/cover no-repeat;
    }
    .slide-4 {
        /* 주제: 저출산 대응 소아의료 체계 (안정적인 소아 의료/병원 배경) */
        background: linear-gradient(rgba(15, 23, 42, 0.65), rgba(15, 23, 42, 0.65)), 
                    url('https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?q=80&w=1600&auto=format&fit=crop') center/cover no-repeat;
    }

    
    /* 슬라이드 이미지 속 텍스트 폰트 스타일 설정 */
    .hero-title {
        font-size: 50px;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 12px;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .hero-subtitle {
        font-size: 20px;
        color: #E2E8F0;
        max-width: 990px;
        margin: 0 auto;
        line-height: 1.7;
        font-weight: 400;
    }

    
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


    /* [ 응급의료, 고령 의료/복지, 소아의료 ] section 텍스트 설정 */
    .section-header {
        font-size: 22px;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: -60px;
        padding-bottom: 8px;
        border-bottom: 2px solid #E2E8F0;
        text-align: center;
    }

    
    /* 7개 카드의 공백 조절 */
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
""", unsafe_allow_html=True)


# ── 1. 상단: 좌우 슬라이드 배너 (4개) ────────────────
st.markdown("""
    <div class="slider-wrapper">
        <div class="slides-container">
            <!-- Slide 1 -->
            <div class="slide slide-1">
                <div class="hero-title">데이터로 진단하는 대한민국 의료·복지 격차</div>
                <div class="hero-subtitle">
                    10개년 공공데이터와 정규화 알고리즘을 통해 지역별 인프라 수급 불균형과 취약지를 입체적으로 조명합니다.
                </div>
            </div>
            <!-- Slide 2 -->
            <div class="slide slide-2">
                <div class="hero-title">생명과 직결되는 응급·필수의료 접근성의 재발견</div>
                <div class="hero-subtitle">
                    대도시권 쏠림 현상과 응급의료 격차를 해소하고, 객관적 지표에 기반한 실효성 있는 정책 대안을 제시합니다.
                </div>
            </div>
            <!-- Slide 3 -->
            <div class="slide slide-3">
                <div class="hero-title">초고령사회, 고령 복지·의료 인프라의 균형을 찾다</div>
                <div class="hero-subtitle">
                    급증하는 고령 인구 대비 요양병원과 노인복지시설의 지역별 수급 상태를 진단하고 미래 수요를 예측합니다.
                </div>
            </div>
            <!-- Slide 4 -->
            <div class="slide slide-4">
                <div class="hero-title">저출산 파고 속, 소아청소년과 인프라 붕괴에 대응하다</div>
                <div class="hero-subtitle">
                    출산율 감소와 소아과 인프라 위축 간의 상관관계를 분석하여 우리 아이들의 건강권을 지킬 취약지를 도출합니다.
                </div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)


# ── 2. 하단: CONTENTS (카테고리별 컬럼 구분) ─────────────────────────
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
                "target": "pages/2_응급의료_고령_BY.py",
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
                "target": "pages/6_출산율_소아과_JH.py",
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