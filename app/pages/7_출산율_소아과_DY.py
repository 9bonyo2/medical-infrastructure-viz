import os
import sys

# 프로젝트 루트 경로 추가 (app/pages -> medical-infrastructure-viz)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st

from src.pediatric.collection import get_geojson
from src.pediatric.correlation import calculate_correlation, create_heatmap_figure
from src.pediatric.preprocess import get_preprocessed_data
from utils.components import kpi_card
from utils.nav import render_sidebar
from utils.style import inject_base_style

# ---------------------------------------------------------
# 1. 페이지 설정 및 공통 스타일 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="출산율과 소아과 분석 (DY)",
    page_icon="💉",
    layout="wide",
)

# 공통 CSS 및 사이드바 내비게이션 적용
inject_base_style()
render_sidebar(active_key="pediatric_dy")

# 한글 폰트 설정
plt.rc("font", family="Malgun Gothic")
plt.rc("axes", unicode_minus=False)

SEQUENTIAL_SCALE = "Blues"


# ---------------------------------------------------------
# 2. 캐시 데이터 로드 함수
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df = get_preprocessed_data()
    # 2015~2024년 데이터 사용
    return df[df["연도별"] <= 2024]


@st.cache_data
def load_geo():
    return get_geojson()


try:
    df_data = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. 사이드바 데이터 필터
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 데이터 필터 옵션")

df_filtered_base = df_data[df_data["시도별"] != "전국"]

# 연도 선택 필터
years = sorted(df_filtered_base["연도별"].unique())
with st.sidebar.expander("📅 연도 선택", expanded=False):
    select_all_years = st.checkbox("전체 선택", value=True, key="all_years")
    selected_years = []
    for yr in years:
        val = select_all_years if select_all_years else False
        if st.checkbox(f"{yr}년", value=val, key=f"yr_{yr}"):
            selected_years.append(yr)

# 시도 선택 필터
sido_list = sorted(df_filtered_base["시도별"].unique())
with st.sidebar.expander("📍 시도 선택", expanded=False):
    select_all_sido = st.checkbox("전체 선택", value=True, key="all_sido")
    selected_sido = []
    for sd in sido_list:
        val = select_all_sido if select_all_sido else False
        if st.checkbox(sd, value=val, key=f"sido_{sd}"):
            selected_sido.append(sd)

df_filtered = df_filtered_base[
    (df_filtered_base["연도별"].isin(selected_years))
    & (df_filtered_base["시도별"].isin(selected_sido))
]

# ---------------------------------------------------------
# 4. 헤더 및 KPI 카드 영역
# ---------------------------------------------------------
st.markdown('<div class="page-title">💉 출생아 수 & 소아청소년과 현황 분석</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">출생아 수, 합계출산율 및 소아청소년과 인프라 간의 상관관계와 지역별/연도별 추이를 분석합니다.</div>',
    unsafe_allow_html=True,
)

# utils.components의 kpi_card를 활용한 상단 메트릭 구성
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

total_births = int(df_filtered["출생아수"].sum()) if not df_filtered.empty else 0
avg_fertility = df_filtered["합계출산율"].mean() if not df_filtered.empty else 0.0
avg_pediatrics = df_filtered["소아청소년과_기관수"].mean() if not df_filtered.empty else 0.0

with kpi_col1:
    kpi_card(
        icon="👶",
        label="총 출생아 수 (선택 범위)",
        value=f"{total_births:,}",
        unit="명",
    )
with kpi_col2:
    kpi_card(
        icon="📉",
        label="평균 합계출산율",
        value=f"{avg_fertility:.3f}",
        unit="명",
    )
with kpi_col3:
    kpi_card(
        icon="🏥",
        label="평균 소아청소년과 기관 수",
        value=f"{avg_pediatrics:.1f}",
        unit="개소",
    )

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. 메인 분석 탭 (추이 / 상관분석 / 지도 및 데이터)
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(
    [
        "📈 연도별/지역별 추이",
        "📊 상관분석 (히트맵 & 산점도)",
        "📋 데이터 테이블 & 지도",
    ]
)

# --- Tab 1: 추이 그래프 ---
with tab1:
    st.subheader("연도별 주요 지표 추이")
    target_metric = st.radio(
        "시각화할 지표 선택",
        ["출생아수", "합계출산율", "소아청소년과_기관수"],
        horizontal=True,
    )

    fig_line = px.line(
        df_filtered,
        x="연도별",
        y=target_metric,
        color="시도별",
        markers=True,
        title=f"연도별 {target_metric} 변화 추이",
        labels={"연도별": "연도", target_metric: target_metric},
    )
    fig_line.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig_line, use_container_width=True)

# --- Tab 2: 상관관계 분석 ---
with tab2:
    st.subheader("지표 간 상관계수 분석")
    corr_vars = ["출생아수", "합계출산율", "소아청소년과_기관수"]

    if not df_filtered.empty:
        corr_matrix = calculate_correlation(df_filtered, corr_vars)

        st.write("**상관계수 행렬**")
        st.dataframe(
            corr_matrix.style.background_gradient(cmap="coolwarm").format("{:.4f}"),
            use_container_width=True,
        )

        st.write("**상관계수 히트맵**")
        fig_sns = create_heatmap_figure(corr_matrix)
        st.pyplot(fig_sns)

        st.divider()

        st.subheader("📈 지표 간 산점도 분석")
        col_scatter1, col_scatter2 = st.columns(2)
        with col_scatter1:
            x_axis = st.selectbox("X축 지표", corr_vars, index=0)
        with col_scatter2:
            y_axis = st.selectbox("Y축 지표", corr_vars, index=2)

        fig_scatter = px.scatter(
            df_filtered,
            x=x_axis,
            y=y_axis,
            color="시도별",
            hover_data=["연도별"],
            trendline="ols",
            title=f"{x_axis} vs {y_axis} 관계",
        )
        fig_scatter.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("선택된 조건에 해당하는 데이터가 없습니다.")

