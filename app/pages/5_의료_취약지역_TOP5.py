import pandas as pd
import streamlit as st

from utils.style import inject_base_style
from utils.nav import render_sidebar
from utils.components import kpi_card, region_panel, top5_ranking_panel
from utils.sample_data import get_region_vulnerability_df, get_top5_vulnerable_df

st.set_page_config(page_title="의료 취약지역 TOP 5", page_icon="⚠️", layout="wide")

inject_base_style()
render_sidebar(active_key="top5")

st.markdown('<div class="page-title">종합 의료 취약지역 TOP 5</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">수요지표(고령인구·출산율·응급수요)와 공급지표(의료기관·병상·전문의 수)를 '
    '인구 가중치로 결합하여 지역별 종합 취약점수를 산출합니다.</div>',
    unsafe_allow_html=True,
)

# ── 요약 KPI ─────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("🗺️", "분석 대상", "228개 시군구")
with c2:
    kpi_card("⚠️", "고위험(70점 이상)", "34개 지역", trend="down")
with c3:
    kpi_card("📊", "평균 취약점수", "48.2점")
with c4:
    kpi_card("🔺", "전년 대비 악화 지역", "12개 지역", delta_text="4개", trend="down")

st.write("")

# ── 가중치 조정 패널 ─────────────────────────────────────────────────
with st.container(border=True):
    st.markdown('<div class="panel-title" style="margin-bottom:10px;">종합 취약점수 가중치 설정</div>',
                unsafe_allow_html=True)
    w1, w2, w3 = st.columns(3)
    with w1:
        st.slider("수요지표 가중치 (고령화·출산율)", 0, 100, 40, key="w_demand")
    with w2:
        st.slider("공급지표 가중치 (의료기관·병상)", 0, 100, 40, key="w_supply")
    with w3:
        st.slider("접근성 가중치 (이동거리·전원율)", 0, 100, 20, key="w_access")
    st.caption("※ 위 가중치는 UI 데모용이며, 실제 산식은 팀 협의 후 utils/sample_data.py 에 반영합니다.")

st.write("")

# ── 전국 현황 버블맵 + TOP5 리스트 ──────────────────────────────────────
left, right = st.columns([2, 1], gap="medium")
with left:
    with st.container(border=True):
        region_panel(get_region_vulnerability_df(), title="전국 종합 취약도 현황")
with right:
    with st.container(border=True):
        top5_ranking_panel(get_top5_vulnerable_df())

st.write("")

# ── 전체 순위 테이블 ─────────────────────────────────────────────────
with st.container(border=True):
    st.markdown('<div class="panel-title" style="margin-bottom:10px;">지역별 종합 취약점수 전체 목록</div>',
                unsafe_allow_html=True)
    df = get_region_vulnerability_df().sort_values("vulnerability_score", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df = df.rename(columns={
        "region": "지역", "vulnerability_score": "종합 취약점수", "population": "인구 수",
    })[["지역", "종합 취약점수", "인구 수"]]
    st.dataframe(df, use_container_width=True, height=420)
