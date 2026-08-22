import streamlit as st
import pandas as pd
import json
import os
import sys
import plotly.express as px
import plotly.graph_objects as go

# 프로젝트 루트 및 app 경로를 sys.path에 주입하여 모듈 경로 검색 보장
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

for path in [project_root, app_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

from utils.style import inject_base_style
from utils.nav import render_sidebar

# [1. 데이터 연동 구조 (모듈화)]
# 백엔드 분석 모듈에서 실제로 필요한 파이프라인 함수만 임포트
from src.aging.analysis.infra_balance import run_all_pipeline

# 시도 표준 명칭 매핑용 사전 정의 (백엔드와 동기화)
SIDO_MAP = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도"
}

def clean_sido(sido_str):
    """
    시도 명칭을 표준 명칭(예: '서울특별시')으로 통일합니다.
    ImportError 방지를 위해 프론트엔드 파일 내부에서 자체 정의하여 사용합니다.
    """
    if not isinstance(sido_str, str):
        return None
    s = sido_str.strip()
    s_base = s.split()[0]  # 영문 병기 제거 ('서울 Seoul' -> '서울')
    
    for k, v in SIDO_MAP.items():
        if k in s_base:
            return v
    return s_base

st.set_page_config(page_title="고령화와 노인의료 분석", page_icon="👵", layout="wide")

# 기본 스타일 및 사이드바 렌더링
inject_base_style()
render_sidebar(active_key="aging_jy")

# 데이터 캐시 로딩 함수 구현
@st.cache_data
def load_analysis_data():
    """
    백엔드 분석 결과 데이터를 로드합니다.
    분석 결과 파일이 없을 경우 백엔드 파이프라인을 일괄 기동한 후 로드합니다.
    """
    result_paths = {
        "trend": "data/aging/result/1_national_yearly_supply_trend_result.csv",
        "normalized": "data/aging/result/2_regional_yearly_minmax_normalized_result.csv",
        "cagr": "data/aging/result/3_regional_10yr_cagr_analysis_result.csv"
    }
    
    # 결과 파일이 없으면 백엔드 파이프라인 작동
    if not all(os.path.exists(path) for path in result_paths.values()):
        run_all_pipeline()
        
    df_trend = pd.read_csv(result_paths["trend"])
    df_normalized = pd.read_csv(result_paths["normalized"])
    df_cagr = pd.read_csv(result_paths["cagr"])
    
    return df_trend, df_normalized, df_cagr

# GeoJSON 캐시 로딩 및 시도명 정제 적용
@st.cache_data
def load_geojson_data():
    """
    행정구역 경계 GeoJSON 데이터를 로딩하고 시도명을 표준형으로 정제합니다.
    """
    geojson_path = "data/aging/raw/TL_SCCO_CTPRVN.json"
    with open(geojson_path, encoding="utf-8") as f:
        geo = json.load(f)
    
    # GeoJSON 내의 시도명 정제 (로컬 clean_sido 함수 사용)
    for feature in geo["features"]:
        raw_name = feature["properties"]["CTP_KOR_NM"]
        feature["properties"]["CTP_KOR_NM"] = clean_sido(raw_name)
        
    return geo