# --- Tab 3: 데이터 테이블 & 지도 ---
with tab3:
    st.subheader("통합 데이터 목록")

    available_years = sorted(df_filtered_base["연도별"].unique())
    if available_years:
        selected_single_year = st.selectbox(
            "조회할 연도 선택",
            options=available_years,
            index=len(available_years) - 1,
        )

        df_table_filtered = df_filtered[
            df_filtered["연도별"] == selected_single_year
        ]

        df_display = (
            df_table_filtered.drop(columns=["연도별"])
            .sort_values(by="시도별")
            .reset_index(drop=True)
        )
        df_display.index = df_display.index + 1

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # CSV 다운로드
        col_down1, col_down2 = st.columns(2)
        with col_down1:
            csv_single_data = df_display.to_csv(encoding="utf-8-sig")
            st.download_button(
                label=f"📥 {selected_single_year}년 선택 데이터 다운로드",
                data=csv_single_data,
                file_name=f"출생아수_소아과현황_{selected_single_year}.csv",
                mime="text/csv",
                key="btn_single_year",
            )
        with col_down2:
            csv_full_data = df_filtered.sort_values(
                by=["연도별", "시도별"]
            ).to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 선택 기간 전체 통합 데이터 다운로드",
                data=csv_full_data,
                file_name="출생아수_합계출산율_소아청소년과_기관수_통합데이터.csv",
                mime="text/csv",
                key="btn_full_years",
            )

        st.divider()

        st.subheader(f"🗺️ {selected_single_year}년 대한민국 지역별 지도 현황")

        METRIC_OPTIONS = {
            "출생아수": "출생아수",
            "합계출산율": "합계출산율",
            "소아청소년과 기관수": "소아청소년과_기관수",
        }

        col_top1, col_top2, col_top3 = st.columns([1.5, 1, 1])

        with col_top1:
            metric_label = st.radio(
                "지도에 표시할 지표",
                list(METRIC_OPTIONS.keys()),
                index=0,
                key="map_metric_radio",
            )
            metric_col = METRIC_OPTIONS[metric_label]

        avg_val = (
            df_table_filtered[metric_col].mean()
            if not df_table_filtered.empty
            else 0
        )
        sum_val = (
            df_table_filtered[metric_col].sum()
            if not df_table_filtered.empty
            else 0
        )

        with col_top2:
            if metric_col == "합계출산율":
                st.metric(f"전국 평균 {metric_label}", f"{avg_val:.3f}")
            elif metric_col == "출생아수":
                st.metric(f"전국 총 {metric_label}", f"{int(sum_val):,}명")
            else:
                st.metric(f"전국 평균 {metric_label}", f"{avg_val:.1f}개소")

        with col_top3:
            if not df_table_filtered.empty:
                top_region = df_table_filtered.sort_values(
                    metric_col, ascending=False
                ).iloc[0]
                top_val_formatted = (
                    f"{top_region[metric_col]:.3f}"
                    if metric_col == "합계출산율"
                    else f"{int(top_region[metric_col]):,}"
                )
                st.metric(
                    f"{metric_label} 1위",
                    f"{top_region['시도별']} ({top_val_formatted})",
                )

        st.markdown("<br>", unsafe_allow_html=True)

        col_map, col_bar = st.columns(2)

        with col_map:
            geo = load_geo()

            if geo is not None:
                color_scales = {
                    "출생아수": "Reds",
                    "합계출산율": "Viridis",
                    "소아청소년과_기관수": SEQUENTIAL_SCALE,
                }

                fig_map = px.choropleth_mapbox(
                    df_table_filtered,
                    geojson=geo,
                    locations="시도별",
                    featureidkey="properties.name",
                    color=metric_col,
                    color_continuous_scale=color_scales[metric_col],
                    mapbox_style="carto-positron",
                    center={"lat": 35.9, "lon": 127.7},
                    zoom=5.5,
                    opacity=0.85,
                    hover_name="시도별",
                    hover_data={
                        "출생아수": ":,2f",
                        "합계출산율": ":.3f",
                        "소아청소년과_기관수": ":,2f",
                        "시도별": False,
                    },
                    labels={metric_col: metric_label},
                )
                fig_map.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=520,
                    coloraxis_colorbar=dict(title=metric_label),
                )
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.warning("경계 데이터(GeoJSON)를 로드할 수 없습니다.")

        with col_bar:
            st.markdown("##### 시도별 순위")
            fig_bar = px.bar(
                df_table_filtered.sort_values(metric_col, ascending=True),
                x=metric_col,
                y="시도별",
                orientation="h",
                color=metric_col,
                color_continuous_scale=(
                    "Reds"
                    if metric_col == "출생아수"
                    else (
                        "Blues"
                        if metric_col == "소아청소년과_기관수"
                        else "Viridis"
                    )
                ),
                labels={metric_col: metric_label, "시도별": ""},
            )
            fig_bar.update_layout(
                height=480,
                coloraxis_showscale=False,
                margin=dict(l=0, r=10, t=10, b=0),
                plot_bgcolor="white",
                paper_bgcolor="white",
            )
            st.plotly_chart(fig_bar, use_container_width=True)