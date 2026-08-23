import os
import sys

# 프로젝트 루트 경로 추가 (app/pages -> medical-infrastructure-viz)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.pediatric.collection import get_geojson
from src.pediatric.correlation import calculate_correlation, create_heatmap_figure
from src.pediatric.preprocess import get_preprocessed_data
from utils.nav import render_sidebar
from utils.style import inject_base_style

# ---------------------------------------------------------
# 1. 페이지 설정 및 공통 스타일 적용
# ---------------------------------------------------------
st.set_page_config(
    page_title="출산율과 소아과 분석 (DY)",
    page_icon="💉",
    layout="wide",
)

inject_base_style()
render_sidebar("pediatric_dy")

plt.rc("font", family="Malgun Gothic")
plt.rc("axes", unicode_minus=False)

# 시도별 위경도 좌표 사전 정의
SIDO_COORDS = {
    "서울특별시": {"lat": 37.5665, "lon": 126.9780},
    "부산광역시": {"lat": 35.1796, "lon": 129.0756},
    "대구광역시": {"lat": 35.8714, "lon": 128.6014},
    "인천광역시": {"lat": 37.4563, "lon": 126.7052},
    "광주광역시": {"lat": 35.1595, "lon": 126.8526},
    "대전광역시": {"lat": 36.3504, "lon": 127.3845},
    "울산광역시": {"lat": 35.5384, "lon": 129.3114},
    "세종특별자치시": {"lat": 36.4800, "lon": 127.2890},
    "경기도": {"lat": 37.4138, "lon": 127.5183},
    "강원특별자치도": {"lat": 37.8228, "lon": 128.1555},
    "강원도": {"lat": 37.8228, "lon": 128.1555},
    "충청북도": {"lat": 36.6357, "lon": 127.4912},
    "충청남도": {"lat": 36.5184, "lon": 126.8000},
    "전북특별자치도": {"lat": 35.7175, "lon": 127.1530},
    "전라북도": {"lat": 35.7175, "lon": 127.1530},
    "전라남도": {"lat": 34.8161, "lon": 126.4629},
    "경상북도": {"lat": 36.5760, "lon": 128.5056},
    "경상남도": {"lat": 35.4606, "lon": 128.2132},
    "제주특별자치도": {"lat": 33.4890, "lon": 126.4983},
}


# ---------------------------------------------------------
# 2. 캐시 데이터 로드 함수
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df = get_preprocessed_data()
    return df[df["연도별"] <= 2024]


@st.cache_data
def load_geo():
    return get_geojson()


try:
    df_data = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 기본 데이터 프레임 (전국 제외)
df_filtered_base = df_data[df_data["시도별"] != "전국"]

# ---------------------------------------------------------
# 3. 커스텀 KPI 카드 컴포넌트 함수
# ---------------------------------------------------------
def render_custom_kpi_card(icon: str, label: str, value: str, unit: str, yoy_html: str):
    html_code = f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.02);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    ">
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 14px; font-weight: 600; color: #64748B;">{label}</span>
                <span style="font-size: 20px;">{icon}</span>
            </div>
            <div style="display: flex; align-items: baseline; gap: 4px; margin-bottom: 8px;">
                <span style="font-size: 28px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px;">{value}</span>
                <span style="font-size: 14px; font-weight: 600; color: #475569;">{unit}</span>
            </div>
        </div>
        <div style="font-size: 13px; font-weight: 600; margin-top: 4px; border-top: 1px solid #F1F5F9; padding-top: 8px;">
            {yoy_html}
        </div>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)


# ---------------------------------------------------------
# 4. 헤더 및 KPI 카드 영역 (1번 요청: 타이틀과 '기준 연도' 셀렉터 한 라인 배치)
# ---------------------------------------------------------
available_years = sorted(df_filtered_base["연도별"].unique(), reverse=True)

if "global_year_select" not in st.session_state:
    st.session_state["global_year_select"] = available_years[0]

# 타이틀 헤더와 기준 연도 셀렉터를 동일 선상에 배치
title_col, select_col = st.columns([8, 2], vertical_alignment="center")

with title_col:
    st.markdown("<h1 style='margin: 0; padding: 0;'>출생아 수 & 소아청소년과 현황 분석</h1>", unsafe_allow_html=True)

with select_col:
    selected_map_year = st.selectbox(
        "기준 연도",
        options=available_years,
        index=available_years.index(st.session_state["global_year_select"]),
        key="global_year_select",
    )

st.caption("출생아 수, 합계출산율 및 소아청소년과 인프라 간의 상관관계와 지역별/연도별 추이를 분석합니다.")
st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

prev_year = selected_map_year - 1

df_curr = df_filtered_base[df_filtered_base["연도별"] == selected_map_year]
df_prev = df_filtered_base[df_filtered_base["연도별"] == prev_year]

curr_births = int(df_curr["출생아수"].sum()) if not df_curr.empty else 0
curr_fertility = df_curr["합계출산율"].mean() if not df_curr.empty else 0.0
curr_pediatrics = df_curr["소아청소년과_기관수"].mean() if not df_curr.empty else 0.0

def format_yoy(diff, pct, unit="", is_float=False):
    if diff > 0:
        val_str = f"+{diff:,.3f}" if is_float else f"+{diff:,}"
        return f'<span style="color: #10B981;">▲ 전년 대비 {val_str}{unit} (+{pct:.1f}%)</span>'
    elif diff < 0:
        val_str = f"{diff:,.3f}" if is_float else f"{diff:,}"
        return f'<span style="color: #EF4444;">▼ 전년 대비 {val_str}{unit} ({pct:.1f}%)</span>'
    else:
        return '<span style="color: #64748B;">- 전년 대비 변동 없음</span>'

if not df_prev.empty:
    prev_births = int(df_prev["출생아수"].sum())
    prev_fertility = df_prev["합계출산율"].mean()
    prev_pediatrics = df_prev["소아청소년과_기관수"].mean()

    diff_b = curr_births - prev_births
    pct_b = (diff_b / prev_births) * 100 if prev_births else 0
    yoy_births_html = format_yoy(diff_b, pct_b, "명")

    diff_f = curr_fertility - prev_fertility
    pct_f = (diff_f / prev_fertility) * 100 if prev_fertility else 0
    yoy_fertility_html = format_yoy(diff_f, pct_f, "명", is_float=True)

    diff_p = curr_pediatrics - prev_pediatrics
    pct_p = (diff_p / prev_pediatrics) * 100 if prev_pediatrics else 0
    yoy_pediatrics_html = format_yoy(round(diff_p, 1), pct_p, "개소", is_float=True)
