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

# ── 타이틀 ────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">지역 의료 인프라 균형 대시보드</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">지역별 인구 변화와 의료시설 공급 수준을 비교하여 '
    '의료 인프라 개선이 필요한 취약지역을 직관적으로 확인하고 분석합니다.</div>',
    unsafe_allow_html=True,
)

# ── 상단 요약 KPI 4개 ───────────────────────────────────────────────────
kpis = get_overview_kpis()
c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("🗄️", "분석 대상", kpis["analysis_target"])
with c2:
    kpi_card("📅", "분석 기간", kpis["analysis_period"])
with c3:
    kpi_card("📁", "분석 분야", kpis["analysis_fields"])
with c4:
    kpi_card("⚠️", "의료 취약지역", kpis["vulnerable_top"])

st.write("")

# ── 메인: 좌측 버블맵 / 우측 TOP5 ───────────────────────────────────────
left, right = st.columns([2, 1], gap="medium")

with left:
    with st.container(border=True):
        region_panel(get_region_vulnerability_df())

with right:
    with st.container(border=True):
        top5_ranking_panel(get_top5_vulnerable_df())

st.write("")

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

q3, q4 = st.columns(2, gap="medium")
with q3:
    quicklink_card("🍼", "출산율과 소아과", "시도별 합계출산율 추이와 전문 소아과 인프라의 위기 수준 데이터 분석",
                    border_color="#2F6FED")
with q4:
    quicklink_card("❗", "종합 의료 취약지역 TOP 5", "수요지표와 공급지표를 인구 가중치로 결합하여 취약지역 종합 순위 도출",
                    border_color="#E5484D")

st.write("")

# ── 프로젝트 분석 흐름 ───────────────────────────────────────────────────
# TODO: 해당 항목은 논의 후 구체화가 필요해 보임.
with st.container(border=True):
    st.markdown("##### 프로젝트 분석 흐름")
    process_flow(["데이터 수집", "데이터 정제 및 표준화", "지역별 지표 분석", "의료 취약점수 산출", "시각화 및 결과 해석"])
