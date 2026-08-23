import os
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── 경로 및 모듈 설정 ──────────────────────────────────────────────────
CURRENT_DIR = Path(__file__).resolve().parent

# 루트 디렉토리 찾기 (app/pages 내부인 경우와 루트에 위치한 경우 모두 대응)
if CURRENT_DIR.name == "pages" and CURRENT_DIR.parent.name == "app":
    PROJECT_ROOT = CURRENT_DIR.parents[1]
elif CURRENT_DIR.name == "app":
    PROJECT_ROOT = CURRENT_DIR.parent
else:
    PROJECT_ROOT = CURRENT_DIR

# sys.path 등록으로 utils 모듈 import 지원
APP_DIR = PROJECT_ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# 공통 스타일 import 시도 (실패 시 안전 fallback 제공)
try:
    from utils.style import inject_base_style, COLORS
    from utils.nav import render_sidebar
    HAS_UTILS = True
except Exception:
    HAS_UTILS = False
    COLORS = {
        "sidebar_bg": "#101A33",
        "accent_blue": "#2F6FED",
        "accent_red": "#E5484D",
        "accent_teal": "#12B886",
        "text_dark": "#1A1F2B",
        "text_muted": "#6B7280",
        "border": "#E7E9EE",
        "page_bg": "#F5F6F9",
        "card_bg": "#FFFFFF",
    }

