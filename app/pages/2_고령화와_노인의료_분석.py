from pathlib import Path

import pandas as pd
import streamlit as st

from utils.style import inject_base_style
from utils.nav import render_sidebar

# ── 서연 추가분(app/aging/*_sy.py) ──────────────────────────────────────
from aging.tab_panels_sy import (
    render_top5_tab,
    render_growth_rate_tab,
    render_facility_corr_tab,
    render_hospital_corr_tab,
)

# 페이지 초기 세팅 함수
st.set_page_config(page_title="고령화율과 노인복지센터/요양병원 수 간의 상관관계 분석", page_icon="👵", layout="wide")

# 프로젝트 디자인 테마 CSS 주입
inject_base_style()

# 사이드바에서 어느 항목으로 표시할건지
render_sidebar(active_key="aging")

# 데이터 가져올 디렉토리 경로
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "aging" / "processed"


# ── 서연 추가분: 상단 KPI 4개 실데이터로 교체 ──────────────────────────────
# 기존 get_aging_kpis()(utils/sample_data.py)는 응급의료 파트용 임시값이 그대로
# 남아있어서, 고령화 파트 실제 분석 결과로 계산하는 함수를 이 파일 안에 둔다.
# (공유 파일은 건드리지 않고, kpi_row() 컴포넌트가 하드코딩한 "전년 대비" 문구가
#  우리 지표(2015년 대비 등)와 안 맞아서 kpi_card와 같은 CSS 클래스만 재사용해
#  자체 렌더링한다.)
@st.cache_data
def get_real_aging_kpis() -> dict:
    panel = pd.read_csv(DATA_DIR / "aging_panel_2015_2024.csv")
    corr_year = pd.read_csv(DATA_DIR / "correlation_by_year.csv")

    p2024 = panel[panel["연도"] == panel["연도"].max()]
    p2015 = panel[panel["연도"] == panel["연도"].min()]
    avg_ratio_now = p2024["고령인구비율"].mean()
    avg_ratio_then = p2015["고령인구비율"].mean()

    facility_2024 = corr_year[
        (corr_year["y"] == "고령인구10만명당_노인복지시설수") & (corr_year["연도"] == 2024)
    ].iloc[0]
    hospital_2015 = corr_year[
        (corr_year["y"] == "고령인구10만명당_요양병원수") & (corr_year["연도"] == 2015)
    ].iloc[0]
    hospital_2024 = corr_year[
        (corr_year["y"] == "고령인구10만명당_요양병원수") & (corr_year["연도"] == 2024)
    ].iloc[0]

    yearly_hospital_total = panel.groupby("연도")["요양병원수"].sum()
    hospital_now = int(yearly_hospital_total.loc[panel["연도"].max()])
    hospital_peak_year = int(yearly_hospital_total.idxmax())
    hospital_peak = int(yearly_hospital_total.max())

    return {
        "aging_ratio": {
            "icon": "👵", "label": "전국 평균 고령인구비율",
            "value": f"{avg_ratio_now:.1f}", "unit": "%",
            "delta": f"2015년 대비 ▲ {avg_ratio_now - avg_ratio_then:.1f}%p", "trend": "up",
        },
        "facility_corr": {
            "icon": "🏢", "label": "고령인구비율 vs 노인복지시설 상관계수",
            "value": f"{facility_2024['pearson_r']:.2f}", "unit": "",
            "delta": f"p={facility_2024['pearson_p']:.3f} (유의)", "trend": "up",
        },
        "hospital_corr_shift": {
            "icon": "🏥", "label": "고령인구비율 vs 요양병원 상관계수 변화",
            "value": f"{hospital_2024['pearson_r']:+.2f}", "unit": "",
            "delta": f"2015년 {hospital_2015['pearson_r']:+.2f} → 부호 반전", "trend": "up",
        },
        "hospital_count": {
            "icon": "🩺", "label": "전국 요양병원 수",
            "value": f"{hospital_now:,}", "unit": "개",
            "delta": f"{hospital_peak_year}년 정점({hospital_peak:,}개) 대비 {hospital_now - hospital_peak:,}개",
            "trend": "down",
        },
    }


def render_real_aging_kpi_row() -> None:
    kpis = get_real_aging_kpis()
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis.values()):
        color = "#22A06B" if kpi["trend"] == "up" else "#E5484D"
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-card-header">
                        <span class="kpi-label">{kpi['label']}</span>
                        <span class="kpi-icon">{kpi['icon']}</span>
                    </div>
                    <div class="kpi-value">{kpi['value']}<span class="kpi-unit">{kpi['unit']}</span></div>
                    <div class="kpi-delta" style="color:{color}">{kpi['delta']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ── 타이틀 ────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">고령화율과 노인복지센터/요양병원 수 간의 상관관계 분석</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">지역별 고령인구비율과 노인복지시설·요양병원의 공급 수준·증가 속도를 비교하여, 의료 인프라가 취약한 지역과 그 상관관계 변화 추이(2015~2024)를 분석합니다.</div><br/>', unsafe_allow_html=True)

# ── 상단 KPI 4개 (서연 추가분: 고령화 파트 실데이터로 교체) ──────────────
render_real_aging_kpi_row()

st.write("")

# ══════════════════════════════════════════════════════════════════════
# 서연 재구성: KPI 박스 아래 탭바 4개 — 우리가 진행한 4가지 분석을 탭으로 구성
# 탭마다 좌측(지도뷰)·우측(분석뷰)을 데이터·시각화 특성에 맞게 구성했다
# (구현: app/aging/tab_panels_sy.py)
#   ① 취약지역 Top5 분석      — 지도: 격차점수 / 분석: 시도별 랭킹
#   ② 지역별 증가 속도        — 지도: 증가율   / 분석: 시도별 막대그래프
#   ③ 노인복지시설 상관관계    — 지도: 연도별 수준 / 분석: 산점도
#   ④ 요양병원 상관관계        — 지도: 연도별 수준 / 분석: 산점도
# ══════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "취약지역 Top5 분석",
    "노인복지센터·요양병원 증가 속도",
    "고령인구비율 vs 노인복지시설 상관관계",
    "고령인구비율 vs 요양병원 상관관계",
])

with tab1:
    render_top5_tab()

with tab2:
    render_growth_rate_tab()

with tab3:
    render_facility_corr_tab()

with tab4:
    render_hospital_corr_tab()
