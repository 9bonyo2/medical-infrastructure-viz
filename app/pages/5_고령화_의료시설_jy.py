import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import json
import os
import sys
import plotly.express as px
import plotly.graph_objects as go
import folium

# 프로젝트 루트 및 app 경로를 sys.path에 주입하여 모듈 경로 검색 보장
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

for path in [project_root, app_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

from utils.style import inject_base_style
from utils.nav import render_sidebar
from src.aging.analysis.infra_balance import run_all_pipeline

# 시도 표준 명칭 매핑용 사전 정의
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
    if not isinstance(sido_str, str):
        return None
    s = sido_str.strip()
    s_base = s.split()[0]
    for k, v in SIDO_MAP.items():
        if k in s_base:
            return v
    return s_base

st.set_page_config(page_title="고령 복지·의료 인프라 분석", page_icon="👵", layout="wide")

# 기본 스타일 및 사이드바 렌더링
inject_base_style()
render_sidebar(active_key="aging_jy")

# 데이터 캐시 로딩 함수
@st.cache_data
def load_analysis_data():
    result_paths = {
        "trend": "data/aging/result/1_national_yearly_supply_trend_result.csv",
        "normalized": "data/aging/result/2_regional_yearly_minmax_normalized_result.csv",
        "cagr": "data/aging/result/3_regional_10yr_cagr_analysis_result.csv"
    }
    if not all(os.path.exists(path) for path in result_paths.values()):
        run_all_pipeline()
        
    df_trend = pd.read_csv(result_paths["trend"])
    df_normalized = pd.read_csv(result_paths["normalized"])
    df_cagr = pd.read_csv(result_paths["cagr"])
    
    return df_trend, df_normalized, df_cagr

@st.cache_data
def load_geojson_data():
    geojson_path = "data/aging/raw/TL_SCCO_CTPRVN.json"
    with open(geojson_path, encoding="utf-8") as f:
        geo = json.load(f)
    for feature in geo["features"]:
        raw_name = feature["properties"]["CTP_KOR_NM"]
        feature["properties"]["CTP_KOR_NM"] = clean_sido(raw_name)
    return geo

# 데이터 로딩
try:
    df_trend, df_normalized, df_cagr = load_analysis_data()
    geojson_data = load_geojson_data()
except Exception as e:
    st.error(f"데이터 로드 중 오류 발생: {e}")
    st.stop()

# KPI 렌더링 개별 카드 컴포넌트
def render_kpi_card(title, value, subtext, icon="🏢", trend="up"):
    color = "#22A06B" if trend == "up" else "#E5484D" if trend == "down" else "#64748B"
    st.markdown(
        f"""
        <div class="kpi-card" style="padding: 18px; border-radius: 14px; border: 1px solid #E7E9EE; background-color: white; box-shadow: 0 1px 2px rgba(16,24,40,0.04); height: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 13px; color: #6B7280; font-weight: 600;">{title}</span>
                <span style="font-size: 20px;">{icon}</span>
            </div>
            <div style="font-size: 24px; font-weight: 700; color: #1A1F2B; margin-bottom: 6px;">{value}</div>
            <div style="font-size: 12px; color: {color}; font-weight: 600; background-color: #F8FAFC; padding: 4px 8px; border-radius: 4px; display: inline-block;">
                {subtext}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ── [1. 상단 섹션] ───────────────────────────────────────────────────
title_col, year_col = st.columns([3, 1])
with title_col:
    st.markdown('<div class="page-title" style="margin-bottom: 2px;">고령 복지·의료 인프라 분석</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle" style="margin-bottom: 20px;">지역별 노인복지시설과 요양병원의 수급 현황을 정밀 비교 분석하여 공급 불균형 상태를 진단합니다.</div>', unsafe_allow_html=True)

with year_col:
    available_years = sorted(list(df_normalized["연도"].unique()), reverse=True)
    selected_year = st.selectbox(
        "기준 연도",
        options=available_years,
        index=available_years.index(2024) if 2024 in available_years else 0,
        key="main_selected_year"
    )

# 선택된 연도의 데이터 필터링
df_year = df_normalized[df_normalized["연도"] == selected_year].copy()

# KPI 데이터 산출
# 1) 의료 우세 지역
med_dom_row = df_year.loc[df_year["인프라_치우침_지수"].idxmin()]
med_dom_region = med_dom_row["시도"]
med_dom_count = med_dom_row["요양병원_수"]
med_other_avg = df_year[df_year["시도"] != med_dom_region]["요양병원_수"].mean()
med_ratio = (med_dom_count / med_other_avg * 100) if med_other_avg > 0 else 100.0

# 2) 복지 우세 지역
wel_dom_row = df_year.loc[df_year["인프라_치우침_지수"].idxmax()]
wel_dom_region = wel_dom_row["시도"]
wel_dom_count = wel_dom_row["복지시설_합계"]
wel_other_avg = df_year[df_year["시도"] != wel_dom_region]["복지시설_합계"].mean()
wel_ratio = (wel_dom_count / wel_other_avg * 100) if wel_other_avg > 0 else 100.0

# 3) 10년 의료시설 성장형 추이
cagr_max_row = df_cagr.loc[df_cagr["요양병원_CAGR(%)"].idxmax()]
cagr_max_region = cagr_max_row["시도"]
cagr_max_val = cagr_max_row["요양병원_CAGR(%)"]

# 4) 10년 의료시설 감소형 추이
cagr_min_row = df_cagr.loc[df_cagr["요양병원_CAGR(%)"].idxmin()]
cagr_min_region = cagr_min_row["시도"]
cagr_min_val = cagr_min_row["요양병원_CAGR(%)"]

# KPI 카드 출력
kpi_cols = st.columns(4)
with kpi_cols[0]:
    render_kpi_card(
        title="의료 우세 지역",
        value=f"{med_dom_region}",
        subtext=f"시설 수: {med_dom_count}개 (평균 대비 {med_ratio:.1f}%)",
        icon="🏥",
        trend="up"
    )
with kpi_cols[1]:
    render_kpi_card(
        title="복지 우세 지역",
        value=f"{wel_dom_region}",
        subtext=f"시설 수: {wel_dom_count:,}개 (평균 대비 {wel_ratio:.1f}%)",
        icon="👵",
        trend="up"
    )
with kpi_cols[2]:
    render_kpi_card(
        title="10년 의료시설 최고성장 지역",
        value=f"{cagr_max_region}",
        subtext=f"성장형 (CAGR: +{cagr_max_val:.2f}%)",
        icon="📈",
        trend="up"
    )
with kpi_cols[3]:
    render_kpi_card(
        title="10년 의료시설 최저성장 지역",
        value=f"{cagr_min_region}",
        subtext=f"감소/정체형 (CAGR: {cagr_min_val:.2f}%)",
        icon="📉",
        trend="down"
    )

st.write("")

# ── [2. 중단 섹션 - 지도 시각화 및 TOP 3 / BOTTOM 3 요약 표] ─────────────
st.markdown("###  지역별 고령 복지·의료 인프라 공급 현황")

# 최상위 탭 구성
tab_med, tab_wel, tab_bal = st.tabs(["의료현황", "복지현황", "균형현황"])

# Folium 지도 그리는 헬퍼 함수
def draw_folium_map(df, geo_data, fill_column, fill_color, legend_label):
    m = folium.Map(
        location=[36.3, 127.8],
        zoom_start=6.5,
        tiles="CartoDB positron",
        zoom_control=False,
        scrollWheelZoom=False,
        dragging=True
    )
    
    folium.Choropleth(
        geo_data=geo_data,
        name="choropleth",
        data=df,
        columns=["시도", fill_column],
        key_on="feature.properties.CTP_KOR_NM",
        fill_color=fill_color,
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name=legend_label,
        highlight=True,
    ).add_to(m)
    
    st_folium(m, height=450, use_container_width=True, returned_objects=[])

# 1) 의료현황 탭
with tab_med:
    col_map, col_tbl = st.columns([2, 1])
    with col_map:
        with st.container(border=True):
            st.markdown('<div class="panel-title" style="margin-bottom:10px;"> 지역별 요양병원 공급 분포</div>', unsafe_allow_html=True)
            draw_folium_map(df_year, geojson_data, "요양병원_수", "Blues", "요양병원 수")
            
    with col_tbl:
        # 상단 상위 TOP 3
        with st.container(border=True):
            st.markdown(f" **{selected_year}년 요양병원 공급 상위 TOP 3**")
            df_med_top3 = df_year[["시도", "요양병원_수"]].sort_values("요양병원_수", ascending=False).head(3).reset_index(drop=True)
            df_med_top3.index += 1
            st.dataframe(df_med_top3, use_container_width=True)
            
        # 하단 하위 BOTTOM 3
        with st.container(border=True):
            st.markdown(f" **{selected_year}년 요양병원 공급 하위 TOP 3**")
            df_med_bottom3 = df_year[["시도", "요양병원_수"]].sort_values("요양병원_수", ascending=True).head(3).reset_index(drop=True)
            df_med_bottom3.index += 1
            st.dataframe(df_med_bottom3, use_container_width=True)

# 2) 복지현황 탭
with tab_wel:
    col_map, col_tbl = st.columns([2, 1])
    with col_map:
        with st.container(border=True):
            st.markdown('<div class="panel-title" style="margin-bottom:10px;">지역별 복지시설 공급 분포</div>', unsafe_allow_html=True)
            draw_folium_map(df_year, geojson_data, "복지시설_합계", "Oranges", "복지시설 수")
            
    with col_tbl:
        # 상단 상위 TOP 3
        with st.container(border=True):
            st.markdown(f" **{selected_year}년 노인복지시설 공급 상위 TOP 3**")
            df_wel_top3 = df_year[["시도", "복지시설_합계"]].sort_values("복지시설_합계", ascending=False).head(3).reset_index(drop=True)
            df_wel_top3.index += 1
            st.dataframe(df_wel_top3, use_container_width=True)
            
        # 하단 하위 BOTTOM 3
        with st.container(border=True):
            st.markdown(f" **{selected_year}년 노인복지시설 공급 하위 TOP 3**")
            df_wel_bottom3 = df_year[["시도", "복지시설_합계"]].sort_values("복지시설_합계", ascending=True).head(3).reset_index(drop=True)
            df_wel_bottom3.index += 1
            st.dataframe(df_wel_bottom3, use_container_width=True)

# 3) 균형현황 탭
with tab_bal:
    col_map, col_tbl = st.columns([2, 1])
    with col_map:
        with st.container(border=True):
            st.markdown('<div class="panel-title" style="margin-bottom:10px;">지역별 의료-복지 인프라 불균형 분포</div>', unsafe_allow_html=True)
            df_year["절대_치우침_지수"] = df_year["인프라_치우침_지수"].abs()
            draw_folium_map(df_year, geojson_data, "절대_치우침_지수", "RdYlGn_r", "불균형 지수")
            
    with col_tbl:
        # 상단 균형 우수 TOP 3
        with st.container(border=True):
            st.markdown(f" **{selected_year}년 인프라 균형성 우수 TOP 3**")
            df_bal_top3 = df_year[["시도", "인프라_치우침_지수"]].copy()
            df_bal_top3["절대_치우침_지수"] = df_bal_top3["인프라_치우침_지수"].abs()
            df_bal_top3 = df_bal_top3.sort_values("절대_치우침_지수", ascending=True).head(3).reset_index(drop=True)
            df_bal_top3.index += 1
            st.dataframe(df_bal_top3[["시도", "인프라_치우침_지수"]], use_container_width=True)
            
        # 하단 불균형 심각 BOTTOM 3
        with st.container(border=True):
            st.markdown(f" **{selected_year}년 인프라 불균형 심각 TOP 3**")
            df_bal_bottom3 = df_year[["시도", "인프라_치우침_지수"]].copy()
            df_bal_bottom3["절대_치우침_지수"] = df_bal_bottom3["인프라_치우침_지수"].abs()
            df_bal_bottom3 = df_bal_bottom3.sort_values("절대_치우침_지수", ascending=False).head(3).reset_index(drop=True)
            df_bal_bottom3.index += 1
            st.dataframe(df_bal_bottom3[["시도", "인프라_치우침_지수"]], use_container_width=True)

st.write("")

# ── [3. 하단 섹션 - 상세 데이터 항목 3대 분석] ───────────────────────────
st.markdown("###  상세 분석")

tab_s1, tab_s2, tab_s3 = st.tabs([
    "1. 정규화 비율 비교",
    "2. 복지·의료 산점도",
    "3. CAGR 종합분석"
])

# 핵심 인사이트 렌더링 헬퍼 함수
def render_insight_grid(insights):
    st.write("")
    st.markdown("#####  핵심 인사이트")
    cols = st.columns(2)
    for i, ins in enumerate(insights):
        col_idx = i % 2
        with cols[col_idx]:
            st.markdown(
                f"""
                <div style="border-left: 4px solid #2F6FED; padding: 10px 14px; margin-bottom: 12px; background-color: #F8FAFC; border-radius: 0 8px 8px 0; min-height: 100px;">
                    <div style="font-weight: 700; color: #1E293B; margin-bottom: 4px; font-size: 14px;">💡 {ins['title']}</div>
                    <div style="font-size: 12.5px; color: #475569; line-height: 1.5;">{ins['content']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

# ── 1. 정규화 비율 비교 탭 ───────────────────────────────────────────
with tab_s1:
    col_title, col_sel = st.columns([3, 1])
    with col_title:
        st.markdown("##### 1. 지역별 정규화 인프라 비율 비교")
    with col_sel:
        s1_years = sorted(list(df_normalized["연도"].unique()))
        selected_year_s1 = st.selectbox(
            "기준 연도",
            options=s1_years,
            index=len(s1_years)-1,
            key="selectbox_s1_year"
        )
        
    df_s1 = df_normalized[df_normalized["연도"] == selected_year_s1].copy()
    
    st.markdown(f"**{selected_year_s1}년 시도별 복지 vs 의료 정규화 인프라 비율 (0~1 범위 비교)**")
    with st.container(border=True):
        fig_s1 = px.bar(
            df_s1,
            x="시도",
            y=["복지시설_정규화", "요양병원_정규화"],
            barmode="group",
            color_discrete_sequence=["#F2994A", "#2F6FED"],
            labels={"value": "정규화 점수 (Min-Max)", "variable": "지표 구분"}
        )
        fig_s1.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_s1, use_container_width=True, key="bar_normalized_s1")
        
    col_med_rank, col_wel_rank = st.columns(2)
    with col_med_rank:
        with st.container(border=True):
            st.markdown(f" **{selected_year_s1}년 의료시설(요양병원) 보유 순위**")
            df_med_rank = df_s1[["시도", "요양병원_수"]].sort_values("요양병원_수", ascending=False).reset_index(drop=True)
            df_med_rank.index += 1
            st.dataframe(df_med_rank, use_container_width=True)
            
    with col_wel_rank:
        with st.container(border=True):
            st.markdown(f" **{selected_year_s1}년 복지시설 보유 순위**")
            df_wel_rank = df_s1[["시도", "복지시설_합계"]].sort_values("복지시설_합계", ascending=False).reset_index(drop=True)
            df_wel_rank.index += 1
            st.dataframe(df_wel_rank, use_container_width=True)

    s1_insights = [
        {"title": "대도시권의 의료 인프라 집중", "content": "서울, 부산, 대구 등 대도시 지역은 복지시설 정규화 점수에 비해 요양병원 공급 비율이 매우 극대화되어 있습니다."},
        {"title": "지방 농어촌의 복지 인프라 강세", "content": "전남, 경북 등 도 단위 지역은 넓은 행정 면적과 경로당 등 복지시설이 고르게 퍼져있어 복지 점수가 상대적으로 높습니다."},
        {"title": "지역 인프라 공급 쏠림 심화", "content": "인구 구조 대비 의료와 복지 시설의 편중도가 뚜렷해 고령인구의 실질적인 수요 분포와 연계한 인프라 확보가 요망됩니다."},
        {"title": "취약 지자체의 정책적 지원 필요", "content": "두 부문의 정규화 점수가 동시에 하위권에 머무르는 중소도시의 인프라 공백을 적극적으로 보완해야 합니다."}
    ]
    render_insight_grid(s1_insights)

# ── 2. 복지 vs 요양 산점도 탭 ─────────────────────────────────────────
with tab_s2:
    col_title, col_sel = st.columns([3, 1])
    with col_title:
        st.markdown("##### 2. 복지·의료 공급 추이 산점도")
    with col_sel:
        s2_years = sorted(list(df_normalized["연도"].unique()))
        selected_year_s2 = st.selectbox(
            "기준 연도",
            options=s2_years,
            index=len(s2_years)-1,
            key="selectbox_s2_year"
        )
        
    df_s2 = df_normalized[df_normalized["연도"] == selected_year_s2].copy()
    
    st.markdown(f"**{selected_year_s2}년 복지시설·의료시설 상관 관계 및 치우침 현황**")
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
                color_continuous_scale="RdYlBu_r",
                labels={"복지시설_합계": "노인복지시설 수 (개)", "요양병원_수": "요양병원 수 (개)"}
            )
            fig_s2.update_traces(textposition='top center', marker=dict(line=dict(width=1, color="grey")))
            fig_s2.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_s2, use_container_width=True, key="scatter_s2")
            
    with col_s2_table:
        with st.container(border=True):
            st.markdown(f" **{selected_year_s2}년 복지-의료시설 원본 데이터**")
            df_s2_tbl = df_s2[["시도", "복지시설_합계", "요양병원_수"]].sort_values("복지시설_합계", ascending=False).reset_index(drop=True)
            st.dataframe(df_s2_tbl, use_container_width=True, hide_index=True, height=350)
            
    s2_insights = [
        {"title": "인프라 분포의 불균형성 입증", "content": "산점도의 분포와 인프라 치우침 지수가 확연히 갈려, 특정 지역에서 복지 혹은 의료의 과편향이 관찰됩니다."},
        {"title": "요양병원 과잉 분포 지역", "content": "부산과 대구는 복지시설 총량에 비해 요양병원의 수급 밀도가 조밀하게 치우쳐 있어 과잉 경쟁의 우려가 있습니다."},
        {"title": "복지 서비스 쏠림 현상", "content": "경기도와 전라남도는 시설 규모가 넓게 분포해 있으나, 이와 비교해 급성 노인의료 대응 인프라(요양병원) 비중이 작습니다."},
        {"title": "인프라 최적 매칭을 위한 기준", "content": "본 산점도에 표시된 편차 수준을 인허가 규제 지표로 삼아 적정 공급 수준으로 조율하는 중재 정책이 필요합니다."}
    ]
    render_insight_grid(s2_insights)