# Streamlit 페이지 기본 설정
st.set_page_config(
    page_title="고령화율 분석 | 지역 의료 인프라",
    page_icon="👵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 공통 CSS 및 사이드바 주입
if HAS_UTILS:
    try:
        inject_base_style()
        render_sidebar(active_key="aging_sj")
    except Exception:
        pass

# 커스텀 컴포넌트 CSS 추가 (KPI 카드 & 인사이트 박스)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F8FAFC;
    }
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #64748B;
        font-size: 13px;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 700;
        color: #0F172A;
        margin: 8px 0 4px 0;
    }
    .kpi-subtext-up {
        font-size: 12px;
        font-weight: 600;
        color: #22A06B;
    }
    .kpi-subtext-down {
        font-size: 12px;
        font-weight: 600;
        color: #E5484D;
    }
    .insight-card {
        background: #FFFFFF;
        border-left: 4px solid #2F6FED;
        border-top: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 14px 16px;
        margin-bottom: 12px;
        min-height: 96px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .insight-title {
        font-weight: 700;
        color: #1E293B;
        font-size: 14px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .insight-desc {
        color: #475569;
        font-size: 13px;
        line-height: 1.5;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ── 데이터 로딩 함수 (캐시 적용) ──────────────────────────────────────────
@st.cache_data
def load_analysis_data():
    processed_dir = PROJECT_ROOT / "data" / "aging" / "processed"
    
    # 1. 추이 데이터
    trend_path = processed_dir / "aging_trend.csv"
    if not trend_path.exists():
        # 데이터가 없을 경우 전처리 및 분석 스크립트 실행
        try:
            from src.aging.collect.preprocess_aging import main as run_step1
            from src.aging.analysis.analyze_aging import main as run_step2
            run_step1()
            run_step2()
        except Exception as e:
            st.error(f"데이터 파일 자동 생성 실패: {e}")

    df_trend = pd.read_csv(trend_path)
    df_cagr = pd.read_csv(processed_dir / "aging_cagr.csv")
    df_risk = pd.read_csv(processed_dir / "aging_risk_rank.csv")

    # GeoJSON 지도데이터 로드
    geo_path = PROJECT_ROOT / "data" / "aging" / "raw" / "skorea_sido_boundary.geojson"
    geo_data = None
    if geo_path.exists():
        with open(geo_path, encoding="utf-8") as f:
            geo_data = json.load(f)
        # properties에 표준 시도명 (sido) 맵핑
        eng_to_std = {
            "Seoul": "서울특별시", "Busan": "부산광역시", "Daegu": "대구광역시", "Incheon": "인천광역시",
            "Gwangju": "광주광역시", "Daejeon": "대전광역시", "Ulsan": "울산광역시", "Sejongsi": "세종특별자치시",
            "Gyeonggi-do": "경기도", "Gangwon-do": "강원특별자치도", "Chungcheongbuk-do": "충청북도",
            "Chungcheongnam-do": "충청남도", "Jeollabuk-do": "전북특별자치도", "Jeollanam-do": "전라남도",
            "Gyeongsangbuk-do": "경상북도", "Gyeongsangnam-do": "경상남도", "Jeju-do": "제주특별자치도"
        }
        for feature in geo_data["features"]:
            eng = feature["properties"].get("name_eng")
            feature["properties"]["sido"] = eng_to_std.get(eng, feature["properties"].get("name"))

    return df_trend, df_cagr, df_risk, geo_data

# 데이터 로드
df_trend, df_cagr, df_risk, geo_data = load_analysis_data()
years_list = sorted(df_trend['연도'].unique().tolist())

# ── 1. 상단 Header & '기준 연도' 선택 ───────────────────────────────────────
col_title, col_year_select = st.columns([3.2, 1.0])

with col_title:
    st.markdown(
        """
        <div style='display:flex; align-items:center; gap:10px;'>
            <h1 style='margin:0; font-size:28px; font-weight:800; color:#0F172A;'>고령화율 분석</h1>
            <span style='background:#E2E8F0; color:#475569; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600;'>2015~2024</span>
        </div>
        <p style='color:#64748B; margin-top:4px; font-size:14px;'>
            대한민국 17개 시도별 고령화 인구 추이, 연평균 증감률(CAGR) 및 고령화 취약/위험 지역을 종합 분석합니다.
        </p>
        """,
        unsafe_allow_html=True
    )

with col_year_select:
    selected_global_year = st.selectbox(
        "📅 기준 연도 선택",
        options=years_list,
        index=len(years_list) - 1,
        key="global_year_select"
    )

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# ── 상단 KPI 카드 계산 ──────────────────────────────────────────────────────
# 선택 연도 데이터
df_curr = df_trend[df_trend['연도'] == selected_global_year]
df_prev = df_trend[df_trend['연도'] == (selected_global_year - 1)] if (selected_global_year - 1) in years_list else df_curr

# 1) 전국 고령화율
nat_curr = df_curr[df_curr['시도'] == '전국']
nat_prev = df_prev[df_prev['시도'] == '전국']
nat_val = nat_curr['고령화율 (%)'].values[0] if not nat_curr.empty else 0
nat_prev_val = nat_prev['고령화율 (%)'].values[0] if not nat_prev.empty else nat_val
nat_delta = round(nat_val - nat_prev_val, 2)

# 2) 17개 시도 기준 최고/최저 고령화 지역
sido_curr = df_curr[df_curr['시도'] != '전국'].sort_values(by='고령화율 (%)', ascending=False)
sido_prev = df_prev[df_prev['시도'] != '전국'].set_index('시도')['고령화율 (%)']

max_row = sido_curr.iloc[0]
max_sido = max_row['시도']
max_val = max_row['고령화율 (%)']
max_prev_val = sido_prev.get(max_sido, max_val)
max_delta = round(max_val - max_prev_val, 2)

min_row = sido_curr.iloc[-1]
min_sido = min_row['시도']
min_val = min_row['고령화율 (%)']
min_prev_val = sido_prev.get(min_sido, min_val)
min_delta = round(min_val - min_prev_val, 2)

# 3) 초고령사회 진입 지역 수 (20% 이상)
super_aged_count = len(sido_curr[sido_curr['고령화율 (%)'] >= 20.0])
super_aged_prev_count = len(sido_prev[sido_prev >= 20.0])
super_aged_delta = super_aged_count - super_aged_prev_count

# KPI HTML 배치
kpi1_sub_cls = "kpi-subtext-up" if nat_delta >= 0 else "kpi-subtext-down"
kpi1_arrow = "▲" if nat_delta >= 0 else "▼"

kpi2_sub_cls = "kpi-subtext-up" if max_delta >= 0 else "kpi-subtext-down"
kpi2_arrow = "▲" if max_delta >= 0 else "▼"

kpi3_sub_cls = "kpi-subtext-up" if min_delta >= 0 else "kpi-subtext-down"
kpi3_arrow = "▲" if min_delta >= 0 else "▼"

kpi4_sub_cls = "kpi-subtext-up" if super_aged_delta >= 0 else "kpi-subtext-down"
kpi4_arrow = "▲" if super_aged_delta >= 0 else "▼"

st.markdown(
    f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-header">
                <span>전국 평균 고령화율</span>
                <span>🇰🇷</span>
            </div>
            <div class="kpi-value">{nat_val:.2f}%</div>
            <div class="{kpi1_sub_cls}">전년 대비 {kpi1_arrow} {abs(nat_delta):.2f}%p</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span>최고 고령화 지역</span>
                <span>🚨</span>
            </div>
            <div class="kpi-value">{max_sido} ({max_val:.2f}%)</div>
            <div class="{kpi2_sub_cls}">전년 대비 {kpi2_arrow} {abs(max_delta):.2f}%p</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span>최저 고령화 지역</span>
                <span>🌱</span>
            </div>
            <div class="kpi-value">{min_sido} ({min_val:.2f}%)</div>
            <div class="{kpi3_sub_cls}">전년 대비 {kpi3_arrow} {abs(min_delta):.2f}%p</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span>초고령사회 진입 지역</span>
                <span>🏛️</span>
            </div>
            <div class="kpi-value">{super_aged_count}개 시도</div>
            <div class="{kpi4_sub_cls}">전년 대비 {kpi4_arrow} {abs(super_aged_delta)}개 지역</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ── 2. 중단 (지역별 고령화 위험/취약 순위) ─────────────────────────────────
st.markdown("<h3 style='font-size:18px; font-weight:700; color:#1E293B; margin-bottom:12px;'>🗺️ [{0}년] 지역별 고령화 위험/취약 지도 및 TOP 3</h3>".format(selected_global_year), unsafe_allow_html=True)

col_map, col_top3 = st.columns([2, 1])

with col_map:
    # Plotly 제목은 외부 HTML로 처리
    st.markdown("<div style='font-size:14px; font-weight:600; color:#475569; margin-bottom:6px;'>시도별 고령화율 지리적 분포 (취약: 🔴, 안전: 🟢)</div>", unsafe_allow_html=True)
    
    if geo_data:
        # 지도 생성
        fig_map = px.choropleth_mapbox(
            sido_curr,
            geojson=geo_data,
            locations='시도',
            featureidkey="properties.sido",
            color='고령화율 (%)',
            color_continuous_scale='Reds', # 취약지역: 빨강 계열
            range_color=[10, 30],
            mapbox_style="carto-positron",
            zoom=5.7,
            center={"lat": 35.8, "lon": 127.8},
            hover_name='시도',
            hover_data={'시도': False, '고령화율 (%)': ':.2f', '고령화 단계': True, '총인구 (명)': ':,', '65세이상 인구 (명)': ':,'}
        )
        fig_map.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            height=380,
            coloraxis_colorbar=dict(
                title="고령화율(%)",
                thickness=12,
                len=0.75
            )
        )
        st.plotly_chart(fig_map, use_container_width=True, key="middle_map_chart")
    else:
        # GeoJSON 파일 예외 대응 (막대 그래프 대체)
        fig_fallback = px.bar(
            sido_curr,
            x='시도',
            y='고령화율 (%)',
            color='고령화율 (%)',
            color_continuous_scale='Reds'
        )
        fig_fallback.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=380)
        st.plotly_chart(fig_fallback, use_container_width=True, key="middle_map_fallback")

with col_top3:
    st.markdown(f"<div style='font-size:14px; font-weight:600; color:#475569; margin-bottom:6px;'>🚨 {selected_global_year}년 고령화 위험 지역 TOP 3</div>", unsafe_allow_html=True)
    
    top3_df = sido_curr.head(3).copy()
    top3_df['순위'] = [f"🥇 1위", "🥈 2위", "🥉 3위"]
    top3_display = top3_df[['순위', '시도', '고령화율 (%)', '고령화 단계']]
    
    # TOP 3 커스텀 리스트 카드 출력
    for idx, row in top3_df.iterrows():
        rank_emoji = "🥇" if row['시도'] == top3_df.iloc[0]['시도'] else "🥈" if row['시도'] == top3_df.iloc[1]['시도'] else "🥉"
        st.markdown(
            f"""
            <div style='background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid #E5484D; border-radius:8px; padding:12px 14px; margin-bottom:10px;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <span style='font-weight:700; font-size:15px; color:#1E293B;'>{rank_emoji} {row['시도']}</span>
                    <span style='background:#FFE5E5; color:#E5484D; font-size:11px; font-weight:700; padding:2px 8px; border-radius:10px;'>{row['고령화 단계']}</span>
                </div>
                <div style='display:flex; justify-content:space-between; margin-top:6px; color:#64748B; font-size:13px;'>
                    <span>고령화율</span>
                    <span style='font-weight:700; color:#D92D20;'>{row['고령화율 (%)']:.2f}%</span>
                </div>
                <div style='display:flex; justify-content:space-between; margin-top:2px; color:#64748B; font-size:12px;'>
                    <span>65세 이상 인구</span>
                    <span>{row['65세이상 인구 (명)']:,} 명</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='font-size:12px; color:#94A3B8; margin-top:4px;'>* 고령화율 20% 이상 시 '초고령사회'로 분류됩니다.</div>", unsafe_allow_html=True)

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# ── 3. 하단 (상세 데이터 항목 3대 분석 섹션 - 탭 구성) ──────────────────────────
st.markdown("<h3 style='font-size:18px; font-weight:700; color:#1E293B; margin-bottom:12px;'>📊 상세 데이터 3대 영역 세부 분석</h3>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "📈 (1) 지역별 고령화율 추이",
    "📊 (2) 고령화율 연평균 증감률 (CAGR)",
    "🏆 (3) 지역별 고령화 위험/취약 순위"
])

# ── TAB 1: (1) 지역별 고령화율 추이 ───────────────────────────────────────────
with tab1:
    t1_head_col, t1_select_col = st.columns([3, 1])
    with t1_head_col:
        st.markdown("<h4 style='font-size:16px; font-weight:700; color:#1E293B; margin-top:8px;'>2015년 ~ 2024년 시도별 고령화율 변화 추이</h4>", unsafe_allow_html=True)
    with t1_select_col:
        t1_selected_sido = st.selectbox(
            "분석 시도 선택",
            options=["전체 시도 비교"] + sorted(df_trend[df_trend['시도'] != '전국']['시도'].unique().tolist()),
            key="tab1_sido_select"
        )

    # 그래프 렌더링
    if t1_selected_sido == "전체 시도 비교":
        fig_t1 = px.line(
            df_trend,
            x='연도',
            y='고령화율 (%)',
            color='시도',
            markers=True,
            color_discrete_map={'전국': '#000000'}
        )
    else:
        filtered_t1 = df_trend[df_trend['시도'].isin(['전국', t1_selected_sido])]
        fig_t1 = px.line(
            filtered_t1,
            x='연도',
            y='고령화율 (%)',
            color='시도',
            markers=True,
            color_discrete_map={'전국': '#94A3B8', t1_selected_sido: '#2F6FED'}
        )
    
    # 14%(고령사회), 20%(초고령사회) 임계선 추가
    fig_t1.add_hline(y=14.0, line_dash="dash", line_color="#F59E0B", annotation_text="고령사회 (14%)", annotation_position="bottom right")
    fig_t1.add_hline(y=20.0, line_dash="dash", line_color="#E5484D", annotation_text="초고령사회 (20%)", annotation_position="top right")

    fig_t1.update_layout(
        title="", # 외부 HTML 제목 지정
        xaxis_title="연도",
        yaxis_title="고령화율 (%)",
        height=400,
        margin=dict(l=20, r=20, t=10, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_t1, use_container_width=True, key="tab1_line_chart")

    # 핵심 인사이트 (2, 2 배열)
    st.markdown("<h5 style='font-size:15px; font-weight:700; color:#1E293B; margin:16px 0 10px 0;'>💡 3대 분석 핵심 인사이트 (고령화율 추이)</h5>", unsafe_allow_html=True)
    
    ins_col1, ins_col2 = st.columns(2)
    with ins_col1:
        st.markdown(
            """
            <div class="insight-card">
                <div class="insight-title">💡 전국 초고령사회 공식 진입</div>
                <div class="insight-desc">전국 평균 고령화율이 2015년 13.15%에서 2024년 20.03%로 가파르게 상승하여 대한민국 전체가 '초고령사회' 단계에 도달했습니다.</div>
            </div>
            <div class="insight-card">
                <div class="insight-title">💡 수도권 vs 지방 고령화 격차 확대</div>
                <div class="insight-desc">전남(27.18%), 경북(26.04%) 등 도 단위 지역의 고령화율은 25%를 상회하는 반면, 경기(16.57%)는 상대적으로 유입 인구가 많아 낮게 유지됩니다.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with ins_col2:
        st.markdown(
            """
            <div class="insight-card">
                <div class="insight-title">💡 세종특별자치시의 최저 고령화율 유지</div>
                <div class="insight-desc">세종시는 2024년 기준 11.41%로 전국 17개 시도 중 가장 젊은 도시 지위를 유지하고 있으며, 유일한 10%대 지역입니다.</div>
            </div>
            <div class="insight-card">
                <div class="insight-title">💡 초고령사회 이행 속도 가속화</div>
                <div class="insight-desc">2017년 고령사회(14%) 진입 이후 불과 7년 만에 20%를 돌파하여 주요 선진국 대비 압도적으로 빠른 고령화 전환 속도를 나타냅니다.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ── TAB 2: (2) 고령화율 연평균 증감률 (CAGR) ─────────────────────────────────
with tab2:
    t2_head_col, t2_select_col = st.columns([3, 1])
    with t2_head_col:
        st.markdown("<h4 style='font-size:16px; font-weight:700; color:#1E293B; margin-top:8px;'>2015년 대비 2024년 고령화율 연평균 증감률 (CAGR)</h4>", unsafe_allow_html=True)
    with t2_select_col:
        t2_sort_opt = st.selectbox(
            "정렬 옵션",
            options=["CAGR 높은순", "CAGR 낮은순", "변화폭(%p) 높은순"],
            key="tab2_sort_select"
        )

    # 데이터 정렬
    sido_cagr_df = df_cagr[df_cagr['시도'] != '전국'].copy()
    if t2_sort_opt == "CAGR 높은순":
        sido_cagr_df.sort_values(by='CAGR(%)', ascending=True, inplace=True)
    elif t2_sort_opt == "CAGR 낮은순":
        sido_cagr_df.sort_values(by='CAGR(%)', ascending=False, inplace=True)
    else:
        sido_cagr_df.sort_values(by='변화폭(%p)', ascending=True, inplace=True)

    fig_t2 = px.bar(
        sido_cagr_df,
        y='시도',
        x='CAGR(%)',
        orientation='h',
        text='CAGR(%)',
        color='CAGR(%)',
        color_continuous_scale='Reds'
    )
    fig_t2.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig_t2.update_layout(
        title="",
        xaxis_title="연평균 증감률 (CAGR %)",
        yaxis_title="시도",
        height=420,
        margin=dict(l=20, r=20, t=10, b=20)
    )
    st.plotly_chart(fig_t2, use_container_width=True, key="tab2_bar_chart")

    # 핵심 인사이트 (2, 2 배열)
    st.markdown("<h5 style='font-size:15px; font-weight:700; color:#1E293B; margin:16px 0 10px 0;'>💡 3대 분석 핵심 인사이트 (연평균 증감률 CAGR)</h5>", unsafe_allow_html=True)
    
    ins2_col1, ins2_col2 = st.columns(2)
    with ins2_col1:
        st.markdown(
            """
            <div class="insight-card">
                <div class="insight-title">💡 울산광역시 고령화 속도 1위</div>
                <div class="insight-desc">울산은 2015년 8.79%에서 2024년 17.19%로 연평균 7.74%의 가장 가파른 고령화율 증가세를 기록했습니다.</div>
            </div>
            <div class="insight-card">
                <div class="insight-title">💡 광역시 단위 대도시권 급속 진행</div>
                <div class="insight-desc">인천(5.74%), 대전(5.74%), 대구(5.66%), 부산(5.59%) 등 대도시권 청년층 유출 및 고령화 진행 속도가 최상위권입니다.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with ins2_col2:
        st.markdown(
            """
            <div class="insight-card">
                <div class="insight-title">💡 기저효과에 따른 상승률 차이</div>
                <div class="insight-desc">전남, 경북 등 기존 고령화율이 높았던 지역은 분모 효과로 CAGR 수치는 상대적으로 낮으나 절대 고령 인구 비중은 최고 수준입니다.</div>
            </div>
            <div class="insight-card">
                <div class="insight-title">💡 맞춤형 의료 인프라 공급 시급성</div>
                <div class="insight-desc">고령화 CAGR이 높은 광역시 지역일수록 향후 5~10년 내 노인 전문 의료 및 만성질환 인프라 수요가 폭증할 것으로 예측됩니다.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ── TAB 3: (3) 지역별 고령화 위험/취약 순위 ──────────────────────────────────
with tab3:
    t3_head_col, t3_select_col = st.columns([3, 1])
    with t3_head_col:
        st.markdown("<h4 style='font-size:16px; font-weight:700; color:#1E293B; margin-top:8px;'>지역별 고령화 위험/취약 순위 및 고령화율 분포</h4>", unsafe_allow_html=True)
    with t3_select_col:
        t3_selected_year = st.selectbox(
            "조회 연도 선택",
            options=years_list,
            index=len(years_list) - 1,
            key="tab3_year_select"
        )

    t3_df = df_risk[df_risk['연도'] == t3_selected_year].sort_values(by='위험순위', ascending=True)

    # 막대 차트
    fig_t3 = px.bar(
        t3_df,
        x='시도',
        y='고령화율 (%)',
        color='고령화율 (%)',
        color_continuous_scale='Reds',
        text='고령화율 (%)'
    )
    fig_t3.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig_t3.add_hline(y=20.0, line_dash="dash", line_color="#E5484D", annotation_text="초고령사회 (20%)")
    fig_t3.update_layout(
        title="",
        xaxis_title="시도",
        yaxis_title="고령화율 (%)",
        height=380,
        margin=dict(l=20, r=20, t=10, b=20)
    )
    st.plotly_chart(fig_t3, use_container_width=True, key="tab3_bar_chart")

    # 상세 데이터 테이블
    st.markdown("<h5 style='font-size:14px; font-weight:700; color:#1E293B; margin-top:12px;'>📋 고령화 위험 순위 상세 데이터표</h5>", unsafe_allow_html=True)
    st.dataframe(
        t3_df[['위험순위', '시도', '고령화율 (%)', '고령화 단계', '총인구 (명)', '65세이상 인구 (명)', '전년대비_증감(%p)']],
        hide_index=True,
        use_container_width=True,
        key="tab3_dataframe"
    )

    # 핵심 인사이트 (2, 2 배열)
    st.markdown("<h5 style='font-size:15px; font-weight:700; color:#1E293B; margin:16px 0 10px 0;'>💡 3대 분석 핵심 인사이트 (고령화 위험/취약 순위)</h5>", unsafe_allow_html=True)
    
    ins3_col1, ins3_col2 = st.columns(2)
    with ins3_col1:
        st.markdown(
            """
            <div class="insight-card">
                <div class="insight-title">💡 전남·경북·강원 최상위 고령화 위험군</div>
                <div class="insight-desc">전라남도, 경상북도, 강원특별자치도는 매년 고령화 위험 순위 TOP 3를 차지하며 대표적인 의료 취약 지역으로 나타납니다.</div>
            </div>
            <div class="insight-card">
                <div class="insight-title">💡 대도시 광역시 중 부산 최초 진입</div>
                <div class="insight-desc">부산광역시가 7대 광역시 중 최초로 2021년 초고령사회에 진입한 후, 대구와 경남 역시 초고령사회로 빠르게 이전하였습니다.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with ins3_col2:
        st.markdown(
            """
            <div class="insight-card">
                <div class="insight-title">💡 연간 고령화율 동반 증가 경향</div>
                <div class="insight-desc">17개 시도 전체의 고령화율이 매년 +0.8%p ~ +1.3%p 수준으로 전 지역에서 고령화가 일제히 심화되고 있습니다.</div>
            </div>
            <div class="insight-card">
                <div class="insight-title">💡 지역 맞춤형 의료 자원 배분 필요</div>
                <div class="insight-desc">고령화 위험 1~5위 지역을 거점으로 응급이송 체계 및 거점 요양 병상을 우선 배치하는 정책적 지원이 시급합니다.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# 하단 푸터 안내
st.markdown("---")
st.markdown("<div style='text-align:center; color:#94A3B8; font-size:12px;'>지역 의료 인프라 균형 분석 시스템 | 고령화율 분석 모듈 (2015-2024 Raw Data 연동)</div>", unsafe_allow_html=True)
