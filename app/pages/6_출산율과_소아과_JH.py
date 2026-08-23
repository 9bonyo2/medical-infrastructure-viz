import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="소아과 공급 역량 분석",
    page_icon="🍼",
    layout="wide",
    initial_sidebar_state="expanded",
)

from pediatric.charts import plot_region_trends, plot_year_comparison  # noqa: E402
from pediatric.controls import select_regions_dropdown, select_year_dropdown  # noqa: E402
from pediatric.data_loader import load_data  # noqa: E402
from pediatric.maps import plot_supply_capacity_map  # noqa: E402
from pediatric.page_style import (  # noqa: E402
    configure_matplotlib_font,
    inject_pediatric_page_style,
)
from pediatric.summaries import (  # noqa: E402
    show_global_kpis,
    show_supply_capacity_summary,
    show_trend_analysis_summary,
    show_year_comparison_summary,
)
from utils.nav import render_sidebar  # noqa: E402
from utils.style import inject_base_style  # noqa: E402


CLINIC_METRIC = "의원1개당전문의수"
CHILD_METRIC = "아동1만명당전문의수"


inject_base_style()
inject_pediatric_page_style()
configure_matplotlib_font()
render_sidebar(active_key="birth_jh")

try:
    df = load_data()
except (ValueError, UnicodeDecodeError, pd.errors.ParserError) as error:
    st.error(f"CSV 파일을 읽을 수 없습니다. {error}")
    st.stop()

years = sorted(df["시점"].dropna().astype(int).unique().tolist())
all_regions = sorted(df["지역"].dropna().unique())

title_column, reference_year_column = st.columns([5, 1], gap="large")
with title_column:
    st.markdown(
        '<div class="page-title">소아과 공급 역량 분석</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-subtitle">지역별 소아과 의원 대비 전문의 인력과 '
        '아동 인구 대비 전문의 공급 수준을 비교합니다.</div>',
        unsafe_allow_html=True,
    )
with reference_year_column:
    reference_year = select_year_dropdown(
        "기준 연도", years, "main_reference_year"
    )

show_global_kpis(df, reference_year)
st.divider()

with st.container(border=True):
    st.markdown("### 중앙값 기준 소아과 공급 지도")
    st.caption("색이 진할수록 두 공급 지표의 중앙값 대비 수준이 높습니다.")

supply_year = reference_year

map_column, supply_summary_column = st.columns([1.35, 0.65], gap="large")
with map_column:
    with st.container(border=True):
        plot_supply_capacity_map(df, supply_year)
with supply_summary_column:
    with st.container(border=True):
        show_supply_capacity_summary(df, supply_year)

st.divider()
trend_tab, comparison_tab = st.tabs(["지역별 연도 추세", "연도별 지역 추세"])

with trend_tab:
    with st.container(border=True):
        st.markdown("#### 분석 지역 선택")
        selected_regions = select_regions_dropdown(
            "표시할 지역", all_regions, "main_trend_regions"
        )

    if not selected_regions:
        st.warning("그래프에 표시할 지역을 한 개 이상 선택해 주세요.")
    else:
        clinic_title_column, child_title_column = st.columns(2, gap="large")
        with clinic_title_column:
            st.markdown("#### 의원 1개당 전문의 수 연도 추세")
        with child_title_column:
            st.markdown("#### 아동 1만 명당 전문의 수 연도 추세")

        clinic_chart_column, child_chart_column = st.columns(2, gap="large")
        with clinic_chart_column:
            with st.container(border=True):
                plot_region_trends(df, selected_regions, CLINIC_METRIC)
        with child_chart_column:
            with st.container(border=True):
                plot_region_trends(df, selected_regions, CHILD_METRIC)

        with st.container(border=True, key="trend-summary-card"):
            show_trend_analysis_summary(df, selected_regions)

with comparison_tab:
    with st.container(border=True):
        st.markdown("#### 비교 연도 선택")
        comparison_year = select_year_dropdown(
            "비교 연도", years, "main_comparison_year"
        )

    clinic_title_column, child_title_column = st.columns(2, gap="large")
    with clinic_title_column:
        st.markdown(f"#### {comparison_year}년 지역별 의원 1개당 전문의 수")
    with child_title_column:
        st.markdown(f"#### {comparison_year}년 지역별 아동 1만 명당 전문의 수")

    clinic_chart_column, child_chart_column = st.columns(2, gap="large")
    with clinic_chart_column:
        with st.container(border=True):
            plot_year_comparison(df, comparison_year, CLINIC_METRIC)
    with child_chart_column:
        with st.container(border=True):
            plot_year_comparison(df, comparison_year, CHILD_METRIC)

    with st.container(border=True, key="year-comparison-summary-card"):
        show_year_comparison_summary(df, comparison_year)