# ── 3. 10년 CAGR 종합분석 탭 ───────────────────────────────────────
with tab_s3:
    st.markdown("##### 3. 복지·의료 CAGR 동적 변화 분석")
    
    min_year = int(df_normalized["연도"].min())
    max_year = int(df_normalized["연도"].max())
    start_year, end_year = st.slider(
        "분석 연도 구간",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        key="slider_s3_years"
    )
    
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
    
    st.markdown(f"**{start_year}년 ~ {end_year}년 ({period}개년) 시도별 인프라 연평균 증감률(CAGR)**")
    
    col_s3_chart, col_s3_table = st.columns([2, 1])
    
    with col_s3_chart:
        with st.container(border=True):
            if period <= 0:
                st.warning("⚠️ 시작 연도와 종료 연도가 동일하여 CAGR을 계산할 수 없습니다. 구간을 조절해 주세요.")
            else:
                fig_s3 = px.bar(
                    df_dyn_cagr,
                    x="시도",
                    y=["복지시설_CAGR(%)", "요양병원_CAGR(%)"],
                    barmode="group",
                    color_discrete_sequence=["#F2994A", "#2F6FED"],
                    labels={"value": "연평균 증감률 CAGR (%)", "variable": "시설 구분"}
                )
                fig_s3.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10), xaxis_tickangle=-45)
                st.plotly_chart(fig_s3, use_container_width=True, key="bar_cagr_s3")
                
    with col_s3_table:
        with st.container(border=True):
            st.markdown(f" **{start_year}년 ~ {end_year}년 CAGR 수치 데이터표**")
            df_dyn_cagr_tbl = df_dyn_cagr[["시도", "복지시설_CAGR(%)", "요양병원_CAGR(%)"]].sort_values("복지시설_CAGR(%)", ascending=False).reset_index(drop=True)
            st.dataframe(df_dyn_cagr_tbl, use_container_width=True, hide_index=True, height=350)
            
    s3_insights = [
        {"title": "요양병원 공급 증가 둔화세", "content": "다수의 지방 정부에서 요양병원 연평균 성장률(CAGR)이 음수로 전환되어 시장 포화와 신규 설치 규제 등의 영향이 가시화되고 있습니다."},
        {"title": "복지 인프라의 점진적 성장", "content": "대다수 지자체의 노인복지시설 공급 증가세는 완만하지만 꾸준히 우상향하여 안정적 재정 투입을 시사합니다."},
        {"title": "성장 격차 기반 맞춤 지원", "content": "특정 지역의 요양병원 쏠림 성장이 진정되면서, 정부 보조금 지급 및 설립 인가 방향이 불균형 해소 위주로 전환되고 있습니다."},
        {"title": "고령화 동향 밀접 모니터링", "content": "시설 증가폭이 고령 인구 증가율과 보조를 맞추는지 실시간으로 모니터링해 재원 낭비 및 관리 사각지대를 방지해야 합니다."}
    ]
    render_insight_grid(s3_insights) #─────────────────────────────────────────────────────────────────────