else:
    yoy_births_html = '<span style="color: #94A3B8;">전년 데이터 없음</span>'
    yoy_fertility_html = '<span style="color: #94A3B8;">전년 데이터 없음</span>'
    yoy_pediatrics_html = '<span style="color: #94A3B8;">전년 데이터 없음</span>'

kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

with kpi_col1:
    render_custom_kpi_card(
        icon="",
        label=f"총 출생아 수 ({selected_map_year}년)",
        value=f"{curr_births:,}",
        unit="명",
        yoy_html=yoy_births_html,
    )

with kpi_col2:
    render_custom_kpi_card(
        icon="",
        label=f"평균 합계출산율 ({selected_map_year}년)",
        value=f"{curr_fertility:.3f}",
        unit="명",
        yoy_html=yoy_fertility_html,
    )

with kpi_col3:
    render_custom_kpi_card(
        icon="",
        label=f"평균 소아청소년과 기관 수 ({selected_map_year}년)",
        value=f"{curr_pediatrics:.1f}",
        unit="개소",
        yoy_html=yoy_pediatrics_html,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. 지도 패널(좌측) + TOP 5 순위 패널(우측) (2번 요청: 외부에 지표 선택 탭 구성)
# ---------------------------------------------------------
METRIC_OPTIONS = {
    "출생아 수": "출생아수",
    "합계출산율": "합계출산율",
    "소아청소년과 기관 수": "소아청소년과_기관수",
}
METRIC_UNITS = {
    "출생아 수": "명",
    "합계출산율": "명",
    "소아청소년과 기관 수": "개소",
}

# 지도 및 TOP 5 패널 외부 상단에 지표 선택 탭 생성
metric_tab_names = list(METRIC_OPTIONS.keys())
metric_tabs = st.tabs(metric_tab_names)

# 각 탭 클릭 시 표시될 지도 & TOP 5 공통 렌더링 함수
def render_map_and_top5_panel(selected_metric_label: str):
    selected_metric_col = METRIC_OPTIONS[selected_metric_label]

    # 지도 패널과 TOP 5 영역을 하나의 대형 패널(Border Container)로 감쌈
    with st.container(border=True):
        map_col, top5_col = st.columns([7, 3])

        # --- [좌측] 지도 카통 박스 ---
        with map_col:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px; margin-bottom: 16px; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <strong style="color: #0F172A; font-size: 16px;">전국 {selected_metric_label} 단계구분도</strong>
                            <span style="background: #E0F2FE; color: #0284C7; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600;">{selected_map_year}년 실제 분석 데이터</span>
                        </div>
                        <span style="font-size: 12px; color: #64748B; font-weight: 500;">
                            낮음 <span style="color: #BAE6FD;">●●●</span> &nbsp;&nbsp; 높음 <span style="color: #0284C7;">●●●</span>
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                df_map_data = df_filtered_base[df_filtered_base["연도별"] == selected_map_year].copy()
                geo = load_geo()

                if geo is not None and not df_map_data.empty:
                    bright_navy_scale = ["#E0F2FE", "#7DD3FC", "#38BDF8", "#0284C7", "#0369A1", "#1E3A8A"]

                    fig_main_map = px.choropleth_mapbox(
                        df_map_data,
                        geojson=geo,
                        locations="시도별",
                        featureidkey="properties.name",
                        color=selected_metric_col,
                        color_continuous_scale=bright_navy_scale,
                        mapbox_style="white-bg",
                        center={"lat": 35.8, "lon": 127.7},
                        zoom=5.7,
                        opacity=0.9,
                        hover_name="시도별",
                        hover_data={
                            "출생아수": ":,2f",
                            "합계출산율": ":.3f",
                            "소아청소년과_기관수": ":,2f",
                            "시도별": False,
                        },
                        labels={selected_metric_col: selected_metric_label},
                    )

                    fig_main_map.update_layout(
                        margin=dict(l=0, r=0, t=0, b=0),
                        height=810,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        coloraxis_colorbar=dict(
                            title=dict(text=f"{selected_metric_label}", font=dict(size=12, color="#0F172A")),
                            thickness=14,
                            len=0.75,
                            x=0.82,
                            xanchor="left",
                            yanchor="middle",
                        ),
                    )
                    st.plotly_chart(fig_main_map, use_container_width=True)
                else:
                    st.warning("경계 데이터(GeoJSON) 또는 해당 조건의 데이터가 존재하지 않습니다.")

        # --- [우측] TOP 5 순위 카드 박스 ---
        with top5_col:
            # 1. 상단 기본 TOP 5 박스
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style="border-bottom: 1px solid #E2E8F0; padding-bottom: 12px; margin-bottom: 16px;">
                        <div style="font-size: 16px; font-weight: 700; color: #0F172A; display: flex; align-items: center; gap: 6px;">
                            {selected_metric_label} TOP 5
                        </div>
                        <div style="font-size: 12px; color: #64748B; margin-top: 2px;">
                            {selected_map_year}년 상위 5개 지역 현황
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if not df_map_data.empty:
                    df_top5 = df_map_data.sort_values(
                        by=selected_metric_col, ascending=False
                    ).head(5)

                    unit = METRIC_UNITS.get(selected_metric_label, "")

                    for idx, (_, row) in enumerate(df_top5.iterrows(), start=1):
                        sido_name = row["시도별"]
                        val = row[selected_metric_col]
                        formatted_val = f"{val:,.3f}" if selected_metric_col == "합계출산율" else f"{int(val):,}"

                        badge_bg = "#0284C7" if idx == 1 else ("#38BDF8" if idx == 2 else ("#7DD3FC" if idx == 3 else "#94A3B8"))
                        badge_color = "#FFFFFF"

                        st.markdown(
                            f"""
                            <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; margin-bottom: 10px; background: #F8FAFC; border-radius: 8px; border: 1px solid #F1F5F9;">
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <span style="background: {badge_bg}; color: {badge_color}; font-size: 12px; font-weight: 700; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                        {idx}
                                    </span>
                                    <span style="font-size: 14px; font-weight: 600; color: #1E293B;">
                                        {sido_name}
                                    </span>
                                </div>
                                <div style="font-size: 14px; font-weight: 700; color: #0369A1;">
                                    {formatted_val} <span style="font-size: 11px; font-weight: 500; color: #64748B;">{unit}</span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("표시할 TOP 5 데이터가 없습니다.")

            # 2. 하단 대비 소아과 최소 취약 지역 TOP 5 박스
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style="border-bottom: 1px solid #E2E8F0; padding-bottom: 12px; margin-bottom: 12px;">
                        <div style="font-size: 16px; font-weight: 700; color: #0F172A; display: flex; align-items: center; gap: 6px;">
                            소아과 인프라 최저 지역 TOP 5
                        </div>
                        <div style="font-size: 12px; color: #64748B; margin-top: 2px;">
                            {selected_map_year}년 지표 대비 소아청소년과 인프라 최저 5개 지역
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                tab_lowest_birth, tab_lowest_fertility = st.tabs(["출생아 수 대비", "합계출산율 대비"])

                if not df_map_data.empty:
                    df_map_calc = df_map_data.copy()
                    df_map_calc["출생아대비_소아과"] = (df_map_calc["소아청소년과_기관수"] / df_map_calc["출생아수"]) * 1000
                    df_map_calc["출산율대비_소아과"] = df_map_calc["소아청소년과_기관수"] / df_map_calc["합계출산율"]

                    with tab_lowest_birth:
                        df_bot_birth = df_map_calc.sort_values(by="출생아대비_소아과", ascending=True).head(5)
                        for idx, (_, row) in enumerate(df_bot_birth.iterrows(), start=1):
                            sido_name = row["시도별"]
                            val = row["출생아대비_소아과"]
                            badge_bg = "#EF4444" if idx == 1 else ("#F97316" if idx == 2 else ("#FBBF24" if idx == 3 else "#94A3B8"))

                            st.markdown(
                                f"""
                                <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; margin-bottom: 8px; background: #FEF2F2; border-radius: 8px; border: 1px solid #FEE2E2;">
                                    <div style="display: flex; align-items: center; gap: 10px;">
                                        <span style="background: {badge_bg}; color: #FFFFFF; font-size: 11px; font-weight: 700; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                            {idx}
                                        </span>
                                        <span style="font-size: 13px; font-weight: 600; color: #1E293B;">
                                            {sido_name}
                                        </span>
                                    </div>
                                    <div style="font-size: 13px; font-weight: 700; color: #DC2626;">
                                        {val:.2f} <span style="font-size: 10px; font-weight: 500; color: #64748B;">개소/천 명</span>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        st.markdown(
                            """
                            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 6px; padding: 8px 10px; margin-top: 10px; margin-bottom: 12px; font-size: 11px; color: #92400E; line-height: 1.4;">
                                <b>산출 기준:</b> (소아청소년과 기관 수 ÷ 총 출생아 수) × 1,000<br>
                                지역 내 <b>해당 연도 출생아 1,000명당 소아과 개수</b>를 의미합니다.
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    with tab_lowest_fertility:
                        df_bot_fert = df_map_calc.sort_values(by="출산율대비_소아과", ascending=True).head(5)
                        for idx, (_, row) in enumerate(df_bot_fert.iterrows(), start=1):
                            sido_name = row["시도별"]
                            val = row["출산율대비_소아과"]
                            badge_bg = "#EF4444" if idx == 1 else ("#F97316" if idx == 2 else ("#FBBF24" if idx == 3 else "#94A3B8"))

                            st.markdown(
                                f"""
                                <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; margin-bottom: 8px; background: #FEF2F2; border-radius: 8px; border: 1px solid #FEE2E2;">
                                    <div style="display: flex; align-items: center; gap: 10px;">
                                        <span style="background: {badge_bg}; color: #FFFFFF; font-size: 11px; font-weight: 700; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                            {idx}
                                        </span>
                                        <span style="font-size: 13px; font-weight: 600; color: #1E293B;">
                                            {sido_name}
                                        </span>
                                    </div>
                                    <div style="font-size: 13px; font-weight: 700; color: #DC2626;">
                                        {val:.1f} <span style="font-size: 10px; font-weight: 500; color: #64748B;">개소/출산율 1.0</span>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        st.markdown(
                            """
                            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 6px; padding: 8px 10px; margin-top: 10px; margin-bottom: 12px; font-size: 11px; color: #92400E; line-height: 1.4;">
                                <b>산출 기준:</b> 소아청소년과 기관 수 ÷ 합계출산율<br>
                                지역 내 <b>합계출산율 1.0명 당 존재하는 소아과 개수</b>를 의미합니다.
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("표시할 데이터가 없습니다.")

# 외부 탭 3개에 대응하여 각각 지도 & TOP5 영역 바인딩
for tab, metric_name in zip(metric_tabs, metric_tab_names):
    with tab:
        render_map_and_top5_panel(metric_name)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. 하단 세부 분석 탭 (추이 / 상관분석 / 데이터 테이블)
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(
    [
        "연도별 추이",
        "상관관계 분석",
        "상세 데이터 테이블",
    ]
)

# --- Tab 1: 추이 그래프 ---
with tab1:
    st.markdown("### 주요 지표 연도별 변화 추이 분석")
    st.caption("2015년부터 2024년까지의 출생아 수, 합계출산율, 소아청소년과 인프라의 시계열 변화 흐름을 다각도로 분석합니다.")

    with st.container(border=True):
        st.markdown("#### 1. 연도별 주요 지표 추이 (Time-Series Trends)")
        st.caption("연도별(2015~2024년) 출생아 수, 합계출산율, 소아청소년과 기관 수의 시계열 변화 흐름 및 증감 추이 비교")

        all_years = sorted(df_filtered_base["연도별"].unique())
        all_sido_list = sorted(df_filtered_base["시도별"].unique())

        ctrl_col1, ctrl_col2 = st.columns([6, 4])

        with ctrl_col1:
            space_c1, main_c1 = st.columns([0.3, 9.7])
            with main_c1:
                selected_year_range = st.select_slider(
                    "연도 범위 선택",
                    options=all_years,
                    value=(all_years[0], all_years[-1]),
                    key="tab1_year_slider",
                )

        with ctrl_col2:
            space_c2, main_c2 = st.columns([0.3, 9.7])
            with main_c2:
                target_metric = st.selectbox(
                    "지표 선택",
                    options=["출생아수", "합계출산율", "소아청소년과_기관수"],
                    index=0,
                    key="tab1_metric_select",
                )

        graph_col, sido_filter_col = st.columns([8, 2])

        with sido_filter_col:
            st.markdown(
                """
                <div style="margin-top: 10px; margin-bottom: 5px;">
                    <label style="font-size: 14px; font-weight: 400; color: #31333F;">지역 선택</label>
                </div>
                """,
                unsafe_allow_html=True
            )

            for sd in all_sido_list:
                if f"tab1_sido_{sd}" not in st.session_state:
                    st.session_state[f"tab1_sido_{sd}"] = True

            btn_all, btn_none = st.columns(2)
            if btn_all.button("전체선택", key="btn_tab1_select_all", use_container_width=True):
                for sd in all_sido_list:
                    st.session_state[f"tab1_sido_{sd}"] = True

            if btn_none.button("전체해제", key="btn_tab1_deselect_all", use_container_width=True):
                for sd in all_sido_list:
                    st.session_state[f"tab1_sido_{sd}"] = False

            selected_tab1_sido = []
            with st.container(height=380, border=True):
                for sd in all_sido_list:
                    if st.checkbox(sd, key=f"tab1_sido_{sd}"):
                        selected_tab1_sido.append(sd)

            metric_info = {
                "출생아수": "<b>출생아 수</b> (명)",
                "합계출산율": "<b>합계출산율</b> (여성 1명이 평생 낳을 것으로 예상되는 평균 출생아 수, 명)",
                "소아청소년과_기관수": "<b>소아청소년과 기관 수</b> (개소)"
            }

            caption_text = metric_info.get(target_metric, "")

            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 10px; margin-top: 2px; font-size: 11px; color: #64748B; line-height: 1.4;">
                    <b>지표 단위 안내:</b><br>{caption_text}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with graph_col:
            df_line_filtered = df_filtered_base[
                (df_filtered_base["연도별"] >= selected_year_range[0])
                & (df_filtered_base["연도별"] <= selected_year_range[1])
                & (df_filtered_base["시도별"].isin(selected_tab1_sido))
            ]

            if not df_line_filtered.empty:
                fig_line = px.line(
                    df_line_filtered,
                    x="연도별",
                    y=target_metric,
                    color="시도별",
                    markers=True,
                    labels={"연도별": "연도", target_metric: target_metric},
                )
                fig_line.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    height=580,
                    margin=dict(l=10, r=10, t=10, b=10),
                )
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("선택한 지역 또는 연도 범위에 해당하는 데이터가 없습니다. 오른쪽에서 지역을 1개 이상 선택해 주세요.")

# --- Tab 2: 상관관계 분석 ---
with tab2:
    st.markdown("### 출산율 및 소아청소년과 상관관계 다각도 분석")
    st.caption("출생아 수, 합계출산율, 소아청소년과 인프라 간의 입체적 상관관계와 시계열 변화를 분석합니다.")

    corr_vars = ["출생아수", "합계출산율", "소아청소년과_기관수"]

    # 1. 버블 차트
    with st.container(border=True):
        st.markdown("#### 1. 버블 차트 (Bubble Chart)")
        st.caption("X축(출생아 수), Y축(합계출산율), 버블 크기(소아청소년과 기관 수), 색상(17개 시도)을 활용한 3차원 분포 비교")

        all_bubble_years = sorted(df_filtered_base["연도별"].unique(), reverse=True)
        all_bubble_years_asc = sorted(df_filtered_base["연도별"].unique())

        b_ctrl_col1, b_ctrl_col2 = st.columns([7, 3])

        with b_ctrl_col1:
            space_left, main_ctrl = st.columns([0.1, 9.9])
            with main_ctrl:
                bubble_mode = st.radio(
                    "모드 선택",
                    options=[
                        "연도끼리 비교",
                        "특정 연도보기",
                        "연도별 타임라인",
                    ],
                    index=0,
                    horizontal=True,
                    key="tab2_bubble_mode_select",
                )

        with b_ctrl_col2:
            if bubble_mode == "특정 연도보기":
                selected_bubble_year = st.selectbox(
                    "연도 선택",
                    options=all_bubble_years,
                    index=0,
                    key="tab2_bubble_single_year",
                )

        if bubble_mode == "연도끼리 비교":
            year_select_col1, year_select_col2 = st.columns(2)

            with year_select_col1:
                left_year = st.selectbox(
                    "왼쪽 차트 연도 선택",
                    options=all_bubble_years_asc,
                    index=0,
                    key="tab2_bubble_left_year",
                )
            with year_select_col2:
                right_year = st.selectbox(
                    "오른쪽 차트 연도 선택",
                    options=all_bubble_years,
                    index=0,
                    key="tab2_bubble_right_year",
                )

            col_b_left, col_b_right = st.columns(2)

            df_b_left = df_filtered_base[df_filtered_base["연도별"] == left_year]
            df_b_right = df_filtered_base[df_filtered_base["연도별"] == right_year]

            with col_b_left:
                st.markdown(f"**{left_year}년 지역별 분포**")
                fig_b_left = px.scatter(
                    df_b_left,
                    x="출생아수",
                    y="합계출산율",
                    size="소아청소년과_기관수",
                    color="시도별",
                    hover_name="시도별",
                    size_max=45,
                    labels={
                        "출생아수": "출생아 수(명)",
                        "합계출산율": "합계출산율(명)",
                        "소아청소년과_기관수": "소아과 수",
                    },
                )
                fig_b_left.update_layout(
                    plot_bgcolor="white", 
                    paper_bgcolor="white", 
                    height=500, 
                    showlegend=False,
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                fig_b_left.update_xaxes(gridcolor="#F1F5F9")
                fig_b_left.update_yaxes(gridcolor="#F1F5F9")
                st.plotly_chart(fig_b_left, use_container_width=True)

            with col_b_right:
                st.markdown(f"**{right_year}년 지역별 분포**")
                fig_b_right = px.scatter(
                    df_b_right,
                    x="출생아수",
                    y="합계출산율",
                    size="소아청소년과_기관수",
                    color="시도별",
                    hover_name="시도별",
                    size_max=45,
                    labels={
                        "출생아수": "출생아 수(명)",
                        "합계출산율": "합계출산율(명)",
                        "소아청소년과_기관수": "소아과 수",
                    },
                )
                fig_b_right.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    height=500,
                    showlegend=True,
                    legend=dict(
                        yanchor="top",
                        y=1.0,
                        xanchor="left",
                        x=1.02
                    ),
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                fig_b_right.update_xaxes(gridcolor="#F1F5F9")
                fig_b_right.update_yaxes(gridcolor="#F1F5F9")
                st.plotly_chart(fig_b_right, use_container_width=True)

            st.markdown("<hr style='margin: 20px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
            st.markdown("##### 지역별 기준 연도 대비 비교 연도 지표 변동률")

            base_yr = min(left_year, right_year)
            target_yr = max(left_year, right_year)

            st.caption(f" **비교 기간:** {base_yr}년(기준) ➔ {target_yr}년(비교)")

            df_base = df_filtered_base[df_filtered_base["연도별"] == base_yr].set_index("시도별")
            df_target = df_filtered_base[df_filtered_base["연도별"] == target_yr].set_index("시도별")

            sido_rate_list = []
            for sd in sorted(df_filtered_base["시도별"].unique()):
                if sd in df_base.index and sd in df_target.index:
                    b_base = df_base.loc[sd, "출생아수"]
                    b_tgt = df_target.loc[sd, "출생아수"]
                    b_chg = ((b_tgt - b_base) / b_base) * 100 if b_base else 0

                    f_base = df_base.loc[sd, "합계출산율"]
                    f_tgt = df_target.loc[sd, "합계출산율"]
                    f_chg = ((f_tgt - f_base) / f_base) * 100 if f_base else 0

                    p_base = df_base.loc[sd, "소아청소년과_기관수"]
                    p_tgt = df_target.loc[sd, "소아청소년과_기관수"]
                    p_chg = ((p_tgt - p_base) / p_base) * 100 if p_base else 0

                    sido_rate_list.append(
                        {
                            "시도별": sd,
                            f"출생아 수 ({base_yr})": b_base,
                            f"출생아 수 ({target_yr})": b_tgt,
                            "출생아 수 변동률": b_chg,
                            f"합계출산율 ({base_yr})": f_base,
                            f"합계출산율 ({target_yr})": f_tgt,
                            "합계출산율 변동률": f_chg,
                            f"소아과 수 ({base_yr})": p_base,
                            f"소아과 수 ({target_yr})": p_tgt,
                            "소아과 수 변동률": p_chg,
                        }
                    )

            df_sido_rate = pd.DataFrame(sido_rate_list)

            def color_rate(val):
                if pd.isna(val):
                    return "color: #94A3B8"
                elif val > 0:
                    return "color: #16A34A; font-weight: bold; background-color: #DCFCE7;"
                elif val < 0:
                    return "color: #DC2626; font-weight: bold; background-color: #FEE2E2;"
                else:
                    return "color: #475569"

            st.dataframe(
                df_sido_rate.style.map(
                    color_rate,
                    subset=["출생아 수 변동률", "합계출산율 변동률", "소아과 수 변동률"]
                ).format(
                    {
                        f"출생아 수 ({base_yr})": "{:,.0f}",
                        f"출생아 수 ({target_yr})": "{:,.0f}",
                        "출생아 수 변동률": "{:+.2f}%",
                        f"합계출산율 ({base_yr})": "{:.3f}",
                        f"합계출산율 ({target_yr})": "{:.3f}",
                        "합계출산율 변동률": "{:+.2f}%",
                        f"소아과 수 ({base_yr})": "{:,.0f}",
                        f"소아과 수 ({target_yr})": "{:,.0f}",
                        "소아과 수 변동률": "{:+.2f}%",
                    }
                ),
                use_container_width=True,
                hide_index=True,
                height=450,
            )

            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 12px; margin-top: 2px; margin-bottom: 16px; font-size: 11px; color: #64748B; line-height: 1.5;">
                    <b>지표 단위 안내:</b> 
                    <b>출생아 수</b> (명) &nbsp;|&nbsp; 
                    <b>합계출산율</b> (여성 1명이 평생 낳을 것으로 예상되는 평균 출생아 수, 명) &nbsp;|&nbsp; 
                    <b>소아청소년과 기관 수</b> (개소) &nbsp;|&nbsp; 
                    <b>변동률</b> (기준 연도 대비 변화율, %)
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif bubble_mode == "특정 연도보기":
            df_single = df_filtered_base[
                df_filtered_base["연도별"] == selected_bubble_year
            ]
            fig_single = px.scatter(
                df_single,
                x="출생아수",
                y="합계출산율",
                size="소아청소년과_기관수",
                color="시도별",
                hover_name="시도별",
                size_max=50,
                labels={
                    "출생아수": "출생아 수(명)",
                    "합계출산율": "합계출산율(명)",
                    "소아청소년과_기관수": "소아과 수",
                },
            )
            st.markdown(f"**{selected_bubble_year}년 지역별 지표 분포**")
            fig_single.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                height=500,
                legend=dict(
                    yanchor="top",
                    y=1.0,
                    xanchor="left",
                    x=1.02
                ),
                margin=dict(l=10, r=10, t=10, b=10)
            )
            fig_single.update_xaxes(gridcolor="#F1F5F9")
            fig_single.update_yaxes(gridcolor="#F1F5F9")
            st.plotly_chart(fig_single, use_container_width=True)

            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 12px; margin-top: 2px; margin-bottom: 16px; font-size: 11px; color: #64748B; line-height: 1.5;">
                    <b>지표 단위 안내:</b> 
                    <b>출생아 수</b> (명) &nbsp;|&nbsp; 
                    <b>합계출산율</b> (여성 1명이 평생 낳을 것으로 예상되는 평균 출생아 수, 명) &nbsp;|&nbsp; 
                    <b>소아청소년과 기관 수</b> (개소)
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:  # 연도별 타임라인
            df_anim = df_filtered_base.sort_values(by="연도별")
            fig_anim = px.scatter(
                df_anim,
                x="출생아수",
                y="합계출산율",
                size="소아청소년과_기관수",
                color="시도별",
                hover_name="시도별",
                animation_frame="연도별",
                animation_group="시도별",
                size_max=50,
                range_x=[0, df_anim["출생아수"].max() * 1.1],
                range_y=[0.5, df_anim["합계출산율"].max() * 1.1],
                labels={
                    "출생아수": "출생아 수(명)",
                    "합계출산율": "합계출산율(명)",
                    "소아청소년과_기관수": "소아과 수",
                },
            )
            fig_anim.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                height=550,
                legend=dict(
                    yanchor="top",
                    y=1.0,
                    xanchor="left",
                    x=1.02
                ),
                margin=dict(l=10, r=10, t=10, b=10)
            )
            fig_anim.update_xaxes(gridcolor="#F1F5F9")
            fig_anim.update_yaxes(gridcolor="#F1F5F9")
            st.plotly_chart(fig_anim, use_container_width=True)

            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 12px; margin-top: 2px; margin-bottom: 16px; font-size: 11px; color: #64748B; line-height: 1.5;">
                    <b>지표 단위 안내:</b> 
                    <b>출생아 수</b> (명) &nbsp;|&nbsp; 
                    <b>합계출산율</b> (여성 1명이 평생 낳을 것으로 예상되는 평균 출생아 수, 명) &nbsp;|&nbsp; 
                    <b>소아청소년과 기관 수</b> (개소)
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. 상관관계 히트맵
    with st.container(border=True):
        st.markdown("#### 2. 상관관계 히트맵 (Correlation Heatmap Matrix)")
        st.caption("세 지표 간 피어슨 상관계수($3 \\times 3$) 및 지역별 지표 상관정도 비교 분석")

        hm_col1, hm_col2 = st.columns([5, 5])

        with hm_col1:
            with st.container(border=True):
                hdr_left, hdr_right = st.columns([6, 4])

                with hdr_left:
                    st.markdown("**지표 간 상관관계 히트맵**")
                    st.caption("선택한 분석 기간 기준 주요 지표 간 피어슨 상관계수")

                with hdr_right:
                    all_years_sorted = sorted(df_filtered_base["연도별"].unique())
                    heatmap_year_options = ["전체"] + [f"{y}년" for y in all_years_sorted]

                    selected_hm_period = st.selectbox(
                        "연도 선택",
                        options=heatmap_year_options,
                        index=0,
                        key="tab2_heatmap_period_select",
                    )

                if selected_hm_period == "전체":
                    df_hm_target = df_filtered_base
                else:
                    yr_val = int(selected_hm_period.replace("년", ""))
                    df_hm_target = df_filtered_base[df_filtered_base["연도별"] == yr_val]

                corr_matrix = df_hm_target[corr_vars].corr()

                fig_hm = px.imshow(
                    corr_matrix,
                    text_auto=".3f",
                    color_continuous_scale="RdBu_r",
                    zmin=-1.0,
                    zmax=1.0,
                    labels=dict(color="상관계수(r)"),
                    x=["출생아 수", "합계출산율", "소아과 수"],
                    y=["출생아 수", "합계출산율", "소아과 수"],
                )

                fig_hm.update_layout(
                    height=500,
                    margin=dict(l=10, r=0, t=20, b=20),
                    paper_bgcolor="#FFFFFF",
                    plot_bgcolor="#FFFFFF",
                    coloraxis_colorbar=dict(
                        lenmode="fraction",
                        len=0.96,
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.1,
                        xpad=5,
                        thickness=16,
                        title=dict(text="상관계수(r)", font=dict(size=12, color="#0F172A")),
                    ),
                )
                fig_hm.update_yaxes(autorange="reversed", scaleanchor="x")

                st.plotly_chart(fig_hm, use_container_width=True)

        with hm_col2:
            # 3. 상관계수 요약 표
            with st.container(border=True):
                st.markdown("**지역별 출생아 수/합계출산율 vs 소아과 기관 수 상관계수**")

                all_years_corr = sorted(df_filtered_base["연도별"].unique())

                pad_left, slider_col, pad_right = st.columns([0.5, 9.0, 0.5], vertical_alignment="center")
                    
                with slider_col:
                    selected_corr_years = st.select_slider(
                        "",
                        options=all_years_corr,
                        value=(all_years_corr[0], all_years_corr[-1]),
                        key="tab2_corr_table_year_slider",
                        label_visibility="collapsed",
                    )

                df_corr_table_source = df_filtered_base[
                    (df_filtered_base["연도별"] >= selected_corr_years[0])
                    & (df_filtered_base["연도별"] <= selected_corr_years[1])
                ]

                sido_corr_list = []
                for sd in sorted(df_filtered_base["시도별"].unique()):
                    df_sd = df_corr_table_source[df_corr_table_source["시도별"] == sd]
                    
                    if len(df_sd) >= 2:
                        corr_birth = df_sd["출생아수"].corr(df_sd["소아청소년과_기관수"])
                        corr_fer = df_sd["합계출산율"].corr(df_sd["소아청소년과_기관수"])
                    else:
                        corr_birth = None
                        corr_fer = None

                    sido_corr_list.append(
                        {
                            "시도별": sd,
                            "출생아 수 vs 소아과 수 상관계수": corr_birth,
                            "합계출산율 vs 소아과 수 상관계수": corr_fer,
                        }
                    )

                df_sido_corr = pd.DataFrame(sido_corr_list)

                def color_corr(val):
                    if pd.isna(val):
                        return "color: #94A3B8"
                    elif val >= 0.7:
                        return "color: #065F46; font-weight: bold; background-color: #D1FAE5;"
                    elif val >= 0.3:
                        return "color: #047857; background-color: #ECFDF5;"
                    elif val <= -0.7:
                        return "color: #991B1B; font-weight: bold; background-color: #FEE2E2;"
                    elif val <= -0.3:
                        return "color: #B91C1C; background-color: #FEF2F2;"
                    else:
                        return "color: #475569"

                st.dataframe(
                    df_sido_corr.style.map(
                        color_corr,
                        subset=["출생아 수 vs 소아과 수 상관계수", "합계출산율 vs 소아과 수 상관계수"]
                    ).format(
                        {
                            "출생아 수 vs 소아과 수 상관계수": "{:+.3f}",
                            "합계출산율 vs 소아과 수 상관계수": "{:+.3f}",
                        },
                        na_rep="계산 불가",
                    ),
                    use_container_width=True,
                    hide_index=True,
                    height=397,
                )

                st.markdown(
                    """
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 12px; margin-top: -10px; font-size: 11px; color: #64748B; line-height: 1.5;">
                        <b>상관계수 해석 범주: </b> 
                        <span style="color: #065F46; font-weight: bold;">+0.7 이상</span> (강한 양의 상관관계) &nbsp;|&nbsp; 
                        <span style="color: #047857;">+0.3 ~ +0.7</span> (뚜렷한/약한 양의 상관관계) &nbsp;|&nbsp; 
                        <span>-0.3 ~ +0.3</span> (상관관계 거의 없음) &nbsp;|&nbsp; 
                        <span style="color: #B91C1C;">-0.7 ~ -0.3</span> (뚜렷한/약한 음의 상관관계) &nbsp;|&nbsp; 
                        <span style="color: #991B1B; font-weight: bold;">-0.7 이하</span> (강한 음의 상관관계)
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown("<br>", unsafe_allow_html=True)
                
    st.markdown("<br>", unsafe_allow_html=True)

    # 3. 산점도 행렬
    with st.container(border=True):
        st.markdown("#### 3. 다중 산점도 대시보드 (Multi-Scatter Plot Dashboard)")
        st.caption("X/Y축에 출생아 수·합계출산율·소아과 수를 교차 적용하고 17개 지자체별 색상 점으로 분포 및 편차를 비교 분석하는 그래프")

        chart_col, filter_col = st.columns([8.2, 1.8])

        all_sido_options = sorted(df_filtered_base["시도별"].unique())
        if "spm_selected_sidos" not in st.session_state:
            st.session_state["spm_selected_sidos"] = all_sido_options.copy()

        with filter_col:
            selected_spm_year = st.selectbox(
                "연도 선택",
                options=["전체"] + [f"{y}년" for y in sorted(df_filtered_base["연도별"].unique(), reverse=True)],
                index=0,
                key="tab2_spm_year_select",
            )

            st.markdown(
                """
                <div style="margin-top: 10px; margin-bottom: 5px;">
                    <label style="font-size: 14px; font-weight: 400; color: #31333F;">지역 선택</label>
                </div>
                """,
                unsafe_allow_html=True
            )            
            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("전체선택", key="spm_btn_all", use_container_width=True):
                st.session_state["spm_selected_sidos"] = all_sido_options.copy()
                st.rerun()
            if btn_col2.button("전체해제", key="spm_btn_none", use_container_width=True):
                st.session_state["spm_selected_sidos"] = []
                st.rerun()

            new_selected_sidos = []
            with st.container(height=330, border=True):
                for sido in all_sido_options:
                    is_checked = sido in st.session_state["spm_selected_sidos"]
                    if st.checkbox(sido, value=is_checked, key=f"spm_chk_{sido}"):
                        new_selected_sidos.append(sido)

            if new_selected_sidos != st.session_state["spm_selected_sidos"]:
                st.session_state["spm_selected_sidos"] = new_selected_sidos
                st.rerun()

        if selected_spm_year == "전체":
            df_spm_target = df_filtered_base.copy()
        else:
            yr_int = int(selected_spm_year.replace("년", ""))
            df_spm_target = df_filtered_base[df_filtered_base["연도별"] == yr_int].copy()

        selected_spm_sido = st.session_state["spm_selected_sidos"]
        if selected_spm_sido:
            df_spm_target = df_spm_target[df_spm_target["시도별"].isin(selected_spm_sido)]
        else:
            df_spm_target = df_spm_target.iloc[0:0]

        with chart_col:
            st.markdown(
                """
                <div style="display: flex; justify-content: space-between; text-align: center; margin-bottom: 8px; padding: 0 10px;">
                    <div style="flex: 1; font-weight: bold; font-size: 16px; color: #1E293B;">출생아 수 vs 소아과 수</div>
                    <div style="flex: 1; font-weight: bold; font-size: 16px; color: #1E293B;">합계출산율 vs 소아과 수</div>
                    <div style="flex: 1; font-weight: bold; font-size: 16px; color: #1E293B;">합계출산율 vs 출생아 수</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            fig_matrix = make_subplots(
                rows=1, cols=3,
                horizontal_spacing=0.08
            )

            sido_list = sorted(df_spm_target["시도별"].unique())
            colors = px.colors.qualitative.Alphabet if len(sido_list) > 10 else px.colors.qualitative.Plotly
            color_map = {sido: colors[i % len(colors)] for i, sido in enumerate(sido_list)}

            added_sidos = set()

            for sido in sido_list:
                df_sido = df_spm_target[df_spm_target["시도별"] == sido]
                show_legend = sido not in added_sidos

                fig_matrix.add_trace(
                    go.Scatter(
                        x=df_sido["출생아수"],
                        y=df_sido["소아청소년과_기관수"],
                        mode="markers",
                        name=sido,
                        marker=dict(color=color_map[sido], size=8),
                        hovertext=df_sido["시도별"],
                        hovertemplate="<b>%{hovertext}</b><br>출생아 수: %{x:,.0f}명<br>소아과 수: %{y:,.0f}개소<extra></extra>",
                        showlegend=show_legend,
                    ),
                    row=1, col=1
                )

                fig_matrix.add_trace(
                    go.Scatter(
                        x=df_sido["합계출산율"],
                        y=df_sido["소아청소년과_기관수"],
                        mode="markers",
                        name=sido,
                        marker=dict(color=color_map[sido], size=8),
                        hovertext=df_sido["시도별"],
                        hovertemplate="<b>%{hovertext}</b><br>합계출산율: %{x:.3f}명<br>소아과 수: %{y:,.0f}개소<extra></extra>",
                        showlegend=False,
                    ),
                    row=1, col=2
                )

                fig_matrix.add_trace(
                    go.Scatter(
                        x=df_sido["합계출산율"],
                        y=df_sido["출생아수"],
                        mode="markers",
                        name=sido,
                        marker=dict(color=color_map[sido], size=8),
                        hovertext=df_sido["시도별"],
                        hovertemplate="<b>%{hovertext}</b><br>합계출산율: %{x:.3f}명<br>출생아 수: %{y:,.0f}명<extra></extra>",
                        showlegend=False,
                    ),
                    row=1, col=3
                )
                added_sidos.add(sido)

            shapes = [
                dict(type="line", xref="paper", yref="paper", x0=0.300, y0=0, x1=0.300, y1=1, line=dict(color="#CBD5E1", width=1)),
                dict(type="line", xref="paper", yref="paper", x0=0.655, y0=0, x1=0.655, y1=1, line=dict(color="#CBD5E1", width=1))
            ]

            fig_matrix.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                height=500,
                margin=dict(l=10, r=10, t=10, b=100),
                shapes=shapes,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.22,
                    xanchor="center",
                    x=0.5,
                    entrywidth=110,
                    entrywidthmode="pixels"
                )
            )

            fig_matrix.update_xaxes(title_text="출생아 수(명)", gridcolor="#F1F5F9", row=1, col=1)
            fig_matrix.update_yaxes(title_text="소아과 수(개소)", title_standoff=3, gridcolor="#F1F5F9", row=1, col=1)

            fig_matrix.update_xaxes(title_text="합계출산율(명)", gridcolor="#F1F5F9", row=1, col=2)
            fig_matrix.update_yaxes(title_text="소아과 수(개소)", title_standoff=3, gridcolor="#F1F5F9", row=1, col=2)

            fig_matrix.update_xaxes(title_text="합계출산율(명)", gridcolor="#F1F5F9", row=1, col=3)
            fig_matrix.update_yaxes(title_text="출생아 수(명)", title_standoff=3, gridcolor="#F1F5F9", row=1, col=3)

            st.plotly_chart(fig_matrix, use_container_width=True)

        st.markdown(
            """
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 12px; margin-top: 1px; margin-bottom: 16px; font-size: 11px; color: #64748B; line-height: 1.5;">
                <b>지표 단위 안내:</b> 
                <b>출생아 수</b> (명) &nbsp;|&nbsp; 
                <b>합계출산율</b> (여성 1명이 평생 낳을 것으로 예상되는 평균 출생아 수, 명) &nbsp;|&nbsp; 
                <b>소아청소년과 기관 수</b> (개소)
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. 이중축 혼합 차트
    with st.container(border=True):
        st.markdown("#### 4. 이중축 혼합 차트 (Dual-Axis Combo Chart)")
        st.caption("시간 흐름에 따른 세 지표의 동시 감소/변화 추세를 시계열로 추적")

        combo_sido_list = ["전국"] + sorted(df_filtered_base["시도별"].unique().tolist())
        selected_combo_sido = st.selectbox(
            "분석 대상 지역 선택",
            options=combo_sido_list,
            index=0,
            key="tab2_combo_sido_select",
        )

        st.markdown(
            f"**{selected_combo_sido} 연도별 지표 추이**"
        )

        if selected_combo_sido == "전국":
            st.markdown(
                """
                <div style="background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; font-size: 12px; color: #0369A1; line-height: 1.5;">
                    <b>전국 데이터 산출 기준 안내:</b> 
                    <b>출생아 수</b> (17개 시·도 총합) &nbsp;|&nbsp; 
                    <b>합계출산율</b> (17개 시·도 산술 평균) &nbsp;|&nbsp; 
                    <b>소아청소년과 기관 수</b> (17개 시·도 총합)
                </div>
                """,
                unsafe_allow_html=True,
            )

            df_combo = (
                df_filtered_base.groupby("연도별")
                .agg({"출생아수": "sum", "합계출산율": "mean", "소아청소년과_기관수": "sum"})
                .reset_index()
            )
        else:
            df_combo = df_filtered_base[df_filtered_base["시도별"] == selected_combo_sido].sort_values(by="연도별")

        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])

        fig_dual.add_trace(
            go.Bar(
                x=df_combo["연도별"],
                y=df_combo["출생아수"],
                name="출생아 수 (명)",
                marker_color="#A3DFFF",
                opacity=0.85,
            ),
            secondary_y=False,
        )

        fig_dual.add_trace(
            go.Scatter(
                x=df_combo["연도별"],
                y=df_combo["합계출산율"],
                name="합계출산율 (명)",
                mode="lines+markers",
                line=dict(color="#EF4444", width=3),
            ),
            secondary_y=True,
        )

        fig_dual.add_trace(
            go.Scatter(
                x=df_combo["연도별"],
                y=df_combo["소아청소년과_기관수"],
                name="소아청소년과 기관 수 (개소)",
                mode="lines+markers",
                line=dict(color="#8B5CF6", width=3),
            ),
            secondary_y=False,
        )

        fig_dual.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=450,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig_dual.update_xaxes(title_text="연도", gridcolor="#F1F5F9", dtick=1)
        fig_dual.update_yaxes(title_text="출생아 수 / 소아과 기관 수", secondary_y=False, gridcolor="#F1F5F9")
        fig_dual.update_yaxes(title_text="합계출산율 (명)", secondary_y=True, showgrid=False)

        st.plotly_chart(fig_dual, use_container_width=True)

        st.markdown(
            """
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 12px; margin-top: 1px; margin-bottom: 16px; font-size: 11px; color: #64748B; line-height: 1.5;">
                    <b>지표 단위 안내:</b> 
                    <b>출생아 수</b> (명) &nbsp;|&nbsp; 
                    <b>합계출산율</b> (여성 1명이 평생 낳을 것으로 예상되는 평균 출생아 수, 명) &nbsp;|&nbsp; 
                    <b>소아청소년과 기관 수</b> (개소)
                </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

# --- Tab 3: 데이터 테이블 ---
with tab3:
    st.subheader("통합 데이터 목록")

    available_years_tab = sorted(df_filtered_base["연도별"].unique(), reverse=True)
    if available_years_tab:
        selected_single_year = st.selectbox(
            "조회할 연도 선택",
            options=available_years_tab,
            index=0,
            key="tab3_year_select",
        )

        df_table_filtered = df_filtered_base[
            df_filtered_base["연도별"] == selected_single_year
        ]

        df_display = (
            df_table_filtered.drop(columns=["연도별"])
            .sort_values(by="시도별")
            .reset_index(drop=True)
        )
        df_display.index = df_display.index + 1

        st.dataframe(df_display, use_container_width=True, hide_index=True)