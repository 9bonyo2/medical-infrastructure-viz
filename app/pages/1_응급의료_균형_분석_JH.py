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
    get_emergency_kpis,
    get_region_vulnerability_df,
    get_correlation_trend_df,
    get_small_multiples_df,
)

st.set_page_config(page_title="응급의료 균형 분석", page_icon="🚑", layout="wide")

inject_base_style()
render_sidebar(active_key="emergency")

# TODO(팀): 아래는 고령화 페이지와 동일한 레이아웃의 템플릿입니다.
#   utils/sample_data.py 에 응급의료 전용 데이터 함수를 추가한 뒤
#   get_correlation_trend_df / get_small_multiples_df 자리를 교체해주세요.

st.markdown('<div class="page-title">응급의료 균형 분석</div>', unsafe_allow_html=True)

kpi_row(
    get_emergency_kpis(),
    icon_map={
        "facility_per_100k": ("🏥", "인구 10만 명당 응급의료기관 수"),
        "bed_capacity": ("🛏️", "인구 10만 명당 응급병상 수"),
        "response_time": ("⏱️", "평균 출동~도착 소요시간"),
        "transfer_success": ("✅", "1차 이송 성공률"),
    },
)

st.write("")

left, right = st.columns([2, 1], gap="medium")
with left:
    with st.container(border=True):
        region_panel(get_region_vulnerability_df())
with right:
    with st.container(border=True):
        st.markdown(
            '<div class="panel-title" style="margin-bottom:10px;">'
            '권역별 응급의료기관 접근성 · 병상 수용력 상관관계 분석</div>',
            unsafe_allow_html=True,
        )
        tab_names = ["서연", "지영", "성재"]
        tabs = st.tabs(tab_names)
        for tab, name in zip(tabs, tab_names):
            with tab:
                for i in range(1, 5):
                    st.text_area(
                        f"{name} 메모 {i}",
                        key=f"emergency_note_{name}_{i}",
                        placeholder="분석 내용 / 코드 스니펫 / 링크 등을 자유롭게 기록하세요.",
                        label_visibility="collapsed",
                        height=68,
                    )

st.write("")

chart_col, table_col, filter_col = st.columns([2.2, 1, 1], gap="medium")
with chart_col:
    with st.container(border=True):
        title_col, select_col = st.columns([3, 1])
        with title_col:
            st.markdown('<div class="panel-title">인구밀도 vs 응급의료 공급 상관계수</div>', unsafe_allow_html=True)
        with select_col:
            st.selectbox("연도", options=list(range(2015, 2025)), index=9, label_visibility="collapsed",
                         key="emergency_year_select")
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
        select_all = st.checkbox("전체 선택", value=True, key="emergency_year_all")
        selected_years = []
        for y in range(2015, 2025):
            checked = st.checkbox(f"{y}년", value=select_all, key=f"emergency_year_{y}")
            if checked:
                selected_years.append(y)
        st.markdown("---")
        with st.expander("📍 시도 선택"):
            regions = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
                       "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
            st.multiselect("시도", options=sorted(regions), default=sorted(regions),
                            label_visibility="collapsed", key="emergency_region_filter")

st.write("")

with st.container(border=True):
    st.markdown('<div class="panel-title">인구 대비 응급의료기관 수 — 연도별</div>', unsafe_allow_html=True)
    small_multiples_grid(get_small_multiples_df("노인복지시설"))
    st.caption("그래프 캡션: 그래프 간단 분석 설명")

st.write("")

with st.container(border=True):
    st.markdown('<div class="panel-title">인구 대비 응급 병상 수 — 연도별</div>', unsafe_allow_html=True)
    small_multiples_grid(get_small_multiples_df("요양병원"))
    st.caption("그래프 캡션: 그래프 간단 분석 설명")
