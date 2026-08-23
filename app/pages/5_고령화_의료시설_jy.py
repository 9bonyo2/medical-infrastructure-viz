import streamlit as st

from utils.style import inject_base_style
from utils.nav import render_sidebar
from utils.components import (
    kpi_row,
    region_panel,
    correlation_trend_chart,
    small_multiples_grid,
)
from utils.sample_data import (
    get_aging_kpis,
    get_region_vulnerability_df,
    get_correlation_trend_df,
    get_small_multiples_df,
)

st.set_page_config(page_title="고령화와 노인의료 분석", page_icon="👵", layout="wide")

inject_base_style()
render_sidebar(active_key="aging_jy")

# ── 타이틀 ────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">고령화 파트</div>', unsafe_allow_html=True)

# ── 상단 KPI 4개 ─────────────────────────────────────────────────────
kpi_row(
    get_aging_kpis(),
    icon_map={
        "facility_per_100k": ("🏢", "인구 10만 명당 응급의료기관 수"),
        "specialist_per_100k": ("👨‍⚕️", "인구 10만 명당 응급의료 전문의 수"),
        "transfer_rate": ("🔁", "응급진료 후 전원율"),
        "emergency_cases": ("🚑", "응급진료 건수"),
    },
)

st.write("")

# ── 전국 현황 버블맵 + 팀원별 작업 공간 ──────────────────────────────────
left, right = st.columns([2, 1], gap="medium")

with left:
    with st.container(border=True):
        region_panel(get_region_vulnerability_df())

with right:
    with st.container(border=True):
        st.markdown(
            '<div class="panel-title" style="margin-bottom:10px;">'
            '고령인구 10만명당 노인복지시설·요양병원 수 상관관계 분석</div>',
            unsafe_allow_html=True,
        )
        # 팀원별 작업 공간 탭 — 각자 분석 메모/스니펫을 넣는 용도 (자유롭게 구조 변경 가능)
        tab_names = ["서연", "지영", "성재"]
        tabs = st.tabs(tab_names)
        for tab, name in zip(tabs, tab_names):
            with tab:
                for i in range(1, 5):
                    st.text_area(
                        f"{name} 메모 {i}",
                        key=f"aging_note_{name}_{i}",
                        placeholder="분석 내용 / 코드 스니펫 / 링크 등을 자유롭게 기록하세요.",
                        label_visibility="collapsed",
                        height=68,
                    )

st.write("")

# ── 상관계수 추이 + 데이터 표 + 필터 ─────────────────────────────────────
chart_col, table_col, filter_col = st.columns([2.2, 1, 1], gap="medium")

with chart_col:
    with st.container(border=True):
        title_col, select_col = st.columns([3, 1])
        with title_col:
            st.markdown(
                '<div class="panel-title">고령인구 비율 vs 시설 공급 비율 상관계수</div>',
                unsafe_allow_html=True,
            )
        with select_col:
            st.selectbox("연도", options=list(range(2015, 2025)), index=9, label_visibility="collapsed")

        trend_df = get_correlation_trend_df()
        correlation_trend_chart(trend_df, x_col="year", series_cols=["노인복지시설", "요양병원"])
        st.caption("그래프 캡션: 그래프 간단 분석 설명")

with table_col:
    with st.container(border=True):
        st.markdown('<div class="panel-title">수치 표 데이터</div>', unsafe_allow_html=True)
        st.dataframe(get_correlation_trend_df(), use_container_width=True, hide_index=True, height=340)

with filter_col:
    with st.container(border=True):
        st.markdown("**📅 연도 선택**")
        select_all = st.checkbox("전체 선택", value=True, key="aging_year_all")
        years = list(range(2015, 2025))
        selected_years = []
        for y in years:
            checked = st.checkbox(f"{y}년", value=select_all, key=f"aging_year_{y}")
            if checked:
                selected_years.append(y)

        st.markdown("---")
        with st.expander("📍 시도 선택"):
            all_regions = list({
                "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
                "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
            })
            st.multiselect("시도", options=sorted(all_regions), default=sorted(all_regions),
                            label_visibility="collapsed", key="aging_region_filter")

st.write("")

# ── 연도별 소규모 산점도 그리드 (노인복지시설) ───────────────────────────
with st.container(border=True):
    st.markdown(
        '<div class="panel-title">고령인구비율 vs 고령인구 10만명당 노인복지시설 수 — 연도별</div>',
        unsafe_allow_html=True,
    )
    small_multiples_grid(get_small_multiples_df("노인복지시설"))
    st.caption("그래프 캡션: 그래프 간단 분석 설명")

st.write("")

# ── 연도별 소규모 산점도 그리드 (요양병원) ───────────────────────────────
with st.container(border=True):
    st.markdown(
        '<div class="panel-title">고령인구비율 vs 고령인구 10만명당 요양병원 수 — 연도별</div>',
        unsafe_allow_html=True,
    )
    small_multiples_grid(get_small_multiples_df("요양병원"))
    st.caption("그래프 캡션: 그래프 간단 분석 설명")