# KPI 렌더링을 위한 개별 카드 컴포넌트
def render_kpi_card(title, value, subtext, icon="🏢"):
    st.markdown(
        f"""
        <div class="kpi-card" style="padding: 18px; border-radius: 8px; border: 1px solid #E2E8F0; background-color: white; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 13px; color: #64748B; font-weight: 600;">{title}</span>
                <span style="font-size: 20px;">{icon}</span>
            </div>
            <div style="font-size: 22px; font-weight: 700; color: #1E293B; margin-bottom: 6px;">{value}</div>
            <div style="font-size: 12px; color: #475569; font-weight: 500; background-color: #F1F5F9; padding: 4px 8px; border-radius: 4px; display: inline-block;">
                {subtext}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# 데이터 로딩
try:
    df_trend, df_normalized, df_cagr = load_analysis_data()
    geojson_data = load_geojson_data()
except Exception as e:
    st.error(f"데이터 로드 중 오류 발생: {e}")
    st.stop()

# ── 타이틀 ────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">고령 의료 및 복지 인프라 현황</div>', unsafe_allow_html=True)
st.markdown(
    "지역별 노인복지시설과 요양병원의 수급 현황을 정밀 비교 분석하여 공급 불균형 상태를 진단합니다. "
    ,unsafe_allow_html=True
)

st.write("")

# ── [2. 상단 KPI 카드 4개 (선택 연도 동적 반영)] ────────────────────────────────
# 조회 연도 선택 컨트롤러 배치 (기본값: 2024년)
available_years = sorted(list(df_normalized["연도"].unique()), reverse=True)
selected_year = st.selectbox(
    "📅 분석 조회 연도 선택 (KPI 및 중단 지도 연동)",
    options=available_years,
    index=available_years.index(2024) if 2024 in available_years else 0
)

# 선택된 연도의 데이터 필터링
df_year = df_normalized[df_normalized["연도"] == selected_year].copy()

# KPI 데이터 산출
# 1) 의료 우세 지역: 인프라 치우침 지수가 가장 낮은(음수로 큰) 지역
med_dom_row = df_year.loc[df_year["인프라_치우침_지수"].idxmin()]
med_dom_region = med_dom_row["시도"]
med_dom_count = med_dom_row["요양병원_수"]
med_other_avg = df_year[df_year["시도"] != med_dom_region]["요양병원_수"].mean()
med_ratio = (med_dom_count / med_other_avg * 100) if med_other_avg > 0 else 100.0

# 2) 복지 우세 지역: 인프라 치우침 지수가 가장 높은(양수로 큰) 지역
wel_dom_row = df_year.loc[df_year["인프라_치우침_지수"].idxmax()]
wel_dom_region = wel_dom_row["시도"]
wel_dom_count = wel_dom_row["복지시설_합계"]
wel_other_avg = df_year[df_year["시도"] != wel_dom_region]["복지시설_합계"].mean()
wel_ratio = (wel_dom_count / wel_other_avg * 100) if wel_other_avg > 0 else 100.0

# 3) 10년 의료시설 성장형 추이: 요양병원 10년 CAGR 성장률 최고 지역
cagr_max_row = df_cagr.loc[df_cagr["요양병원_CAGR(%)"].idxmax()]
cagr_max_region = cagr_max_row["시도"]
cagr_max_val = cagr_max_row["요양병원_CAGR(%)"]

# 4) 10년 의료시설 감소형 추이: 요양병원 10년 CAGR 성장률 최저 지역
cagr_min_row = df_cagr.loc[df_cagr["요양병원_CAGR(%)"].idxmin()]
cagr_min_region = cagr_min_row["시도"]
cagr_min_val = cagr_min_row["요양병원_CAGR(%)"]

# KPI 레이아웃 배치
kpi_cols = st.columns(4)
with kpi_cols[0]:
    render_kpi_card(
        title="의료 우세 지역",
        value=f"{med_dom_region}",
        subtext=f"시설 수: {med_dom_count}개 (평균 대비 {med_ratio:.1f}%)",
        icon="🏥"
    )
with kpi_cols[1]:
    render_kpi_card(
        title="복지 우세 지역",
        value=f"{wel_dom_region}",
        subtext=f"시설 수: {wel_dom_count:,}개 (평균 대비 {wel_ratio:.1f}%)",
        icon="👵"
    )
with kpi_cols[2]:
    render_kpi_card(
        title="10년 의료시설 최고성장 지역",
        value=f"{cagr_max_region}",
        subtext=f"성장형 (증감률: +{cagr_max_val:.2f}%)",
        icon="📈"
    )
with kpi_cols[3]:
    render_kpi_card(
        title="10년 의료시설 최저성장 지역",
        value=f"{cagr_min_region}",
        subtext=f"감소/정체형 (증감률: {cagr_min_val:.2f}%)",
        icon="📉"
    )

st.write("")

# ── [3. 중단: 지도 시각화 + 탭별 TOP 3 데이터프레임] ───────────────────────────
st.markdown("###  전국 노인 인프라 공급 공간 분포 분석")

# 탭을 먼저 최상위에 두어 클릭에 의해 아래의 지도와 표가 동시 갱신되도록 탭별 칼럼 구성
tab_med, tab_wel, tab_bal = st.tabs(["의료현황 분석", "복지현황 분석", "균형현황 분석"])

# 1) 의료현황 분석 탭
with tab_med:
    col_map, col_tbl = st.columns([2, 1])
    with col_map:
        with st.container(border=True):
            # 의료시설 단계구분도 (파란색 계열)
            fig_med = px.choropleth(
                df_year,
                geojson=geojson_data,
                locations="시도",
                featureidkey="properties.CTP_KOR_NM",
                color="요양병원_수",
                color_continuous_scale="Blues",
                labels={"요양병원_수": "요양병원 수"},
                title=f"📍 {selected_year}년 시도별 요양병원 공급 분포"
            )
            fig_med.update_geos(fitbounds="locations", visible=False)
            fig_med.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=450)
            st.plotly_chart(fig_med, use_container_width=True)
            
    with col_tbl:
        with st.container(border=True):
            st.markdown(f"##### 🏥 {selected_year}년 요양병원 공급 TOP 3")
            df_med_top3 = df_year[["시도", "요양병원_수"]].sort_values("요양병원_수", ascending=False).head(3).reset_index(drop=True)
            df_med_top3.index += 1
            st.dataframe(df_med_top3, use_container_width=True)
            st.caption("요양병원 수가 많은 상위 3개 시도입니다. 경기도와 대도시권 중심으로 공급량이 쏠려있음을 나타냅니다.")

# 2) 복지현황 분석 탭
with tab_wel:
    col_map, col_tbl = st.columns([2, 1])
    with col_map:
        with st.container(border=True):
            # 복지시설 단계구분도 (주황색 계열)
            fig_wel = px.choropleth(
                df_year,
                geojson=geojson_data,
                locations="시도",
                featureidkey="properties.CTP_KOR_NM",
                color="복지시설_합계",
                color_continuous_scale="Oranges",
                labels={"복지시설_합계": "복지시설 수"},
                title=f"📍 {selected_year}년 시도별 복지시설 공급 분포"
            )
            fig_wel.update_geos(fitbounds="locations", visible=False)
            fig_wel.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=450)
            st.plotly_chart(fig_wel, use_container_width=True)
            
    with col_tbl:
        with st.container(border=True):
            st.markdown(f"##### 👵 {selected_year}년 노인복지시설 공급 TOP 3")
            df_wel_top3 = df_year[["시도", "복지시설_합계"]].sort_values("복지시설_합계", ascending=False).head(3).reset_index(drop=True)
            df_wel_top3.index += 1
            st.dataframe(df_wel_top3, use_container_width=True)
            st.caption("노인복지시설(경로당, 복지관 등)이 풍부하게 설치된 상위 3개 시도입니다. 주로 농어촌 비율이 높고 면적이 넓은 지자체가 우세합니다.")

# 3) 균형현황 분석 탭
with tab_bal:
    col_map, col_tbl = st.columns([2, 1])
    with col_map:
        with st.container(border=True):
            # 균형도 단계구분도 (절대 치우침 지수 기준: 0일 때 초록, 클수록 주황->빨강)
            df_year["절대_치우침_지수"] = df_year["인프라_치우침_지수"].abs()
            color_scale_bal = ["#2E7D32", "#FFA000", "#D32F2F"] # 초록 -> 주황 -> 빨강
            
            fig_bal = px.choropleth(
                df_year,
                geojson=geojson_data,
                locations="시도",
                featureidkey="properties.CTP_KOR_NM",
                color="절대_치우침_지수",
                color_continuous_scale=color_scale_bal,
                range_color=[0, max(df_year["절대_치우침_지수"].max(), 0.5)],
                labels={"절대_치우침_지수": "불균형 지수"},
                title=f"📍 {selected_year}년 시도별 의료-복지 인프라 불균형 분포"
            )
            fig_bal.update_geos(fitbounds="locations", visible=False)
            fig_bal.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=450)
            st.plotly_chart(fig_bal, use_container_width=True)
            
    with col_tbl:
        with st.container(border=True):
            st.markdown(f"##### ⚖️ {selected_year}년 인프라 균형성 우수 TOP 3")
            # 균형성은 절대 치우침 지수가 0에 가장 가까운 순서
            df_bal_top3 = df_year[["시도", "절대_치우침_지수", "인프라_치우침_지수"]].sort_values("절대_치우침_지수", ascending=True).head(3).reset_index(drop=True)
            df_bal_top3.index += 1
            # 보여줄 때는 깔끔하게 변수 선택
            st.dataframe(df_bal_top3[["시도", "인프라_치우침_지수"]], use_container_width=True)
            st.caption("인프라 치우침 지수가 0에 근접한 수급 균형 최우수 지자체입니다. 의료와 복지 자원이 비교적 고르게 분배되어 있음을 뜻합니다.")

st.write("")

# ── [4. 하단: 상세 데이터 항목 3대 분석 섹션] ──────────────────────────────
st.markdown("###  인프라 비교 상세 분석")

# ──────────────────────────────────────────────────────────────────────
# 섹션 1: 지역/지역별 인프라 상대적 비율 비교 (Min-Max 정규화 막대그래프)
# ──────────────────────────────────────────────────────────────────────
st.markdown("#### 1️. 지역별 정규화 인프라 비율 비교")
# 연도 선택 1개 토글 (라디오 버튼)
s1_years = sorted(list(df_normalized["연도"].unique()))
selected_year_s1 = st.radio(
    "📅 섹션 1 분석 대상 연도 선택",
    options=s1_years,
    index=len(s1_years)-1,
    horizontal=True,
    key="radio_s1"
)

# 데이터 필터링
df_s1 = df_normalized[df_normalized["연도"] == selected_year_s1].copy()

# 막대그래프 독립 카드 구성
with st.container(border=True):
    fig_s1 = px.bar(
        df_s1,
        x="시도",
        y=["복지시설_정규화", "요양병원_정규화"],
        barmode="group",
        color_discrete_sequence=["#F2994A", "#2F6FED"], # 복지 주황, 의료 파랑
        labels={"value": "정규화 점수 (Min-Max)", "variable": "지표 구분"},
        title=f" {selected_year_s1}년 시도별 복지 vs 의료 정규화 인프라 비율 (0~1 범위 비교)"
    )
    fig_s1.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_s1, use_container_width=True)

# 하단에 표 데이터를 columns로 분리하여 독립 상자로 각각 배치
col_med_rank, col_wel_rank = st.columns(2)

with col_med_rank:
    with st.container(border=True):
        st.markdown(f"##### 🏥 {selected_year_s1}년 의료시설(요양병원) 보유 순위")
        df_med_rank = df_s1[["시도", "요양병원_수"]].sort_values("요양병원_수", ascending=False).reset_index(drop=True)
        df_med_rank.index += 1
        st.dataframe(df_med_rank, use_container_width=True)

with col_wel_rank:
    with st.container(border=True):
        st.markdown(f"##### 👴 {selected_year_s1}년 복지시설 보유 순위")
        df_wel_rank = df_s1[["시도", "복지시설_합계"]].sort_values("복지시설_합계", ascending=False).reset_index(drop=True)
        df_wel_rank.index += 1
        st.dataframe(df_wel_rank, use_container_width=True)

st.write("")

# ──────────────────────────────────────────────────────────────────────
# 섹션 2: 지역/연도별 복지시설 vs 요양병원 공급 추이 산점도
# ──────────────────────────────────────────────────────────────────────
st.markdown("#### 2️. 복지시설 vs 요양병원 공급 추이 산점도")
# 가로형 도트(버튼 라디오) 형태 단일 연도 선택
selected_year_s2 = st.radio(
    "📅 섹션 2 분석 대상 연도 선택",
    options=s1_years,
    index=len(s1_years)-1,
    horizontal=True,
    key="radio_s2"
)

# 데이터 필터링
df_s2 = df_normalized[df_normalized["연도"] == selected_year_s2].copy()

col_s2_scatter, col_s2_table = st.columns([2, 1])

with col_s2_scatter:
    with st.container(border=True):
        fig_s2 = px.scatter(
            df_s2,
            x="복지시설_합계",
            y="요양병원_수",
            text="시도",
            size="복지시설_합계",
            color="인프라_치우침_지수",
            color_continuous_scale="RdYlBu_r", # 복지치우침(양수)은 빨강/주황, 의료치우침(음수)은 파랑
            labels={"복지시설_합계": "노인복지시설 수 (개)", "요양병원_수": "요양병원 수 (개)"},
            title=f" {selected_year_s2}년 노인복지시설 vs 요양병원 상관 관계 및 치우침 현황"
        )
        fig_s2.update_traces(textposition='top center', marker=dict(line=dict(width=1, color="grey")))
        fig_s2.update_layout(height=400, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_s2, use_container_width=True)

with col_s2_table:
    with st.container(border=True):
        st.markdown(f"#####  {selected_year_s2}년 복지-의료시설 원본 데이터")
        df_s2_tbl = df_s2[["시도", "복지시설_합계", "요양병원_수"]].sort_values("복지시설_합계", ascending=False).reset_index(drop=True)
        st.dataframe(df_s2_tbl, use_container_width=True, hide_index=True, height=350)

st.write("")

# ──────────────────────────────────────────────────────────────────────
# 섹션 3: 지역별 의료시설과 복지시설의 연평균 증감률(CAGR) 변화 패턴 종합분석
# ──────────────────────────────────────────────────────────────────────
st.markdown("#### 3️. 연도 구간별 복지/의료시설 CAGR 동적 변화 분석")

# 연도 구간 슬라이더 배치
min_year = int(df_normalized["연도"].min())
max_year = int(df_normalized["연도"].max())
start_year, end_year = st.slider(
    "📆 CAGR 분석 연도 구간 슬라이더 설정",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# 동적 CAGR 연산 처리
period = end_year - start_year

df_start = df_normalized[df_normalized["연도"] == start_year][["시도", "복지시설_합계", "요양병원_수"]]
df_end = df_normalized[df_normalized["연도"] == end_year][["시도", "복지시설_합계", "요양병원_수"]]

df_dyn_cagr = pd.merge(df_start, df_end, on="시도", suffixes=("_start", "_end"))

def calculate_dynamic_cagr(start_val, end_val, p):
    if p <= 0 or start_val <= 0 or end_val <= 0:
        return 0.0
    return (((end_val / start_val) ** (1 / p)) - 1) * 100

df_dyn_cagr["복지시설_CAGR(%)"] = df_dyn_cagr.apply(
    lambda r: calculate_dynamic_cagr(r["복지시설_합계_start"], r["복지시설_합계_end"], period), axis=1
).round(2)

df_dyn_cagr["요양병원_CAGR(%)"] = df_dyn_cagr.apply(
    lambda r: calculate_dynamic_cagr(r["요양병원_수_start"], r["요양병원_수_end"], period), axis=1
).round(2)

col_s3_chart, col_s3_table = st.columns([2, 1])

with col_s3_chart:
    with st.container(border=True):
        if period == 0:
            st.warning("⚠️ 시작 연도와 종료 연도가 동일하여 CAGR을 계산할 수 없습니다. 구간을 조절해 주세요.")
        else:
            fig_s3 = px.bar(
                df_dyn_cagr,
                x="시도",
                y=["복지시설_CAGR(%)", "요양병원_CAGR(%)"],
                barmode="group",
                color_discrete_sequence=["#F2994A", "#2F6FED"], # 복지 주황, 의료 파랑
                labels={"value": "연평균 증감률 CAGR (%)", "variable": "시설 구분"},
                title=f" {start_year}년 ~ {end_year}년 ({period}개년) 시도별 인프라 연평균 증감률(CAGR)"
            )
            fig_s3.update_layout(height=400, margin=dict(l=10, r=10, t=40, b=10), xaxis_tickangle=-45)
            st.plotly_chart(fig_s3, use_container_width=True)

with col_s3_table:
    with st.container(border=True):
        st.markdown(f"#####  {start_year}년 ~ {end_year}년 CAGR 수치 데이터표")
        df_dyn_cagr_tbl = df_dyn_cagr[["시도", "복지시설_CAGR(%)", "요양병원_CAGR(%)"]].sort_values("복지시설_CAGR(%)", ascending=False).reset_index(drop=True)
        st.dataframe(df_dyn_cagr_tbl, use_container_width=True, hide_index=True, height=350)
